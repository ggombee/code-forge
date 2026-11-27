"""합성 CLI의 사용자 계약을 실제 subprocess 관찰로 검증한다."""

import importlib.util
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch


_SPEC = importlib.util.spec_from_file_location("g0b_oracle", Path(__file__).resolve().parents[1] / "oracle.py")
oracle = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(oracle)


# baseline의 텍스트를 치환하지 않고 사용자 계약으로부터 독립 작성한 수정 후보다.
_REPAIRED = textwrap.dedent('''\
    import argparse
    import json
    from pathlib import Path
    import shutil
    import sys

    class ContractParser(argparse.ArgumentParser):
        def error(self, message):
            print("FAIL: " + message, file=sys.stderr)
            raise SystemExit(2)

    parser = ContractParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--tool", required=True)
    args = parser.parse_args()
    try:
        value = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("FAIL: 설정 읽기 실패", file=sys.stderr)
        sys.exit(3)
    if not isinstance(value, dict) or value.get("enabled") is not True:
        print("FAIL: 정책 비활성", file=sys.stderr)
        sys.exit(4)
    if shutil.which(args.tool) is None:
        print("FAIL: 도구 부재", file=sys.stderr)
        sys.exit(5)
    print("PASS")
''').encode("utf-8")


class OracleContractTests(unittest.TestCase):
    def test_baseline_exposes_false_pass_to_consumer(self):
        result = oracle.verify(oracle.baseline_bytes())
        self.assertFalse(result["passed"])
        cases = {case["name"]: case for case in result["cases"]}
        for name in ("missing_config", "malformed_config", "missing_tool"):
            with self.subTest(name=name):
                case = cases[name]
                self.assertFalse(case["passed"])
                self.assertEqual(case["actual_exit"], 0)
                self.assertIn("PASS", case["stdout"])
        for name in ("disabled_config", "array_config", "numeric_enabled", "valid_config_tool_present"):
            with self.subTest(name=name):
                self.assertTrue(cases[name]["passed"])

    def test_independent_repair_satisfies_success_and_failure_contracts(self):
        result = oracle.verify(_REPAIRED)
        self.assertTrue(result["passed"], result["cases"])
        for case in result["cases"]:
            with self.subTest(name=case["name"]):
                if case["name"] == "valid_config_tool_present":
                    self.assertEqual(case["actual_exit"], 0)
                    self.assertIn("PASS", case["stdout"])
                else:
                    self.assertGreater(case["actual_exit"], 0)
                    self.assertIn("FAIL", case["stderr"])

    def test_pass_claim_and_zero_exit_cannot_override_failed_checks(self):
        result = oracle.verify(b'print("PASS")\n')
        self.assertFalse(result["passed"])
        cases = {case["name"]: case for case in result["cases"]}
        self.assertTrue(cases["valid_config_tool_present"]["passed"])
        for name in ("missing_config", "malformed_config", "missing_tool", "disabled_config"):
            self.assertFalse(cases[name]["passed"])

    def test_crash_with_fail_message_is_not_validation(self):
        candidate = b'print("FAIL", flush=True)\nraise ValueError("synthetic crash")\n'
        result = oracle.verify(candidate)
        self.assertFalse(result["passed"])
        for case in result["cases"]:
            self.assertFalse(case["passed"])
            self.assertGreater(case["actual_exit"], 0)
            self.assertIn("Traceback", case["stderr"])

    def test_workspace_creation_preserves_existing_contents_and_baseline(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            root = Path(temporary)
            existing = root / "policy_check.py"
            existing.write_text("기존 사용자 파일", encoding="utf-8")
            first = oracle.write_workspace(root)
            second = oracle.write_workspace(root)
            self.assertNotEqual(first["workspace"], second["workspace"])
            self.assertEqual(existing.read_text(encoding="utf-8"), "기존 사용자 파일")
            target = Path(first["workspace"]) / first["target_rel"]
            target.write_bytes(_REPAIRED)
            self.assertTrue(oracle.verify(target.read_bytes())["passed"])
            result = oracle.verify(oracle.baseline_bytes())
            self.assertFalse(result["passed"])
            cases = {case["name"]: case for case in result["cases"]}
            for name in ("missing_config", "malformed_config", "missing_tool"):
                self.assertFalse(cases[name]["passed"])
                self.assertEqual(cases[name]["actual_exit"], 0)

    def test_inherited_environment_is_not_forwarded(self):
        candidate = textwrap.dedent('''\
            import os
            if "G0B_SYNTHETIC_CREDENTIAL" in os.environ:
                print("FAIL: 상속된 환경")
                raise SystemExit(1)
        ''').encode("utf-8") + _REPAIRED
        with patch.dict(os.environ, {"G0B_SYNTHETIC_CREDENTIAL": "synthetic-only"}):
            result = oracle.verify(candidate)
        self.assertTrue(result["passed"], result["cases"])

    def test_hang_and_output_flood_are_rejected(self):
        candidates = (
            (b'import time\ntime.sleep(60)\n', "timeout"),
            (b'import os\nwhile True: os.write(1, b"x" * 8192)\n', "output_limit_exceeded"),
        )
        for candidate, reason in candidates:
            with self.subTest(reason=reason):
                with patch.object(oracle, "_CASE_TIMEOUT_SECONDS", 0.5), patch.object(oracle, "_MAX_OUTPUT_BYTES", 4096):
                    result = oracle.verify(candidate)
                self.assertFalse(result["passed"])
                for case in result["cases"]:
                    self.assertFalse(case["passed"])
                    self.assertEqual(case["error"], reason)
                    size = len(case["stdout"].encode()) + len(case["stderr"].encode())
                    self.assertLessEqual(size, 4096)

    def test_oversized_candidate_is_rejected_before_execution(self):
        with patch.object(oracle, "_MAX_CANDIDATE_BYTES", 128):
            result = oracle.verify(b'print("PASS")\n' + b"#" * 129)
        self.assertFalse(result["passed"])
        self.assertTrue(all(case["actual_exit"] is None for case in result["cases"]))


if __name__ == "__main__":
    unittest.main()
