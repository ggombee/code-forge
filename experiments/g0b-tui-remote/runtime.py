"""G0b의 명시적 개인 Codex CLI 실행 경계. 자동 재시도·계정 전환 없음.

read-only CLI와 도구 사용 감시는 OS 전체 읽기/네트워크 격리가 아니다.
원시 JSONL·stderr·자격정보는 저장하거나 호출자에게 반환하지 않는다.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time


MAX_CANDIDATE = 1024 * 1024
MAX_FINAL = 8 * MAX_CANDIDATE
MAX_LINE = 8 * MAX_CANDIDATE
MAX_STREAM = 32 * MAX_CANDIDATE
SCHEMA = Path(__file__).resolve().with_name("runtime-schema.json")
PROJECT = Path(__file__).resolve().parents[2]
CONTRACT = """완전한 Python CLI source를 candidate 문자열 하나에 담아 반환한다.
첨부 source만 변환하고 도구, shell, 파일 읽기, 검색, 네트워크를 사용하지 않는다.
--config와 --tool은 필수 인자다. 설정 파일 부재, 읽기/인코딩/JSON 오류,
설정이 object가 아니거나 enabled가 bool true가 아닌 경우, 지정 도구를 PATH에서
찾을 수 없는 경우에는 traceback 없이 FAIL을 출력하고 양수 exit code로 종료한다.
enabled가 bool true이고 지정 도구가 PATH에 있으면 PASS와 exit 0을 유지한다.
오류 경로에서 PASS를 출력하지 않는다. 외부 의존성 없는 Python stdlib만 사용한다.
생성은 검증·승인·반영이 아니며 판정기 내용을 추측하거나 접근하지 않는다.
"""


class RuntimeFailure(Exception):
    """비밀이나 원시 child 오류를 포함하지 않는 실패 코드."""

    def __init__(self, code, message, metadata=None):
        self.code = code
        self.message = message
        self.metadata = metadata or {}
        super().__init__(message)


def _fail(code, message, metadata=None):
    raise RuntimeFailure(code, message, metadata)


def private_read(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or info.st_size > limit):
            _fail("UNSAFE_FILE", "일반 소유 파일 또는 크기 경계를 확인하지 못했습니다.")
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(data)))
            if not chunk:
                return bytes(data)
            data.extend(chunk)
        _fail("OUTPUT_LIMIT", "파일 크기 경계를 넘었습니다.")
    finally:
        os.close(fd)


def private_write(path, value):
    """전용 flat 상태 디렉터리에서 원자적으로 최소 metadata만 갱신한다."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".runtime-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False).encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def child_environment(binary):
    """회사 연동·API key·provider override·proxy·Python 주입 변수를 상속하지 않는다."""
    home = Path.home()
    return {
        "HOME": str(home), "CODEX_HOME": str(home / ".codex"),
        "CODEX_AUTO_ACCOUNT_SELECTED": "personal",
        "FORGE_GLOW_CODEX_ACCOUNT": "personal",
        "PATH": os.pathsep.join(dict.fromkeys([str(Path(binary).parent),
                                              "/usr/bin", "/bin", "/usr/sbin", "/sbin"])),
        "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "TZ": "UTC",
    }


def _guard(action, env, path=None):
    guard = Path.home() / ".config/personal-project-guard/guard.py"
    if not guard.is_file():
        _fail("IDENTITY_UNKNOWN", "공식 개인 프로젝트 guard가 없습니다.")
    command = [sys.executable, "-I", "-B", str(guard), action]
    if path is not None:
        command.append(str(path))
    # doctor/inspect는 로컬 검사다. 출력은 보관·전달하지 않는다.
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as error:
            result = subprocess.run(command, cwd=PROJECT, env=env, stdin=subprocess.DEVNULL,
                                    stdout=output, stderr=error, timeout=30)
            if result.returncode != 0:
                _fail("IDENTITY_UNKNOWN" if action == "doctor" else "CONTENT_BLOCKED",
                      "공식 guard 검사가 통과하지 않았습니다.")
    except (OSError, subprocess.TimeoutExpired):
        _fail("IDENTITY_UNKNOWN", "공식 guard의 완료를 관측하지 못했습니다.")


