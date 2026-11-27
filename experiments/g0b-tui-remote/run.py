#!/usr/bin/env python3
"""G0b 개인 Codex CLI / stdlib TUI. 조회·생성·승인·반영은 별도 action이다."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import termios
import time
import tty
import unicodedata
import uuid

from core import ATTEMPT_START_STATES, Core, CoreError
import oracle
from runtime import (RuntimeFailure, child_environment, execute, preflight,
                     private_read, private_write, PROJECT)


class ProjectionCore(Core):
    """Core의 실제 조회 API를 읽기 전용 연결로 사용한다. 초기화/복구는 하지 않는다."""

    def __init__(self, state_dir):
        self.state_dir = Path(state_dir).absolute()
        self.db_path = self.state_dir / "core.sqlite3"
        info = self.state_dir.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o700):
            raise CoreError("PERMISSION_DENIED", "상태 디렉터리 경계를 확인하지 못했습니다.")
        self._state_inode = [info.st_dev, info.st_ino]
        self._secure_files()

    @contextmanager
    def _connection(self, *, write=False):
        if write:
            raise CoreError("READ_ONLY", "조회 연결로 상태를 변경할 수 없습니다.")
        self._secure_files()
        conn = None
        try:
            conn = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True, timeout=0)
            conn.execute("PRAGMA query_only=ON")
            if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise CoreError("SCHEMA_VERSION", "초기화된 Core DB가 아닙니다.")
            yield conn
        except sqlite3.Error as exc:
            raise CoreError("STORAGE_ERROR", "Core projection을 읽지 못했습니다.") from exc
        finally:
            if conn is not None:
                conn.close()


def projection(state_dir):
    if not (Path(state_dir) / "core.sqlite3").exists():
        return None
    return ProjectionCore(state_dir)


def metadata_path(state_dir, work_id):
    # Core가 생성한 ID만 경로 구성에 사용한다.
    if len(work_id) != 32 or any(c not in "0123456789abcdef" for c in work_id):
        raise CoreError("WORK_NOT_FOUND", "올바른 Work ID가 필요합니다.")
    return Path(state_dir) / ("runtime-" + work_id + ".json")


def read_metadata(state_dir, work_id):
    try:
        return json.loads(private_read(metadata_path(state_dir, work_id), 1024 * 1024))
    except FileNotFoundError:
        return {}
    except (ValueError, RuntimeFailure):
        raise RuntimeFailure("RUNTIME_RECORD_INVALID", "runtime 관측 기록을 읽지 못했습니다.")


def view(state_dir, work):
    result = dict(work)
    observation = read_metadata(state_dir, work["work_id"])
    observation["phase"] = work["state"]
    failure = work.get("runtime_failure")
    if failure:
        for key in ("process_exited", "exit_code", "turn_completed", "usage", "timeout_seconds",
                    "worker_lease_released", "backend_model_observed"):
            observation.pop(key, None)
        observation.update(failure["runtime_metadata"])
        observation["error"] = {"code": failure["error_code"], "message": failure["error_message"]}
    result["runtime_observation"] = observation
    return result


def select_runtime(args):
    if not args.expected_account:
        raise RuntimeFailure("IDENTITY_UNKNOWN", "명시적 --expected-account가 필요합니다.")
    return preflight(codex_binary=args.codex_binary, model=args.model,
                     expected_account=args.expected_account)


def same_identity(work, selection):
    if work["identity"] != selection["identity"]:
        raise CoreError("IDENTITY_MISMATCH", "작업에 고정한 runtime·모델·개인 계정과 다릅니다.")


def check_pin(state_dir, work):
    metadata = read_metadata(state_dir, work["work_id"])
    if (metadata.get("oracle_sha256") != oracle.oracle_sha256()
            or metadata.get("baseline_sha256") != hashlib.sha256(oracle.baseline_bytes()).hexdigest()
            or metadata.get("baseline_sha256") != work["baseline_sha256"]):
        raise RuntimeFailure("ORACLE_CHANGED", "생성 시 고정한 oracle/baseline과 현재 파일이 다릅니다.")
    return metadata


def new_work(args):
    selection = select_runtime(args)
    root = Path(args.workspace).expanduser().absolute()
    # oracle API는 인수 디렉터리 아래에 새 합성 workspace를 만든다.
    # 이미 존재하는 비어 있지 않은 디렉터리는 명시적으로 거부한다.
    if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise CoreError("INVALID_PATH", "합성 workspace에 symlink 경로를 사용할 수 없습니다.")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise CoreError("WORKSPACE_NOT_EMPTY", "새 경로 또는 빈 디렉터리가 필요합니다.")
    state = Path(args.state_dir).absolute()
    if root == state or state in root.parents:
        raise CoreError("INVALID_PATH", "flat Core 상태 경로 아래에는 workspace를 만들 수 없습니다.")
    core = Core(args.state_dir)
    fixture = oracle.write_workspace(root)
    work = core.create_work(Path(fixture["workspace"]), fixture["target_rel"],
                            selection["identity"], budget_units=1)
    private_write(metadata_path(args.state_dir, work["work_id"]), {
        **selection["metadata"], "oracle_sha256": oracle.oracle_sha256(),
        "baseline_sha256": fixture["baseline_sha256"], "phase": "NEW",
    })
    return {"work_id": work["work_id"], "state": work["state"], "revision": work["revision"],
            "workspace": work["workspace"], "model_called": False}


def launch(args, *, snapshot=None):
    core = Core(args.state_dir)
    if not 180 <= args.timeout <= 3600:
        raise RuntimeFailure("INVALID_TIMEOUT", "timeout은 180~3600초여야 합니다.")
    work = core.get_work(args.work_id)
    if snapshot is not None and snapshot["revision"] != work["revision"]:
        raise CoreError("STALE_REVISION", "실행 확인 뒤 revision이 바뀌었습니다. 최신 상태를 조회하십시오.")
    # worker만 start_attempt를 호출한다. 빠른 거부는 실제 Core 계약과 같다.
    if work["state"] == "RUNNING":
        raise CoreError("ATTEMPT_RUNNING", "이미 실행 중입니다.")
    if work["state"] == "RUNTIME_UNKNOWN":
        raise CoreError("RUNTIME_UNKNOWN", "기존 실행의 종료·외부효과가 미확정입니다. 새 호출을 시작할 수 없습니다.")
    if work["state"] not in ATTEMPT_START_STATES:
        raise CoreError("INVALID_STATE", "이 상태에서는 새 attempt를 시작할 수 없습니다.")
    if work["used_units"] >= work["budget_units"]:
        raise CoreError("BUDGET_EXHAUSTED", "모델 호출 예약 상한에 도달했습니다.")
    selection = select_runtime(args)
    same_identity(work, selection)
    check_pin(args.state_dir, work)
    token = uuid.uuid4().hex
    handshake = Path(args.state_dir) / ("launch-" + token + ".json")
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
               "--state-dir", str(Path(args.state_dir).absolute()),
               "--codex-binary", selection["binary"], "--model", args.model,
               "--expected-account", args.expected_account,
               "_worker", work["work_id"], "--launch-token", token,
               "--expected-revision", str(work["revision"]), "--timeout", str(args.timeout)]
    # -I를 사용할 때 script 디렉터리를 명시적으로 로드하는 bootstrap을 사용한다.
    command[3:4] = ["-c", _bootstrap(), str(Path(__file__).resolve())]
    descriptors = []
    try:
        for suffix in ("stdout", "stderr"):
            path = Path(args.state_dir) / ("worker-" + token + "." + suffix)
            descriptors.append(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600))
        worker = subprocess.Popen(command, cwd=PROJECT, env=selection["env"],
                                  stdin=subprocess.DEVNULL, stdout=descriptors[0], stderr=descriptors[1],
                                  start_new_session=True, close_fds=True)
    finally:
        for fd in descriptors:
            os.close(fd)
    # 시작 응답만 기다린다. launcher가 사라져도 worker는 같은 Work를 계속 수행한다.
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if handshake.exists():
            response = json.loads(private_read(handshake, 65536))
            if response.get("error"):
                raise RuntimeFailure(response["error"], response["message"])
            return response
        if worker.poll() is not None:
            raise RuntimeFailure("WORKER_START_FAILED", "worker가 시작 응답 전에 종료했습니다.")
        time.sleep(0.05)
    return {"work_id": work["work_id"], "worker_pid": worker.pid,
            "launch_status": "START_UNCONFIRMED", "model_completion_observed": False,
            "message": "시작 응답 미관측. 재실행하지 말고 status/events를 조회하십시오."}


def _bootstrap():
    # 고정 stdlib bootstrap. 모델 코드·사용자 문자열을 Python 코드에 삽입하지 않는다.
    return ("import runpy,sys; from pathlib import Path; "
            "p=sys.argv.pop(1); sys.path.insert(0,str(Path(p).parent)); "
            "runpy.run_path(p,run_name='__main__')")


@contextmanager
def worker_lock(state_dir, work_id):
    path = metadata_path(state_dir, work_id).with_suffix(".lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise RuntimeFailure("UNSAFE_FILE", "worker lease 파일 경계를 확인하지 못했습니다.")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeFailure("ATTEMPT_RUNNING", "동일 Work의 worker가 lease를 보유합니다.")
        yield
    finally:
        os.close(fd)


def _finish_cancel(core, attempt):
    current = core.get_work(attempt["work_id"])
    if ((current["state"] == "CANCEL_REQUESTED"
         or current["state"] == "RUNTIME_UNKNOWN" and current.get("cancel_requested", False))
            and current["attempt_id"] == attempt["attempt_id"]
            and current["lease_generation"] == attempt["lease_generation"]):
        return core.finish_cancel(current["work_id"], expected_revision=current["revision"],
                                  attempt_id=attempt["attempt_id"],
                                  lease_generation=attempt["lease_generation"], process_exited=True)
    return current


def _record_runtime_failure(core, attempt, error):
    current = core.get_work(attempt["work_id"])
    if (current["attempt_id"] != attempt["attempt_id"]
            or current["lease_generation"] != attempt["lease_generation"]):
        return current
    if current["state"] not in {"RUNNING", "CANCEL_REQUESTED", "RUNTIME_UNKNOWN"}:
        return current
    return core.runtime_failure(
        current["work_id"], expected_revision=current["revision"],
        attempt_id=attempt["attempt_id"], lease_generation=attempt["lease_generation"],
        error_code=error.code, error_message=error.message,
        runtime_metadata=error.metadata, process_exited=error.metadata.get("process_exited") is True)


def worker(args):
    core = Core(args.state_dir)
    if not 180 <= args.timeout <= 3600:
        raise RuntimeFailure("INVALID_TIMEOUT", "timeout은 180~3600초여야 합니다.")
    if len(args.launch_token) != 32 or any(ch not in "0123456789abcdef" for ch in args.launch_token):
        raise RuntimeFailure("INVALID_REQUEST", "내부 launch token 형식이 올바르지 않습니다.")
    handshake = Path(args.state_dir) / ("launch-" + args.launch_token + ".json")
    attempt = None
    metadata = {}
    try:
        with worker_lock(args.state_dir, args.work_id):
            selection = select_runtime(args)
            initial = core.get_work(args.work_id)
            same_identity(initial, selection)
            metadata = check_pin(args.state_dir, initial)
            attempt = core.start_attempt(args.work_id, expected_revision=args.expected_revision,
                                         identity=selection["identity"], executor_pid=os.getpid())
            metadata.update(phase="RUNNING", attempt_id=attempt["attempt_id"],
                            lease_generation=attempt["lease_generation"], worker_pid=os.getpid(),
                            attempt_revision=attempt["revision"], error=None, child_pid=None,
                            process_exited=True)
            private_write(metadata_path(args.state_dir, args.work_id), metadata)
            private_write(handshake, {"work_id": args.work_id, "worker_pid": os.getpid(),
                                      "state": "RUNNING", "attempt_id": attempt["attempt_id"],
                                      "revision": attempt["revision"]})

            def cancelled():
                current = core.get_work(args.work_id)
                return (current["state"] != "RUNNING"
                        or current["attempt_id"] != attempt["attempt_id"]
                        or current["lease_generation"] != attempt["lease_generation"])

            def spawned(pid):
                metadata.update(child_pid=pid, process_exited=False)
                private_write(metadata_path(args.state_dir, args.work_id), metadata)

            candidate, observed = execute(
                selection, baseline=oracle.baseline_bytes(),
                final_path=Path(args.state_dir) / ("final-" + attempt["attempt_id"] + ".json"),
                cancelled=cancelled, timeout=args.timeout, on_spawn=spawned)
            metadata.update(observed, phase="VERIFYING")
            private_write(metadata_path(args.state_dir, args.work_id), metadata)
            if cancelled():
                result = _finish_cancel(core, attempt)
                metadata.update(phase=result["state"])
                private_write(metadata_path(args.state_dir, args.work_id), metadata)
                return {"work_id": args.work_id, "result": "RESULT_FENCED"}
            check_pin(args.state_dir, attempt)
            verification = oracle.verify(candidate)
            check_pin(args.state_dir, attempt)
            # 판정기의 출력 원문은 보관하지 않는다. 사례별 행동 사실만 원장에 전달한다.
            verification["cases"] = [{key: case.get(key) for key in
                                      ("name", "passed", "expected_exit", "actual_exit", "error")}
                                     for case in verification["cases"]]
            if cancelled():
                result = _finish_cancel(core, attempt)
                metadata.update(phase=result["state"])
                private_write(metadata_path(args.state_dir, args.work_id), metadata)
                return {"work_id": args.work_id, "result": "RESULT_FENCED"}
            result = core.record_candidate(args.work_id, expected_revision=attempt["revision"],
                                           attempt_id=attempt["attempt_id"],
                                           lease_generation=attempt["lease_generation"],
                                           candidate=candidate, verification=verification)
            metadata.update(phase=result["state"], candidate_sha256=result["candidate_sha256"])
            private_write(metadata_path(args.state_dir, args.work_id), metadata)
            return {"work_id": args.work_id, "state": result["state"]}
    except Exception as error:
        # 원문 exception/traceback은 자격정보·child 출력을 포함할 수 있어 출력하지 않는다.
        if not isinstance(error, (RuntimeFailure, CoreError)):
            error = RuntimeFailure("WORKER_FAILED", "worker 내부 작업을 완료하지 못했습니다.",
                                   {"process_exited": metadata.get("process_exited", False)})
        if attempt is not None:
            observed = error.metadata if isinstance(error, RuntimeFailure) else {}
            metadata.update(observed)
            # 실행 뒤 pin/검증 단계의 오류에도 이미 관측한 실제 wait 결과를 보존한다.
            failure = RuntimeFailure(error.code, error.message, dict(metadata))
            result = _record_runtime_failure(core, attempt, failure)
            if result["attempt_id"] == attempt["attempt_id"] and result.get("runtime_failure"):
                metadata.update(phase=result["state"], error={"code": failure.code, "message": failure.message})
                private_write(metadata_path(args.state_dir, args.work_id), metadata)
        private_write(handshake, {"work_id": args.work_id, "error": error.code, "message": error.message})
        raise error


def approve(args, *, snapshot=None, digest=None, revision=None):
    core = Core(args.state_dir)
    current = core.get_work(args.work_id)
    if current["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
        raise CoreError(current["state"], "runtime 실패 작업은 승인할 수 없습니다.")
    work = snapshot or current
    selection = select_runtime(args)
    same_identity(work, selection)
    return core.approve(args.work_id,
                        expected_revision=revision if revision is not None else args.expected_revision,
                        artifact_sha256=digest or args.artifact_sha256, identity=selection["identity"])


def apply(args, *, snapshot=None, approval_id=None, key=None):
    core = Core(args.state_dir)
    current = core.get_work(args.work_id)
    if current["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
        raise CoreError(current["state"], "runtime 실패 작업은 반영할 수 없습니다.")
    work = snapshot or current
    selection = select_runtime(args)
    same_identity(work, selection)
    failpoint = getattr(args, "fail_after_replace", False)
    try:
        return core.apply(args.work_id, expected_revision=work["revision"],
                          approval_id=approval_id or args.approval_id, identity=selection["identity"],
                          idempotency_key=key or args.idempotency_key, fail_after_replace=failpoint)
    except RuntimeError:
        if failpoint:
            raise RuntimeFailure("APPLY_RESPONSE_LOST", "명시적 replace 직후 failpoint입니다. status 조회 후 reconcile이 필요합니다.")
        raise


def reconcile(args):
    core = Core(args.state_dir)
    work = core.get_work(args.work_id)
    if work["state"] not in {"RUNNING", "CANCEL_REQUESTED"}:
        return core.reconcile(args.work_id)
    with worker_lock(args.state_dir, args.work_id):
        current = core.get_work(args.work_id)
        if current["state"] not in {"RUNNING", "CANCEL_REQUESTED"}:
            return current
        # flock 획득은 worker lease 소멸 관측이다. PID 존재 여부는 종료 증거로 쓰지 않는다.
        # 다른 부모의 child를 wait할 수 없으므로 취소완료나 실제 child 종료를 주장하지 않는다.
        failure = RuntimeFailure("WORKER_LOST", "worker lease가 소멸했습니다. child 종료는 미관측입니다.",
                                 {"process_exited": False, "worker_lease_released": True})
        result = _record_runtime_failure(core, current, failure)
        observation = read_metadata(args.state_dir, args.work_id)
        observation.update(phase=result["state"], error={"code": failure.code, "message": failure.message},
                           process_exited=False, worker_lease_released=True)
        private_write(metadata_path(args.state_dir, args.work_id), observation)
        return result


def cancel(args, *, snapshot=None):
    core = Core(args.state_dir)
    work = snapshot or core.get_work(args.work_id)
    result = core.request_cancel(args.work_id, expected_revision=work["revision"])
    # attempt가 없으면 이 adapter가 시작한 child 자체가 없다.
    if result["state"] == "CANCEL_REQUESTED" and result["attempt_id"] is None:
        return core.finish_cancel(args.work_id, expected_revision=result["revision"], attempt_id=None,
                                  lease_generation=result["lease_generation"], process_exited=True)
    if result["state"] == "CANCEL_REQUESTED":
        if (result.get("runtime_failure") or {}).get("process_exited") is True:
            return _finish_cancel(core, result)
        try:
            with worker_lock(args.state_dir, args.work_id):
                observed = read_metadata(args.state_dir, args.work_id)
                if (observed.get("attempt_id") == result["attempt_id"]
                        and observed.get("lease_generation") == result["lease_generation"]
                        and observed.get("process_exited") is True):
                    return _finish_cancel(core, result)
        except RuntimeFailure as error:
            if error.code != "ATTEMPT_RUNNING":
                raise
    return result


def _width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _lines(text, width):
    # 원장 문자열의 ANSI/control 주입을 막고 terminal의 마지막 열은 사용하지 않는다.
    safe = "".join(ch if ch.isprintable() else " " for ch in str(text))
    line = ""
    for ch in safe:
        if _width(ch) > width:
            ch = "?"
        if _width(line + ch) > width:
            yield line
            line = ""
        line += ch
    yield line


def tui(args):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeFailure("TTY_REQUIRED", "tui는 실제 입력·출력 terminal이 필요합니다.")
    reader = projection(args.state_dir)
    if reader is None:
        raise CoreError("EMPTY_STATE", "Core DB가 없습니다. new로 Work를 먼저 만드십시오.")
    work = reader.get_work(args.work_id)
    bound = (work["revision"], work["candidate_sha256"]) if work["candidate_sha256"] else None
    approved = work if work["approval_id"] else None
    message = "q/Ctrl-C는 접속만 해제합니다. v로 화면 후보를 승인 대상으로 선택합니다."
    pending = None
    detach = False
    scroll = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    old_signals = {}

    def stop(signum, frame):
        nonlocal detach
        detach = True

    try:
        for signum in (signal.SIGINT, signal.SIGHUP, signal.SIGTERM):
            old_signals[signum] = signal.signal(signum, stop)
        tty.setcbreak(fd)
        while not detach:
            work = reader.get_work(args.work_id)
            observation = view(args.state_dir, work)["runtime_observation"]
            verification = work.get("verification") or {}
            cases = verification.get("cases", [])
            passed = sum(case.get("passed") is True for case in cases)
            receipt = work.get("receipt") or {}
            rows = ["G0b · 개인 Codex CLI 실험", "Work: " + work["work_id"],
                    f"상태: {work['state']}   revision: {work['revision']}",
                    "요청 model: " + work["identity"]["model"] + " (backend model 미관측)",
                    f"호출 예약: {work['used_units']}/{work['budget_units']} (금액 상한 아님)",
                    "현재 후보: " + str(work["candidate_sha256"] or "없음"),
                    "독립 검증: " + str(verification.get("passed", "미실행")) + f" · 사례 {passed}/{len(cases)}",
                    "oracle: " + str(verification.get("oracle_sha256") or observation.get("oracle_sha256")),
                    "승인 대상: " + (f"rev {bound[0]} / {bound[1]}" if bound else "미선택 · v로 선택"),
                    "승인 ID: " + str(work["approval_id"] or "없음"),
                    "runtime: " + str(observation.get("phase")) + " · 오류: " + str(observation.get("error") or "없음"),
                    "실제 process 종료: " + ("관측됨" if observation.get("process_exited") is True else "미관측"),
                    "취소 요청: " + ("있음" if work.get("cancel_requested", work["state"] == "CANCEL_REQUESTED") else "없음"),
                    "readback: " + str(receipt.get("readback_sha256") or "없음"),
                    "반영 key: " + str(receipt.get("idempotency_key") or "없음"),
                    "반영 근거: " + str(receipt.get("effect") or "없음"),
                    "r 실행 | v 후보 선택 | a 승인 | p 반영 | c 취소 | q 해제 | j/k 스크롤", message]
            if pending:
                rows.append("확인: " + pending[0] + " · y 실행 / 다른 키 해제")
            size = shutil.get_terminal_size((80, 24))
            width = max(1, size.columns - 1)
            rendered = [line for row in rows for line in _lines(row, width)]
            if len(rendered) > size.lines:
                # 좁은 창에서도 생략된 digest·근거를 명시적 스크롤로 읽을 수 있다.
                limit = max(1, size.lines - 1)
                scroll = min(scroll, max(0, len(rendered) - limit))
                rendered = rendered[scroll:scroll + limit]
            sys.stdout.write("\x1b[H\x1b[2J" + "\r\n".join(rendered))
            sys.stdout.flush()
            ready, _, _ = select.select([fd], [], [], 0.5)
            if not ready:
                continue
            char = os.read(fd, 1).decode("ascii", errors="ignore")
            if char in {"q", "\x03", ""}:
                break
            if char in {"j", "k"}:
                scroll = max(0, scroll + (1 if char == "j" else -1))
                continue
            try:
                if pending:
                    _, operation = pending
                    pending = None
                    if char == "y":
                        result = operation()
                        message = "요청 결과: " + str(result.get("state", result.get("launch_status", "시작 요청됨")))
                    else:
                        message = "실행하지 않았습니다."
                elif char == "v":
                    if work["state"] == "REVIEW_READY" and work["candidate_sha256"]:
                        bound = (work["revision"], work["candidate_sha256"])
                        approved = work if work["approval_id"] else None
                        message = "화면의 revision·digest를 승인 대상으로 고정했습니다."
                    else:
                        message = "검증을 통과한 후보가 없습니다."
                elif char == "r":
                    if work["state"] == "RUNTIME_UNKNOWN":
                        raise RuntimeFailure("RUNTIME_UNKNOWN", "종료·외부효과가 미확정이므로 실행·승인·반영이 차단됩니다.")
                    if work["state"] == "RUNNING":
                        raise CoreError("ATTEMPT_RUNNING", "이미 실행 중입니다.")
                    if work["state"] not in ATTEMPT_START_STATES:
                        raise CoreError("INVALID_STATE", "이 상태에서는 새 attempt를 시작할 수 없습니다.")
                    if work["used_units"] >= work["budget_units"]:
                        raise CoreError("BUDGET_EXHAUSTED", "모델 호출 예약 상한에 도달했습니다.")
                    snapshot = work
                    pending = ("모델 호출 1회 예약", lambda: launch(args, snapshot=snapshot))
                elif char == "a":
                    if work["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
                        raise RuntimeFailure(work["state"], "runtime 실패 작업은 승인할 수 없습니다.")
                    if bound is None:
                        raise RuntimeFailure("NO_APPROVAL_TARGET", "v로 승인 대상을 먼저 선택하십시오.")
                    selected = bound

                    def approve_selected(selected=selected, snapshot=work):
                        nonlocal approved
                        result = approve(args, snapshot=snapshot, revision=selected[0], digest=selected[1])
                        approved = result
                        return result

                    pending = (f"후보 승인 rev {selected[0]} / {selected[1]}", approve_selected)
                elif char == "p":
                    if work["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
                        raise RuntimeFailure(work["state"], "runtime 실패 작업은 반영할 수 없습니다.")
                    # 자동 refresh가 승인·반영 대상을 바꾸지 않는다.
                    selected = approved
                    if selected is None:
                        raise RuntimeFailure("NO_APPROVAL_TARGET", "명시적 유효 승인이 필요합니다.")
                    operation_key = uuid.uuid4().hex
                    pending = ("파일 반영 / " + str(selected["candidate_sha256"]),
                               lambda selected=selected, key=operation_key: apply(
                                   args, snapshot=selected, approval_id=selected["approval_id"], key=key))
                elif char == "c":
                    snapshot = work
                    pending = ("현재 Work 취소 요청", lambda: cancel(args, snapshot=snapshot))
                if pending:
                    # 확인 대상 digest가 있는 하단으로 이동한다. 자동 승인은 하지 않는다.
                    scroll = 10**6
            except (CoreError, RuntimeFailure) as error:
                message = error.code + ": " + error.message
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        for signum, handler in old_signals.items():
            signal.signal(signum, handler)
        sys.stdout.write("\r\n접속 해제 · Work와 worker는 독립적으로 유지됩니다.\r\n")
        sys.stdout.flush()
    return None


def parser():
    result = argparse.ArgumentParser(description="G0b 개인 Codex CLI 실험. OMP RPC 연결은 포함하지 않습니다.")
    result.add_argument("--state-dir", type=Path, default=Path.home() / ".local/state/codeforge-g0b",
                        help="소유자 전용 durable Core 상태 경로")
    result.add_argument("--codex-binary", help="명시적 개인 Codex 바이너리 (생략 시 codex PATH)")
    result.add_argument("--model", help="명시적 요청 model (이 실증: gpt-6.1-sol); 자동 대체 없음")
    result.add_argument("--expected-account", help="로컬 OAuth email 대조값; DB에는 fingerprint만 기록")
    commands = result.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="합성 workspace·Work 생성; 모델 호출 없음")
    new.add_argument("--workspace", required=True, help="새 경로 또는 빈 상위 경로; 하위 합성 디렉터리 생성")
    status = commands.add_parser("status", help="순수 상태 조회; 실행·복구 없음")
    status.add_argument("work_id", nargs="?")
    for name, help_text in (("events", "순수 이벤트 조회"), ("run", "detached worker에서 모델 한 번 실행"),
                            ("_worker", "내부 전용 detached worker"), ("approve", "정확한 후보·revision 승인"),
                            ("apply", "별도 명시 반영·실제 readback"), ("reconcile", "명시적 반영/worker 장애 조정"),
                            ("cancel", "명시 취소 요청; 종료 관측 뒤 완료"), ("tui", "terminal 접속; q는 취소 아닌 detach")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("work_id")
        if name in {"run", "_worker", "tui"}:
            command.add_argument("--timeout", type=int, default=240, help="CLI timeout 초 (180~3600, 기본 240)")
        if name == "_worker":
            command.add_argument("--launch-token", required=True)
            command.add_argument("--expected-revision", type=int, required=True)
        if name == "approve":
            command.add_argument("--artifact-sha256", required=True, help="사용자가 확인한 정확한 후보 digest")
            command.add_argument("--expected-revision", type=int, required=True, help="사용자가 관측한 revision; 자동 갱신 없음")
        if name == "apply":
            command.add_argument("--approval-id", required=True)
            command.add_argument("--idempotency-key", required=True)
            command.add_argument("--fail-after-replace", action="store_true",
                                 help="smoke용 명시 장애: replace 직후 실패하여 APPLY_UNKNOWN/reconcile 경로 확인")
    return result


def main():
    args = parser().parse_args()
    args.state_dir = args.state_dir.expanduser().absolute()
    os.umask(0o077)
    try:
        if args.command in {"status", "events"}:
            core = projection(args.state_dir)
            if core is None:
                output = {"state": "EMPTY", "database_exists": False, "works": [], "model_called": False}
            elif args.command == "events":
                output = core.events(args.work_id)
            elif args.work_id:
                output = view(args.state_dir, core.get_work(args.work_id))
            else:
                output = [view(args.state_dir, work) for work in core.list_work()]
        else:
            output = {"new": new_work, "run": launch, "_worker": worker, "approve": approve,
                      "apply": apply, "cancel": cancel, "reconcile": reconcile, "tui": tui}[args.command](args)
        if output is not None:
            print(json.dumps(output, ensure_ascii=False, allow_nan=False))
        return 0
    except (CoreError, RuntimeFailure) as error:
        print(json.dumps({"error": error.code, "message": error.message}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception:
        print(json.dumps({"error": "LOCAL_IO_FAILED", "message": "로컬 작업을 완료하지 못했습니다."}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
