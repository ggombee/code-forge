"""stdlib 기반의 단일 사용자 G0b 원장과 로컬 파일 반영.

모든 변경 API는 Work projection을 반환한다. apply의 영수증은 receipt에 있다.
조회 API는 복구나 모델 호출을 하지 않는다. 시간은 UTC epoch 초다.
identity와 verification은 신뢰하는 OS/runtime adapter의 관측 입력이며 문자열
자체가 인증이나 독립 검증을 수행하지 않는다. credential 입력은 받지 않는다.

SQLite writer lock은 이 Core를 사용하는 실행기를 fence한다. 같은 OS 사용자의
임의 파일 쓰기/디렉터리 이동까지 직렬화하는 sandbox는 아니다. 파일 교체와 DB
완료 커밋은 별개이며, 그 사이의 장애는 durable intent와 digest로 조정한다.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import uuid


POLICY_VERSION = "g0b-single-user-file-v1"
_IDENTITY_KEYS = ("provider", "model", "account_fingerprint")
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
ATTEMPT_START_STATES = frozenset({"NEW", "REVIEW_READY", "VERIFICATION_FAILED", "RUNTIME_FAILED"})


class CoreError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _error(code, message):
    raise CoreError(code, message)


def _identity(value):
    if not isinstance(value, dict):
        _error("IDENTITY_UNKNOWN", "adapter가 관측한 identity가 필요합니다.")
    result = {}
    for key in _IDENTITY_KEYS:
        part = value.get(key)
        if not isinstance(part, str) or part.strip().lower() in {
            "", "unknown", "none", "null", "unset", "n/a", "?",
        }:
            _error("IDENTITY_UNKNOWN", "provider, model, account fingerprint를 확인해야 합니다.")
        result[key] = part
    return result


def _match_identity(work, identity):
    if _identity(identity) != work["identity"]:
        _error("IDENTITY_MISMATCH", "작업에 고정된 identity와 다릅니다.")


def _revision(work, expected):
    if type(expected) is not int or expected != work["revision"]:
        _error("STALE_REVISION", "최신 revision을 다시 조회해야 합니다.")


def _runtime_observation(value, process_exited):
    # runtime이 정제한 종료·사용량 사실만 저장한다. 임의 문자열/중첩 payload는 받지 않는다.
    if not isinstance(value, dict) or type(process_exited) is not bool:
        _error("INVALID_RUNTIME_OBSERVATION", "정제된 runtime 관측과 실제 종료 관측 bool이 필요합니다.")
    result = {"process_exited": process_exited}
    for key in ("turn_completed", "worker_lease_released", "backend_model_observed"):
        if key in value:
            if type(value[key]) is not bool:
                _error("INVALID_RUNTIME_OBSERVATION", "runtime 관측 bool의 형식이 올바르지 않습니다.")
            result[key] = value[key]
    for key in ("exit_code", "timeout_seconds"):
        if key in value:
            if value[key] is not None and type(value[key]) is not int:
                _error("INVALID_RUNTIME_OBSERVATION", "runtime 종료 코드와 제한 시간은 정수여야 합니다.")
            result[key] = value[key]
    if value.get("process_exited", process_exited) is not process_exited:
        _error("INVALID_RUNTIME_OBSERVATION", "종료 관측 인자와 metadata가 다릅니다.")
    if not process_exited and result.get("exit_code") is not None:
        _error("INVALID_RUNTIME_OBSERVATION", "종료 미관측에 종료 코드를 기록할 수 없습니다.")
    if "usage" in value:
        usage = value["usage"]
        if not isinstance(usage, dict):
            _error("INVALID_RUNTIME_OBSERVATION", "사용량은 관측한 정수 필드만 기록합니다.")
        result["usage"] = {}
        for key in ("input_tokens", "output_tokens", "cached_input_tokens"):
            if key in usage:
                if type(usage[key]) is not int or usage[key] < 0:
                    _error("INVALID_RUNTIME_OBSERVATION", "사용량은 0 이상의 정수여야 합니다.")
                result["usage"][key] = usage[key]
    return result


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _is_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(
        ch in "0123456789abcdef" for ch in value
    )


def _absolute(path):
    path = Path(path)
    if ".." in path.parts:
        _error("INVALID_PATH", "상위 경로 참조는 허용하지 않습니다.")
    return path.absolute()


def _target_parts(target_rel):
    if not isinstance(target_rel, str) or not target_rel or "\x00" in target_rel:
        _error("INVALID_PATH", "상대 target 경로가 필요합니다.")
    parts = target_rel.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _error("INVALID_PATH", "절대 경로, 빈 구성요소, 상위 경로 참조는 허용하지 않습니다.")
    return parts


@contextmanager
def _directory(path, *, create=False):
    """각 구성요소를 no-follow로 열고 최종 디렉터리 fd를 유지한다."""
    path = _absolute(path)
    fd = os.open(path.anchor, _DIRECTORY_FLAGS)
    try:
        for part in path.parts[1:]:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                else:
                    os.fsync(fd)
            next_fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    except OSError as exc:
        raise CoreError("INVALID_PATH", "디렉터리 경계 또는 접근 권한을 확인할 수 없습니다.") from exc
    finally:
        os.close(fd)


def _owned(info, *, directory=False, private=False):
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode):
        _error("INVALID_PATH", "요청한 일반 파일/디렉터리 종류와 다릅니다.")
    if info.st_uid != os.getuid():
        _error("PERMISSION_DENIED", "현재 OS 사용자가 소유한 파일/디렉터리여야 합니다.")
    mode = stat.S_IMODE(info.st_mode)
    if mode & (0o077 if private else 0o022) or mode & 0o7000:
        _error("PERMISSION_DENIED", "파일/디렉터리 권한이 허용 범위를 벗어났습니다.")
    if not directory and info.st_nlink != 1:
        _error("INVALID_PATH", "hard link 파일은 지원하지 않습니다.")


def _inode(info):
    return [info.st_dev, info.st_ino]


def _read_fd(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


@contextmanager
def _target(workspace, target_rel, binding=None):
    parts = _target_parts(target_rel)
    with _directory(workspace) as root_fd:
        parent_fd = os.dup(root_fd)
        target_fd = None
        try:
            chain = []
            info = os.fstat(parent_fd)
            _owned(info, directory=True)
            chain.append(_inode(info))
            for part in parts[:-1]:
                next_fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
                info = os.fstat(parent_fd)
                _owned(info, directory=True)
                chain.append(_inode(info))
            target_fd = os.open(
                parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=parent_fd,
            )
            info = os.fstat(target_fd)
            _owned(info)
            observed = {"directories": chain, "mode": stat.S_IMODE(info.st_mode)}
            if binding is not None and observed != binding:
                _error("PERMISSION_DENIED", "대상 경계 또는 파일 모드가 작업 생성 뒤 달라졌습니다.")
            yield parent_fd, parts[-1], target_fd, observed
        except OSError as exc:
            raise CoreError("INVALID_PATH", "존재하는 일반 파일과 symlink 없는 경로가 필요합니다.") from exc
        finally:
            if target_fd is not None:
                os.close(target_fd)
            os.close(parent_fd)


class Core:
    """전용 상태 디렉터리를 소유하는 POSIX 로컬 Core.

    used_units는 start_attempt가 커밋한 모델 호출 예약 횟수다. 실패/취소 때
    환불하지 않으며 토큰/금액 상한을 의미하지 않는다. identity에는 세 고정
    식별 필드만 남긴다. adapter는 검증 cases에도 credential을 넣지 않아야 한다.
    """

    def __init__(self, state_dir: Path):
        self.state_dir = _absolute(state_dir)
        self.db_path = self.state_dir / "core.sqlite3"
        with _directory(self.state_dir, create=True) as fd:
            info = os.fstat(fd)
            if info.st_uid != os.getuid():
                _error("PERMISSION_DENIED", "상태 디렉터리 소유자가 다릅니다.")
            os.fchmod(fd, 0o700)
            self._state_inode = _inode(info)
            # SQLite 최초 생성에도 넓은 umask의 영향을 받지 않는다.
            db_fd = os.open("core.sqlite3", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            try:
                db_info = os.fstat(db_fd)
                if not stat.S_ISREG(db_info.st_mode) or db_info.st_uid != os.getuid() or db_info.st_nlink != 1:
                    _error("PERMISSION_DENIED", "상태 DB 소유권 또는 파일 종류가 올바르지 않습니다.")
                os.fchmod(db_fd, 0o600)
                os.fsync(db_fd)
            finally:
                os.close(db_fd)
            os.fsync(fd)
        self._secure_files(repair=True)
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("BEGIN IMMEDIATE")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                _error("SCHEMA_VERSION", "지원하지 않는 상태 DB 버전입니다.")
            conn.execute("CREATE TABLE IF NOT EXISTS works (work_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            conn.execute("""CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL,
                revision INTEGER NOT NULL, type TEXT NOT NULL, state TEXT NOT NULL,
                timestamp REAL NOT NULL, details TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS apply_keys (
                work_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (work_id, idempotency_key))""")
            conn.execute("PRAGMA user_version=1")
            conn.commit()
        self._secure_files()

    @contextmanager
    def _state_directory(self):
        with _directory(self.state_dir) as fd:
            info = os.fstat(fd)
            _owned(info, directory=True, private=True)
            if _inode(info) != self._state_inode or stat.S_IMODE(info.st_mode) != 0o700:
                _error("PERMISSION_DENIED", "상태 디렉터리 경계가 달라졌습니다.")
            yield fd

    def _secure_files(self, *, repair=False):
        with self._state_directory() as fd:
            for name in os.listdir(fd):
                try:
                    file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                except FileNotFoundError:
                    # 마지막 SQLite 연결 종료와 sidecar 정리가 겹칠 수 있다.
                    continue
                except OSError as exc:
                    raise CoreError("PERMISSION_DENIED", "상태 파일을 안전하게 열 수 없습니다.") from exc
                try:
                    info = os.fstat(file_fd)
                    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                        _error("PERMISSION_DENIED", "상태 파일 소유권 또는 종류가 올바르지 않습니다.")
                    if repair:
                        os.fchmod(file_fd, 0o600)
                    else:
                        _owned(info, private=True)
                finally:
                    os.close(file_fd)

    @contextmanager
    def _connection(self, *, write=False):
        self._secure_files()
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=0, isolation_level=None)
            conn.execute("PRAGMA synchronous=FULL")
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            if write:
                conn.commit()
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise CoreError("CORE_BUSY", "다른 Core 변경이 진행 중입니다. 최신 상태를 조회하십시오.") from exc
            raise CoreError("STORAGE_ERROR", "SQLite 작업을 완료하지 못했습니다.") from exc
        except sqlite3.Error as exc:
            raise CoreError("STORAGE_ERROR", "SQLite 상태를 읽거나 저장하지 못했습니다.") from exc
        finally:
            if conn is not None:
                conn.close()

    def _load(self, conn, work_id):
        row = conn.execute("SELECT payload FROM works WHERE work_id=?", (work_id,)).fetchone()
        if row is None:
            _error("WORK_NOT_FOUND", "작업이 없습니다.")
        return json.loads(row[0])

    def _save(self, conn, work, event, details=None, *, new=False):
        now = time.time()
        if not new:
            work["revision"] += 1
        work["updated_at"] = now
        conn.execute(
            "INSERT INTO works VALUES (?, ?) ON CONFLICT(work_id) DO UPDATE SET payload=excluded.payload",
            (work["work_id"], json.dumps(work, ensure_ascii=False)),
        )
        conn.execute(
            "INSERT INTO events (work_id, revision, type, state, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)",
            (work["work_id"], work["revision"], event, work["state"], now,
             json.dumps(details or {}, ensure_ascii=False)),
        )

    def _artifact(self, work):
        name = work.get("candidate_file")
        if not name or Path(name).name != name:
            _error("STALE_APPROVAL", "후보 artifact가 없습니다.")
        with self._state_directory() as fd:
            try:
                artifact_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                try:
                    _owned(os.fstat(artifact_fd), private=True)
                    data = _read_fd(artifact_fd)
                finally:
                    os.close(artifact_fd)
            except OSError as exc:
                raise CoreError("STALE_APPROVAL", "후보 artifact를 읽을 수 없습니다.") from exc
        if _sha256(data) != work["candidate_sha256"]:
            _error("STALE_APPROVAL", "후보 artifact digest가 달라졌습니다.")
        return data

    def _write_artifact(self, candidate):
        name = "candidate-" + uuid.uuid4().hex + ".bin"
        with self._state_directory() as fd:
            artifact_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(artifact_fd, "wb") as stream:
                stream.write(candidate)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(fd)
        return name

    def create_work(self, workspace: Path, target_rel: str, identity: dict, budget_units: int = 1) -> dict:
        identity = _identity(identity)
        if type(budget_units) is not int or budget_units < 0:
            _error("INVALID_BUDGET", "호출 횟수 상한은 0 이상의 정수여야 합니다.")
        workspace = _absolute(workspace)
        _target_parts(target_rel)
        target_path = workspace / target_rel
        if self.state_dir == target_path or self.state_dir in target_path.parents:
            _error("INVALID_PATH", "Core 상태 파일은 작업 대상으로 사용할 수 없습니다.")
        with _target(workspace, target_rel) as (_, _, fd, binding):
            baseline = _sha256(_read_fd(fd))
        now = time.time()
        work = {
            "work_id": uuid.uuid4().hex, "revision": 0, "state": "NEW",
            "identity": identity, "workspace": str(workspace), "target_rel": target_rel,
            "baseline_sha256": baseline, "budget_units": budget_units, "used_units": 0,
            "attempt_id": None, "lease_generation": 0, "executor_pid": None,
            "candidate_sha256": None, "candidate_file": None, "verification": None,
            "approval_id": None, "approval": None, "receipt": None,
            "runtime_failure": None, "cancel_requested": False,
            "policy_version": POLICY_VERSION, "target_binding": binding,
            "apply_intent": None, "created_at": now, "updated_at": now,
        }
        with self._connection(write=True) as conn:
            self._save(conn, work, "WORK_CREATED", new=True)
        return work

    def get_work(self, work_id: str) -> dict:
        with self._connection() as conn:
            return self._load(conn, work_id)

    def list_work(self) -> list[dict]:
        with self._connection() as conn:
            return [json.loads(row[0]) for row in conn.execute("SELECT payload FROM works ORDER BY rowid")]

    def events(self, work_id: str) -> list[dict]:
        with self._connection() as conn:
            self._load(conn, work_id)
            rows = conn.execute(
                "SELECT sequence, revision, type, state, timestamp, details FROM events WHERE work_id=? ORDER BY sequence",
                (work_id,),
            ).fetchall()
        return [dict(sequence=row[0], work_id=work_id, revision=row[1], type=row[2],
                     state=row[3], timestamp=row[4], details=json.loads(row[5])) for row in rows]

    def start_attempt(self, work_id, *, expected_revision: int, identity: dict,
                      executor_pid: int | None = None) -> dict:
        if executor_pid is not None and (type(executor_pid) is not int or executor_pid <= 0):
            _error("INVALID_PID", "executor_pid는 adapter가 관측한 양의 PID여야 합니다.")
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _match_identity(work, identity)
            _revision(work, expected_revision)
            if work["state"] == "RUNNING":
                _error("ATTEMPT_RUNNING", "이미 실행 중인 attempt가 있습니다.")
            if work["state"] == "RUNTIME_UNKNOWN":
                _error("RUNTIME_UNKNOWN", "기존 실행의 종료·외부효과가 미확정입니다. 새 호출을 시작할 수 없습니다.")
            if work["state"] not in ATTEMPT_START_STATES:
                _error("INVALID_STATE", "이 상태에서는 새 attempt를 시작할 수 없습니다.")
            if work["used_units"] >= work["budget_units"]:
                _error("BUDGET_EXHAUSTED", "모델 호출 예약 횟수 상한에 도달했습니다.")
            work.update(state="RUNNING", used_units=work["used_units"] + 1,
                        attempt_id=uuid.uuid4().hex, lease_generation=work["lease_generation"] + 1,
                        executor_pid=executor_pid, candidate_sha256=None, candidate_file=None,
                        verification=None, approval_id=None, approval=None,
                        runtime_failure=None, cancel_requested=False)
            self._save(conn, work, "ATTEMPT_STARTED")
        return work

    def runtime_failure(self, work_id, *, expected_revision: int, attempt_id: str,
                        lease_generation: int, error_code: str, error_message: str,
                        runtime_metadata: dict, process_exited: bool) -> dict:
        """신뢰하는 runtime의 정제된 오류만 기록한다. 원시 exception/auth 입력 API가 아니다.

        종료 미관측은 같은 attempt의 후속 종료 관측만 받으며 후보 제출로 회복하지 않는다.
        오류 문구는 runtime의 고정 문구여야 하며 child 출력·인증 문자열을 전달하지 않는다.
        """
        if (not isinstance(error_code, str) or not 1 <= len(error_code) <= 64
                or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in error_code)
                or not isinstance(error_message, str) or not 1 <= len(error_message) <= 512
                or not all(ch.isprintable() for ch in error_message)):
            _error("INVALID_RUNTIME_OBSERVATION", "runtime의 고정 오류 코드와 정제된 문구가 필요합니다.")
        observation = _runtime_observation(runtime_metadata, process_exited)
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _revision(work, expected_revision)
            if (work["state"] not in {"RUNNING", "CANCEL_REQUESTED", "RUNTIME_UNKNOWN"}
                    or not attempt_id or work["attempt_id"] != attempt_id
                    or type(lease_generation) is not int or work["lease_generation"] != lease_generation):
                _error("STALE_ATTEMPT", "현재 실패 대상 attempt/lease가 아닙니다.")
            cancelled = work.get("cancel_requested", False) or work["state"] == "CANCEL_REQUESTED"
            failure = {"attempt_id": attempt_id, "lease_generation": lease_generation,
                       "error_code": error_code, "error_message": error_message,
                       "runtime_metadata": observation, "process_exited": process_exited}
            work.update(state="RUNTIME_FAILED" if process_exited else "RUNTIME_UNKNOWN",
                        runtime_failure=failure, cancel_requested=cancelled,
                        candidate_sha256=None, candidate_file=None, verification=None,
                        approval_id=None, approval=None)
            if process_exited:
                work.update(executor_pid=None, lease_generation=work["lease_generation"] + 1)
                if cancelled:
                    work["state"] = "CANCELLED"
            self._save(conn, work, work["state"], failure)
        return work

    def record_candidate(self, work_id, *, expected_revision: int, attempt_id: str,
                         lease_generation: int, candidate: bytes, verification: dict) -> dict:
        if not isinstance(candidate, bytes):
            _error("INVALID_CANDIDATE", "후보는 bytes여야 합니다.")
        if (not isinstance(verification, dict) or type(verification.get("passed")) is not bool
                or not _is_digest(verification.get("oracle_sha256"))
                or not isinstance(verification.get("cases"), list)):
            _error("VERIFICATION_FAILED", "독립 verifier의 passed, oracle digest, cases가 필요합니다.")
        evidence = {key: verification[key] for key in ("passed", "oracle_sha256", "cases")}
        try:
            evidence = json.loads(json.dumps(evidence, ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise CoreError("VERIFICATION_FAILED", "검증 결과는 JSON으로 기록할 수 있어야 합니다.") from exc
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _revision(work, expected_revision)
            if (work["state"] != "RUNNING" or work["attempt_id"] != attempt_id
                    or type(lease_generation) is not int or work["lease_generation"] != lease_generation):
                _error("STALE_ATTEMPT", "현재 실행 중인 attempt/lease의 결과가 아닙니다.")
            name = self._write_artifact(candidate)
            work.update(candidate_file=name, candidate_sha256=_sha256(candidate),
                        verification=evidence, approval_id=None, approval=None,
                        state="REVIEW_READY" if evidence["passed"] else "VERIFICATION_FAILED")
            self._save(conn, work, work["state"], {"candidate_sha256": work["candidate_sha256"]})
        return work

    def _binding(self, work):
        return {key: work[key] for key in (
            "workspace", "target_rel", "baseline_sha256", "candidate_sha256", "identity",
            "policy_version", "target_binding", "attempt_id", "lease_generation",
        )}

    def approve(self, work_id, *, expected_revision: int, artifact_sha256: str,
                identity: dict, expires_in: int = 300) -> dict:
        if type(expires_in) is not int or expires_in <= 0:
            _error("STALE_APPROVAL", "승인 유효 기간은 양의 정수 초여야 합니다.")
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _match_identity(work, identity)
            _revision(work, expected_revision)
            if work["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
                _error(work["state"], "runtime 실패 작업은 검증된 승인 후보가 아닙니다.")
            if work["state"] == "VERIFICATION_FAILED" or not (work["verification"] or {}).get("passed"):
                _error("VERIFICATION_FAILED", "검증을 통과한 후보만 승인할 수 있습니다.")
            if work["state"] != "REVIEW_READY" or artifact_sha256 != work["candidate_sha256"]:
                _error("STALE_APPROVAL", "승인 대상 후보가 현재 후보와 다릅니다.")
            self._artifact(work)
            with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (_, _, fd, _):
                if _sha256(_read_fd(fd)) != work["baseline_sha256"]:
                    _error("STALE_BASE", "대상이 baseline 이후 외부에서 변경됐습니다.")
            approval_id = uuid.uuid4().hex
            work.update(approval_id=approval_id, approval={
                "approval_id": approval_id, "binding": self._binding(work),
                "revision": work["revision"] + 1, "expires_at": time.time() + expires_in,
            })
            self._save(conn, work, "APPROVED", {"approval_id": approval_id})
        return work

    def _check_approval(self, work, approval_id):
        approval = work.get("approval")
        if (not approval or work["approval_id"] != approval_id
                or approval["approval_id"] != approval_id
                or approval["binding"] != self._binding(work)
                or approval["expires_at"] <= time.time()
                or work["policy_version"] != POLICY_VERSION):
            _error("STALE_APPROVAL", "승인이 없거나 만료됐거나 승인 binding이 달라졌습니다.")
        if not (work["verification"] or {}).get("passed"):
            _error("VERIFICATION_FAILED", "검증을 통과하지 않은 후보입니다.")

    def _key(self, conn, work_id, key):
        row = conn.execute("SELECT payload FROM apply_keys WHERE work_id=? AND idempotency_key=?",
                           (work_id, key)).fetchone()
        return json.loads(row[0]) if row else None

    def _save_key(self, conn, work, intent):
        conn.execute(
            "INSERT INTO apply_keys VALUES (?, ?, ?) ON CONFLICT(work_id, idempotency_key) DO UPDATE SET payload=excluded.payload",
            (work["work_id"], intent["idempotency_key"], json.dumps(intent, ensure_ascii=False)),
        )

    def _repeated(self, work, previous, approval_id):
        if previous["approval_id"] != approval_id:
            _error("STALE_APPROVAL", "같은 idempotency key를 다른 승인에 사용할 수 없습니다.")
        if previous.get("receipt") is not None:
            result = dict(work)
            result["receipt"] = previous["receipt"]
            return result
        if previous["status"] == "NOT_APPLIED":
            _error("STALE_APPROVAL", "반영되지 않은 intent입니다. 새 승인과 새 key가 필요합니다.")
        _error("APPLY_UNKNOWN", "기존 반영 intent를 먼저 조정해야 합니다.")

    def apply(self, work_id, *, expected_revision: int, approval_id: str, identity: dict,
              idempotency_key: str, fail_after_replace: bool = False) -> dict:
        if type(fail_after_replace) is not bool:
            _error("INVALID_REQUEST", "fail_after_replace는 bool이어야 합니다.")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            _error("INVALID_IDEMPOTENCY_KEY", "비어 있지 않은 idempotency key가 필요합니다.")
        # 조회는 순수 projection이다. 복구는 이 명시적 변경 API에서만 수행한다.
        snapshot = self.get_work(work_id)
        _match_identity(snapshot, identity)
        if snapshot["state"] in {"APPLYING", "APPLY_UNKNOWN"}:
            self.reconcile(work_id)
        token = uuid.uuid4().hex
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _match_identity(work, identity)
            if work["state"] in {"RUNTIME_UNKNOWN", "RUNTIME_FAILED"}:
                _error(work["state"], "runtime 실패 작업은 반영할 수 없습니다.")
            previous = self._key(conn, work_id, idempotency_key)
            if previous is not None:
                return self._repeated(work, previous, approval_id)
            _revision(work, expected_revision)
            if work["state"] in {"APPLYING", "APPLY_UNKNOWN"}:
                _error("APPLY_UNKNOWN", "다른 반영 intent가 조정되지 않았습니다.")
            if work["state"] != "REVIEW_READY":
                _error("STALE_APPROVAL", "반영 가능한 승인 후보가 아닙니다.")
            self._check_approval(work, approval_id)
            if work["approval"]["revision"] != work["revision"]:
                _error("STALE_APPROVAL", "승인 revision 이후 작업이 변경됐습니다.")
            self._artifact(work)
            with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (_, name, fd, observed):
                if _sha256(_read_fd(fd)) != work["baseline_sha256"]:
                    _error("STALE_BASE", "대상이 baseline 이후 외부에서 변경됐습니다.")
                target_identity = (observed["directories"][-1], name)
            # 같은 target을 맡은 다른 Work의 미확정 intent도 자동 재반영하지 않는다.
            # 부모 identity와 파일명은 workspace 표현 및 파일 교체 뒤에도 같다.
            for (payload,) in conn.execute("SELECT payload FROM works WHERE work_id<>?", (work_id,)):
                other = json.loads(payload)
                if ((other["target_binding"]["directories"][-1], Path(other["target_rel"]).name) == target_identity
                        and other["state"] in {"APPLYING", "APPLY_UNKNOWN"}):
                    _error("APPLY_UNKNOWN", "같은 대상에 다른 Work의 미확정 intent가 있습니다.")
            intent = {"token": token, "idempotency_key": idempotency_key,
                      "approval_id": approval_id, "binding": self._binding(work),
                      "status": "PENDING", "revision": work["revision"] + 1,
                      "started_at": time.time(), "receipt": None}
            work.update(state="APPLYING", apply_intent=intent)
            self._save(conn, work, "APPLY_INTENT_RECORDED", {"idempotency_key": idempotency_key})
            self._save_key(conn, work, intent)
        # intent 커밋 뒤에만 실제 파일을 교체하며 두 번째 writer transaction이
        # lease/취소/조정 변경과 파일 효과를 직렬화한다.
        try:
            with self._connection(write=True) as conn:
                work = self._load(conn, work_id)
                current = work.get("apply_intent") or {}
                if (work["state"] != "APPLYING" or current.get("token") != token
                        or current.get("status") != "PENDING"
                        or current.get("revision") != work["revision"]
                        or current.get("binding") != self._binding(work)):
                    _error("STALE_APPROVAL", "반영 소유권이 이미 조정되거나 변경됐습니다.")
                _match_identity(work, identity)
                self._check_approval(work, approval_id)
                candidate = self._artifact(work)
                self._replace(work, candidate, fail_after_replace=fail_after_replace)
                self._complete(conn, work, recovered=False)
            return work
        except Exception:
            self._mark_unknown(work_id, token)
            raise

    def _replace(self, work, candidate, *, fail_after_replace):
        with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (parent_fd, name, fd, _):
            if _sha256(_read_fd(fd)) != work["baseline_sha256"]:
                _error("STALE_BASE", "반영 직전 baseline 비교가 실패했습니다.")
            temporary = ".g0b-" + uuid.uuid4().hex + ".tmp"
            temporary_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                   0o600, dir_fd=parent_fd)
            replaced = False
            try:
                with os.fdopen(temporary_fd, "wb") as stream:
                    stream.write(candidate)
                    stream.flush()
                    os.fchmod(stream.fileno(), work["target_binding"]["mode"])
                    os.fsync(stream.fileno())
                # 경로를 다시 열어 이동/교체된 부모나 target을 교체 전에 거부한다.
                with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (check_parent, _, check_fd, _):
                    if _inode(os.fstat(check_parent)) != _inode(os.fstat(parent_fd)):
                        _error("INVALID_PATH", "반영 직전 대상 부모가 달라졌습니다.")
                    if _sha256(_read_fd(check_fd)) != work["baseline_sha256"]:
                        _error("STALE_BASE", "반영 직전 대상 digest가 달라졌습니다.")
                    os.replace(temporary, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                    replaced = True
                    if fail_after_replace:
                        raise RuntimeError("테스트용 반영 직후 응답 유실")
                os.fsync(parent_fd)
                with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (_, _, read_fd, _):
                    if _sha256(_read_fd(read_fd)) != work["candidate_sha256"]:
                        _error("APPLY_UNKNOWN", "반영 후 readback digest가 후보와 다릅니다.")
                    os.fsync(read_fd)
            finally:
                if not replaced:
                    try:
                        os.unlink(temporary, dir_fd=parent_fd)
                    except FileNotFoundError:
                        pass

    def _mark_unknown(self, work_id, token):
        # 실패 기록도 같은 intent일 때만 갱신한다. 원래 예외를 가리지 않는다.
        try:
            with self._connection(write=True) as conn:
                work = self._load(conn, work_id)
                intent = work.get("apply_intent") or {}
                if work["state"] == "APPLYING" and intent.get("token") == token:
                    work["state"] = "APPLY_UNKNOWN"
                    self._save(conn, work, "APPLY_UNKNOWN")
        except (CoreError, OSError):
            pass

    def _complete(self, conn, work, *, recovered):
        intent = work["apply_intent"]
        receipt = {
            "work_id": work["work_id"], "target": str(Path(work["workspace"]) / work["target_rel"]),
            "workspace": work["workspace"], "target_rel": work["target_rel"],
            "base_sha256": work["baseline_sha256"], "baseline_sha256": work["baseline_sha256"],
            "artifact_sha256": work["candidate_sha256"], "readback_sha256": work["candidate_sha256"],
            "target_sha256": work["candidate_sha256"],
            "idempotency_key": intent["idempotency_key"], "approval_id": intent["approval_id"],
            "effect": {"kind": "local_file_digest_readback", "recovered": recovered,
                       "replace_observed": not recovered, "target_fsynced": True},
            "timestamp": time.time(),
        }
        intent.update(status="APPLIED", receipt=receipt)
        work.update(state="APPLIED", receipt=receipt)
        self._save_key(conn, work, intent)
        self._save(conn, work, "APPLIED", {"recovered": recovered, "readback_sha256": work["candidate_sha256"]})

    def reconcile(self, work_id) -> dict:
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            if work["state"] not in {"APPLYING", "APPLY_UNKNOWN"}:
                return work
            intent = work.get("apply_intent")
            if not intent or intent["status"] != "PENDING":
                _error("APPLY_UNKNOWN", "조정할 durable intent가 없습니다.")
            try:
                with _target(work["workspace"], work["target_rel"], work["target_binding"]) as (parent, _, fd, _):
                    observed = _sha256(_read_fd(fd))
                    if observed == work["candidate_sha256"]:
                        os.fsync(fd)
                        os.fsync(parent)
            except (CoreError, OSError):
                observed = None
            if observed == work["candidate_sha256"]:
                self._complete(conn, work, recovered=True)
            elif observed == work["baseline_sha256"]:
                intent.update(status="NOT_APPLIED", observed_sha256=observed)
                work.update(state="REVIEW_READY", approval_id=None, approval=None)
                self._save_key(conn, work, intent)
                self._save(conn, work, "APPLY_NOT_PERFORMED", {"observed_sha256": observed, "automatic_replay": False})
            else:
                work["state"] = "APPLY_UNKNOWN"
                self._save(conn, work, "APPLY_UNKNOWN", {"observed_sha256": observed})
        return work

    def request_cancel(self, work_id, *, expected_revision: int) -> dict:
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _revision(work, expected_revision)
            if work["state"] in {"APPLIED", "CANCELLED", "CANCEL_REQUESTED"}:
                return work
            if work["state"] in {"APPLYING", "APPLY_UNKNOWN"}:
                _error("APPLY_UNKNOWN", "반영 intent를 먼저 조정해야 취소 여부를 결정할 수 있습니다.")
            if work["state"] == "RUNTIME_UNKNOWN":
                if not work.get("cancel_requested", False):
                    work.update(cancel_requested=True, approval_id=None, approval=None)
                    self._save(conn, work, "CANCEL_REQUESTED", {"process_exited": False})
                return work
            work.update(state="CANCEL_REQUESTED", cancel_requested=True, approval_id=None, approval=None)
            self._save(conn, work, "CANCEL_REQUESTED")
        return work

    def finish_cancel(self, work_id, *, expected_revision: int, attempt_id: str | None,
                      lease_generation: int, process_exited: bool) -> dict:
        if type(process_exited) is not bool:
            _error("INVALID_EXIT_EVIDENCE", "process_exited에는 실제 종료 관측 bool이 필요합니다.")
        with self._connection(write=True) as conn:
            work = self._load(conn, work_id)
            _revision(work, expected_revision)
            cancelling = (work["state"] == "CANCEL_REQUESTED"
                          or work["state"] == "RUNTIME_UNKNOWN" and work.get("cancel_requested", False))
            if (not cancelling or work["attempt_id"] != attempt_id
                    or type(lease_generation) is not int or work["lease_generation"] != lease_generation):
                _error("STALE_ATTEMPT", "취소 대상 attempt/lease가 아닙니다.")
            if process_exited:
                work.update(state="CANCELLED", executor_pid=None,
                            lease_generation=work["lease_generation"] + 1)
                if work.get("runtime_failure"):
                    work["runtime_failure"]["process_exited"] = True
                    work["runtime_failure"]["runtime_metadata"]["process_exited"] = True
            self._save(conn, work, "CANCELLED" if process_exited else "CANCEL_EXIT_NOT_OBSERVED",
                       {"process_exited": process_exited})
        return work