def _jwt_claims(token):
    if not isinstance(token, str) or len(token) > 65536:
        raise ValueError()
    part = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def preflight(*, codex_binary=None, model, expected_account):
    """guard와 같은 개인 auth 범위의 로컬 claim을 대조한다. 로그인은 하지 않는다."""
    if not isinstance(model, str) or not model.strip() or model.startswith("-"):
        _fail("MODEL_REQUIRED", "명시적 --model이 필요합니다.")
    personal = (Path.home() / ".codex").resolve()
    if (os.environ.get("CODEX_AUTO_ACCOUNT_SELECTED") != "personal"
            or os.environ.get("FORGE_GLOW_CODEX_ACCOUNT") != "personal"
            or os.environ.get("CLAUDE_AUTO_ACCOUNT_SELECTED")
            or not os.environ.get("CODEX_HOME")
            or Path(os.environ.get("CODEX_HOME", "")).expanduser().resolve() != personal):
        _fail("IDENTITY_UNKNOWN", "실제 개인 Codex 환경을 확인하지 못했습니다.")
    binary = codex_binary or shutil.which("codex")
    if not binary or not Path(binary).is_file() or not os.access(binary, os.X_OK):
        _fail("RUNTIME_UNAVAILABLE", "지정한 Codex 실행 파일을 찾을 수 없습니다.")
    binary = str(Path(binary).absolute())
    env = child_environment(binary)
    _guard("doctor", env)
    try:
        # policy와 credential은 로컬에서만 읽고 값은 반환/기록하지 않는다.
        policy = json.loads(private_read(Path.home() / ".config/personal-project-guard/local-policy.json", MAX_CANDIDATE))
        if Path(policy["personal_profile"]).resolve() != personal:
            raise ValueError()
        auth = json.loads(private_read(personal / "auth.json", MAX_CANDIDATE))
        if auth.get("OPENAI_API_KEY") or auth.get("auth_mode") not in (None, "chatgpt"):
            raise ValueError()
        tokens = auth["tokens"]
        account = tokens["account_id"]
        fingerprint = hashlib.sha256(account.encode()).hexdigest()
        if not account or fingerprint != policy["personal_account_sha256"]:
            raise ValueError()
        claims = _jwt_claims(tokens["id_token"])
        if not expected_account or claims.get("email", "").casefold() != expected_account.casefold():
            raise ValueError()
        claimed_account = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
        if claimed_account is not None and claimed_account != account:
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RuntimeFailure, RuntimeError):
        _fail("IDENTITY_UNKNOWN", "guard와 요청한 개인 계정의 동일 범위를 관측하지 못했습니다.")
    return {
        "identity": {"provider": "codex-cli", "model": model, "account_fingerprint": fingerprint},
        "binary": binary, "env": env,
        "metadata": {"runtime": "personal-codex-cli", "requested_model": model,
                     "backend_model": None, "backend_model_observed": False,
                     "identity_evidence": "guard-doctor+local-oauth-claims",
                     "model_evidence": "CLI 요청 인자만 확인; 실제 backend model 미관측"},
    }


