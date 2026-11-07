"""통제된 G0b 합성 CLI 전용 독립 판정기.

부모는 이 파일의 digest를 고정하고 모델에는 baseline과 사용자 계약만 전달한다.
모델이 수정하는 workspace에는 oracle을 복사하지 않는다. 임시 환경과 실행 제한은
OS sandbox가 아니다. 임의 코드의 파일·네트워크 접근을 차단하는 서비스가 아니며,
기존 권한 안에서 이 합성 fixture의 수정 후보에만 사용한다. POSIX 실행 환경용이다.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time


_BASELINE = Path(__file__).resolve().parent / "fixtures" / "policy_check.py"
_PYTHON = str(Path(sys.executable).resolve())
_TOOL_NAME = "g0b_fixture_tool"
_MAX_CANDIDATE_BYTES = 1024 * 1024
_MAX_OUTPUT_BYTES = 64 * 1024
_CASE_TIMEOUT_SECONDS = 2.0

# 설정 바이트, PATH의 도구 유무, 성공 기대값, 선택적 생략 인자 순서다.
# 설정의 None은 파일 부재를 뜻한다.
_CASES = (
    ("missing_config", None, True, False),
    ("malformed_config", b'{"enabled":', True, False),
    ("missing_tool", b'{"enabled":true}', False, False),
    ("disabled_config", b'{"enabled":false}', True, False),
    ("array_config", b'[]', True, False),
    ("null_config", b'null', True, False),
    ("string_config", b'"enabled"', True, False),
    ("number_config", b'1', True, False),
    ("missing_enabled", b'{}', True, False),
    ("numeric_enabled", b'{"enabled":1}', True, False),
    ("string_enabled", b'{"enabled":"true"}', True, False),
    ("null_enabled", b'{"enabled":null}', True, False),
    ("invalid_encoding", b'\xff', True, False),
    ("missing_config_argument", b'{"enabled":true}', True, False, "--config"),
    ("missing_tool_argument", b'{"enabled":true}', True, False, "--tool"),
    ("valid_config_tool_present", b'{"enabled":true}', True, True),
)


def baseline_bytes() -> bytes:
    """수정하지 않는 배포 원본을 읽는다."""
    return _BASELINE.read_bytes()


def oracle_sha256() -> str:
    """부모가 별도로 보관·대조할 이 oracle 파일의 바이트 digest다."""
    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def write_workspace(root: Path) -> dict:
    """root 안에 새 작업 디렉토리를 만들며 기존 항목은 덮어쓰지 않는다."""
    baseline = baseline_bytes()
    root = Path(root).absolute()
    root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="g0b-fixture-", dir=root))
    try:
        with (workspace / "policy_check.py").open("xb") as target:
            target.write(baseline)
        with (workspace / "config.json").open("xb") as config:
            config.write(b'{"enabled":true}\n')
    except BaseException:
        shutil.rmtree(workspace)
        raise
    return {
        "workspace": str(workspace),
        "target_rel": "policy_check.py",
        "baseline_sha256": hashlib.sha256(baseline).hexdigest(),
    }


def _stop(process: subprocess.Popen) -> None:
    # 같은 프로세스 그룹의 자식이 출력 pipe를 붙잡는 경우도 정리한다.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.kill()
    except ProcessLookupError:
        pass


def _run(command: list[str], root: Path, env: dict[str, str]) -> dict:
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    remaining = _MAX_OUTPUT_BYTES
    error = None
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError:
        return {
            "actual_exit": None, "stdout": "", "stderr": "후보를 시작하지 못했습니다.",
            "error": "spawn_error",
        }

    deadline = time.monotonic() + _CASE_TIMEOUT_SECONDS
    selector = selectors.DefaultSelector()
    try:
        for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or process.poll() is None:
            left = deadline - time.monotonic()
            if left <= 0:
                error = "timeout"
                break
            for key, _ in selector.select(min(left, 0.05)):
                try:
                    chunk = os.read(key.fd, min(8192, remaining + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                captured[key.data].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    error = "output_limit_exceeded"
                    break
                remaining -= len(chunk)
            if error:
                break
    finally:
        _stop(process)
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            error = error or "termination_timeout"
        selector.close()
        process.stdout.close()
        process.stderr.close()

    return {
        "actual_exit": process.returncode,
        "stdout": captured["stdout"].decode("utf-8", errors="replace").replace(str(root), "<fixture>"),
        "stderr": captured["stderr"].decode("utf-8", errors="replace").replace(str(root), "<fixture>"),
        "error": error,
    }


def _verify_case(candidate: bytes, name: str, config: bytes | None,
                 tool_present: bool, expect_success: bool,
                 omitted_argument: str | None = None) -> dict:
    # 부모 환경을 복사하지 않는다. 사례마다 HOME·PATH·cwd·임시 파일을 새로 만든다.
    with tempfile.TemporaryDirectory(prefix="g0b-oracle-", dir="/tmp") as temporary:
        root = Path(temporary)
        for directory in ("home", "tmp", "bin", "empty-bin"):
            (root / directory).mkdir()
        script = root / "policy_check.py"
        script.write_bytes(candidate)
        config_path = root / "config.json"
        if config is not None:
            config_path.write_bytes(config)
        tool = root / "bin" / _TOOL_NAME
        # which가 가용성만 확인한다. 이 도구를 실행할 필요는 없다.
        tool.write_bytes(b"#!/bin/sh\nexit 97\n")
        tool.chmod(0o700)
        env = {
            "HOME": str(root / "home"),
            "TMPDIR": str(root / "tmp"),
            "PATH": str(root / ("bin" if tool_present else "empty-bin")),
            "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
        }
        command = [_PYTHON, "-I", "-B", str(script)]
        if omitted_argument != "--config":
            command.extend(["--config", str(config_path)])
        if omitted_argument != "--tool":
            command.extend(["--tool", _TOOL_NAME])
        observation = _run(command, root, env)

    stdout = observation["stdout"]
    combined = stdout + "\n" + observation["stderr"]
    has_pass = re.search(r"(?m)^\s*PASS\b", combined) is not None
    has_fail = re.search(r"(?m)^\s*FAIL\b", combined) is not None
    actual_exit = observation["actual_exit"]
    if expect_success:
        contract_met = (actual_exit == 0 and re.search(r"(?m)^\s*PASS\b", stdout) is not None
                        and not has_fail)
    else:
        contract_met = (actual_exit is not None and actual_exit > 0 and has_fail
                        and not has_pass and "Traceback (most recent call last)" not in combined)
    return {
        "name": name,
        "passed": observation["error"] is None and contract_met,
        "expected_exit": 0 if expect_success else "nonzero",
        **observation,
    }


def verify(candidate: bytes) -> dict:
    """모델의 주장 대신 실제 CLI 실행 결과로 고정 계약을 평가한다."""
    digest = oracle_sha256()
    if len(candidate) > _MAX_CANDIDATE_BYTES:
        cases = [{
            "name": "candidate_size", "passed": False, "expected_exit": 0,
            "actual_exit": None, "stdout": "", "stderr": "후보 크기가 허용 범위를 넘었습니다.",
            "error": "candidate_too_large",
        }]
    else:
        cases = [_verify_case(candidate, *case) for case in _CASES]
    return {
        "passed": all(case["passed"] for case in cases),
        "oracle_sha256": digest,
        "cases": cases,
    }