class EventReader:
    """bounded JSONL 파서. 원문 대신 종료·usage·도구 사용 사실만 유지한다."""

    def __init__(self):
        self.buffer = bytearray()
        self.total = 0
        self.completed = False
        self.usage = None

    def feed(self, chunk):
        self.total += len(chunk)
        if self.total > MAX_STREAM:
            _fail("OUTPUT_LIMIT", "CLI JSONL 출력 한도를 넘었습니다.")
        self.buffer.extend(chunk)
        while b"\n" in self.buffer:
            line, _, tail = self.buffer.partition(b"\n")
            self.buffer = bytearray(tail)
            if len(line) > MAX_LINE:
                _fail("OUTPUT_LIMIT", "CLI 이벤트 한도를 넘었습니다.")
            if line.strip():
                self.event(line)
        if len(self.buffer) > MAX_LINE:
            _fail("OUTPUT_LIMIT", "CLI 이벤트 한도를 넘었습니다.")

    def event(self, line):
        try:
            event = json.loads(line)
            kind = event["type"]
            if not isinstance(kind, str):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            _fail("INVALID_EVENT", "CLI JSONL 형식이 올바르지 않습니다.")
        if kind in {"error", "turn.failed"}:
            _fail("TURN_FAILED", "CLI가 turn 실패를 보고했습니다.")
        item = event.get("item", {})
        item_type = item.get("type", "") if isinstance(item, dict) else ""
        if (kind.startswith("item.") and item_type not in {"agent_message", "reasoning"}
                or any(word in kind for word in ("tool", "command", "file_change", "web_search"))):
            _fail("TOOL_USE_FORBIDDEN", "CLI에서 허용하지 않은 도구/작업 이벤트를 관측했습니다.")
        if kind == "turn.completed":
            if self.completed:
                _fail("INVALID_EVENT", "여러 turn 완료 이벤트는 허용하지 않습니다.")
            self.completed = True
            usage = event.get("usage")
            if isinstance(usage, dict):
                observed = {k: usage[k] for k in ("input_tokens", "output_tokens", "cached_input_tokens")
                            if type(usage.get(k)) is int and usage[k] >= 0}
                if {"input_tokens", "output_tokens"} <= observed.keys():
                    self.usage = observed

    def finish(self):
        if self.buffer.strip():
            self.event(bytes(self.buffer))
        self.buffer.clear()
        if not self.completed:
            _fail("TURN_INCOMPLETE", "실제 turn.completed를 관측하지 못했습니다.")
        if self.usage is None:
            _fail("USAGE_UNOBSERVED", "완료 turn의 input/output token usage를 관측하지 못했습니다.")


def parse_candidate(data):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    try:
        result = json.loads(data, object_pairs_hook=unique_object)
        if not isinstance(result, dict) or set(result) != {"candidate"} or not isinstance(result["candidate"], str):
            raise ValueError()
        candidate = result["candidate"].encode("utf-8")
    except (ValueError, TypeError, UnicodeError):
        _fail("INVALID_FINAL_JSON", "최종 응답은 candidate source 문자열 하나인 JSON이어야 합니다.")
    if not candidate or len(candidate) > MAX_CANDIDATE or b"\x00" in candidate:
        _fail("INVALID_CANDIDATE", "후보 source가 비었거나 크기/문자 경계를 넘었습니다.")
    return candidate


def terminate_group(process):
    """자신이 생성한 child group만 종료하고 실제 wait 결과를 반환한다."""
    # 이미 reap한 PID는 재사용될 수 있다. 완료 관측 뒤에는 신호를 보내지 않는다.
    if process.returncode is not None:
        return process.returncode
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        return process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            return process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _fail("EXIT_UNOBSERVED", "child process의 실제 종료를 관측하지 못했습니다.")


def execute(selection, *, baseline, final_path, cancelled, timeout=240, on_spawn=None):
    """하나의 실제 CLI process/turn만 실행한다. cancelled는 Core projection 조회다."""
    if timeout < 180 or timeout > 3600:
        _fail("INVALID_TIMEOUT", "timeout은 180~3600초여야 합니다.", {"process_exited": True})
    final_path = Path(final_path)
    if final_path.exists() or final_path.is_symlink():
        _fail("UNSAFE_FILE", "최종 응답 경로는 아직 존재하지 않아야 합니다.", {"process_exited": True})
    reader = EventReader()
    metadata = dict(selection["metadata"], timeout_seconds=timeout, process_exited=False)
    process = None
    failure = None
    selector = selectors.DefaultSelector()
    try:
        # cwd에는 합성 source만 존재한다. oracle·저장소·개인 자료를 복사하지 않는다.
        with tempfile.TemporaryDirectory(prefix="g0b-model-", dir="/tmp") as temporary:
            workspace = Path(temporary)
            (workspace / "policy_check.py").write_bytes(baseline)
            prompt = (CONTRACT + "\n첨부 baseline source:\n" + baseline.decode("utf-8")).encode()
            command = [selection["binary"], "exec", "--model", selection["identity"]["model"],
                       "--sandbox", "read-only", "--ignore-user-config", "--ignore-rules",
                       "--skip-git-repo-check", "--ephemeral", "--cd", str(workspace),
                       "--json", "--output-schema", str(SCHEMA),
                       "--output-last-message", str(final_path), "-"]
            if cancelled():
                _fail("CANCELLED", "모델 시작 전에 취소 요청을 관측했습니다.", dict(metadata, process_exited=True))
            # stdin은 작은 고정 fixture이며 shell을 사용하지 않는다.
            with tempfile.TemporaryFile() as input_file:
                input_file.write(prompt)
                input_file.seek(0)
                process = subprocess.Popen(command, cwd=workspace, env=selection["env"],
                                           stdin=input_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           start_new_session=True)
            if on_spawn:
                on_spawn(process.pid)
            for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            deadline = time.monotonic() + timeout
            stderr_count = 0
            while selector.get_map() or process.poll() is None:
                if cancelled():
                    _fail("CANCELLED", "Core 취소 요청을 관측했습니다.")
                if time.monotonic() >= deadline:
                    _fail("RUNTIME_TIMEOUT", "명시한 CLI 제한 시간을 넘었습니다.")
                for key, _ in selector.select(0.1):
                    try:
                        chunk = os.read(key.fd, 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif key.data == "stdout":
                        reader.feed(chunk)
                    else:
                        stderr_count += len(chunk)
                        if stderr_count > MAX_STREAM:
                            _fail("OUTPUT_LIMIT", "CLI stderr 출력 한도를 넘었습니다.")
            metadata.update(exit_code=process.wait(), process_exited=True)
            if process.returncode != 0:
                _fail("CLI_EXIT_FAILED", "Codex CLI가 0이 아닌 exit code로 종료했습니다.")
            reader.finish()
            metadata.update(usage=reader.usage, turn_completed=True)
            candidate = parse_candidate(private_read(final_path, MAX_FINAL))
            # 결과에 비밀 형태가 있으면 DB artifact로 반입하기 전 차단한다.
            _guard("inspect", selection["env"], final_path)
    except RuntimeFailure as exc:
        failure = exc
    except Exception:
        failure = RuntimeFailure("RUNTIME_IO_FAILED", "CLI 실행 또는 출력 파일 접근에 실패했습니다.")
    finally:
        selector.close()
        if process is not None:
            try:
                metadata.update(exit_code=terminate_group(process), process_exited=True)
            except (RuntimeFailure, OSError):
                # wait 실패를 cleanup 예외로 덮거나 종료 관측으로 바꾸지 않는다.
                metadata.update(process_exited=False)
                metadata.pop("exit_code", None)
                if failure is None:
                    failure = RuntimeFailure("EXIT_UNOBSERVED", "child process의 실제 종료를 관측하지 못했습니다.")
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        else:
            metadata["process_exited"] = True
        if reader.usage is not None:
            metadata["usage"] = reader.usage
        metadata["turn_completed"] = reader.completed
        try:
            final_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            if failure is None:
                failure = RuntimeFailure("RUNTIME_IO_FAILED", "CLI 최종 응답 파일을 정리하지 못했습니다.")
    if failure is not None:
        failure.metadata.update(metadata)
        raise failure
    return candidate, metadata
