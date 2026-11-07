"""소비자 경계 검사. 합성 child는 오류/종료 검사 전용이며 제품 실증이 아니다.

실제 계정·모델·네트워크를 사용하지 않는다. 이 파일 작성 호출에서는 실행하지 않았다.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load("g0b_runtime_boundary", ROOT / "runtime.py")
# run.py의 실제 의존 모듈을 같은 파일에서 로드한다. 가짜 Core/oracle은 만들지 않는다.
core = load("g0b_core_boundary", ROOT / "core.py")
oracle = load("g0b_oracle_boundary", ROOT / "oracle.py")
with patch.dict(sys.modules, {"core": core, "oracle": oracle, "runtime": runtime}):
    cli = load("g0b_cli_boundary", ROOT / "run.py")


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="g0b-runtime-boundary-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.spawned = []

    def child(self, program):
        """선택한 child 행동만 재현하는 로컬 fixture. 실제 CLI 성공을 모사하지 않는다."""
        binary = self.root / "boundary-child"
        binary.write_text("#!" + sys.executable + "\n" + program, encoding="utf-8")
        binary.chmod(0o700)
        return {
            "binary": str(binary), "env": runtime.child_environment(str(binary)),
            "identity": {"provider": "synthetic-boundary", "model": "boundary-only",
                         "account_fingerprint": "synthetic-boundary"},
            "metadata": {"requested_model": "boundary-only", "backend_model_observed": False},
        }

    def execute(self, selection, cancelled=lambda: False):
        return runtime.execute(selection, baseline=b"print('PASS')\n",
                               final_path=self.root / "final.json", cancelled=cancelled,
                               on_spawn=self.spawned.append, timeout=180)

    def running_work(self, *, budget_units=2):
        workspace = self.root / "workspace"
        workspace.mkdir(mode=0o700)
        (workspace / "target.py").write_bytes(b"print('PASS')\n")
        ledger = core.Core(self.root / "state")
        identity = {"provider": "synthetic-boundary", "model": "boundary-only",
                    "account_fingerprint": "synthetic-boundary"}
        work = ledger.create_work(workspace, "target.py", identity, budget_units=budget_units)
        attempt = ledger.start_attempt(work["work_id"], expected_revision=work["revision"],
                                       identity=identity, executor_pid=os.getpid())
        return ledger, attempt

    def assert_failure(self, code, operation):
        with self.assertRaises(runtime.RuntimeFailure) as raised:
            operation()
        self.assertEqual(raised.exception.code, code)
        self.assertNotIn("비밀_오류_원문", raised.exception.message)
        self.assertNotIn("비밀_오류_원문", json.dumps(raised.exception.metadata))
        return raised.exception

    def test_invalid_final_json_after_observed_completion_has_no_candidate(self):
        ledger, attempt = self.running_work(budget_units=1)
        child = self.child("""
import json, pathlib, sys
pathlib.Path(sys.argv[sys.argv.index('--output-last-message') + 1]).write_text('{broken')
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':11,'output_tokens':7}}), flush=True)
""")
        failure = self.assert_failure("INVALID_FINAL_JSON", lambda: self.execute(child))
        self.assertTrue(failure.metadata["process_exited"])
        self.assertEqual(failure.metadata["exit_code"], 0)
        self.assertEqual(failure.metadata["usage"]["input_tokens"], 11)
        self.assertFalse((self.root / "final.json").exists())
        failed = cli._record_runtime_failure(ledger, attempt, failure)
        self.assertEqual(failed["state"], "RUNTIME_FAILED")
        self.assertIsNone(failed["candidate_sha256"])
        self.assertIsNone(failed["verification"])
        observer = cli.projection(self.root / "state")
        before = ledger.events(attempt["work_id"])
        reconnected = observer.get_work(attempt["work_id"])
        self.assertEqual(reconnected, failed)
        observation = cli.view(self.root / "state", reconnected)["runtime_observation"]
        self.assertEqual(observation["phase"], "RUNTIME_FAILED")
        self.assertEqual(observation["error"]["code"], "INVALID_FINAL_JSON")
        self.assertTrue(observation["process_exited"])
        self.assertEqual(before[-1]["details"]["runtime_metadata"]["usage"]["input_tokens"], 11)
        self.assertEqual(observer.events(attempt["work_id"]), before)
        args = cli.parser().parse_args(["--state-dir", str(self.root / "state"), "run", attempt["work_id"]])
        with patch.object(runtime.subprocess, "Popen") as spawn:
            with self.assertRaises(core.CoreError) as raised:
                cli.launch(args)
        self.assertEqual(raised.exception.code, "BUDGET_EXHAUSTED")
        spawn.assert_not_called()
        self.assertEqual(observer.events(attempt["work_id"]), before)

    def test_turn_failure_is_not_hidden_by_zero_exit_or_final_json(self):
        child = self.child("""
import json
print(json.dumps({'type':'turn.failed','error':{'message':'비밀_오류_원문'}}), flush=True)
""")
        failure = self.assert_failure("TURN_FAILED", lambda: self.execute(child))
        self.assertTrue(failure.metadata["process_exited"])

    def test_tool_event_is_rejected_and_child_is_reaped(self):
        child = self.child("""
import json, time
print(json.dumps({'type':'item.started','item':{'type':'command_execution','command':'비밀_오류_원문'}}), flush=True)
time.sleep(30)
""")
        failure = self.assert_failure("TOOL_USE_FORBIDDEN", lambda: self.execute(child))
        self.assertTrue(failure.metadata["process_exited"])
        with self.assertRaises(ProcessLookupError):
            os.kill(self.spawned[0], 0)

    def test_core_cancel_is_only_finished_after_actual_child_wait(self):
        state = self.root / "state"
        workspace = self.root / "workspace"
        workspace.mkdir(mode=0o700)
        (workspace / "target.py").write_bytes(b"print('PASS')\n")
        ledger = core.Core(state)
        identity = {"provider": "synthetic-boundary", "model": "boundary-only",
                    "account_fingerprint": "synthetic-boundary"}
        work = ledger.create_work(workspace, "target.py", identity)
        attempt = ledger.start_attempt(work["work_id"], expected_revision=work["revision"],
                                       identity=identity, executor_pid=os.getpid())

        def cancel_on_spawn(pid):
            self.spawned.append(pid)
            pending = ledger.request_cancel(work["work_id"], expected_revision=attempt["revision"])
            self.assertEqual(pending["state"], "CANCEL_REQUESTED")
            self.assertIsNone(pending["candidate_sha256"])

        child = self.child("import time\ntime.sleep(30)\n")
        with self.assertRaises(runtime.RuntimeFailure) as raised:
            runtime.execute(child, baseline=b"print('PASS')\n", final_path=state / "final.json",
                            cancelled=lambda: ledger.get_work(work["work_id"])["state"] == "CANCEL_REQUESTED",
                            timeout=180, on_spawn=cancel_on_spawn)
        self.assertEqual(raised.exception.code, "CANCELLED")
        self.assertTrue(raised.exception.metadata["process_exited"])
        with self.assertRaises(ProcessLookupError):
            os.kill(self.spawned[0], 0)
        completed = cli._finish_cancel(ledger, attempt)
        self.assertEqual(completed["state"], "CANCELLED")
        self.assertGreater(completed["lease_generation"], attempt["lease_generation"])

    def test_unobserved_usage_and_missing_completion_are_failures(self):
        for program, code in [
            ("print('{\"type\":\"turn.completed\"}', flush=True)\n", "USAGE_UNOBSERVED"),
            ("print('{\"type\":\"thread.started\"}', flush=True)\n", "TURN_INCOMPLETE"),
        ]:
            with self.subTest(code=code):
                self.assert_failure(code, lambda: self.execute(self.child(program)))

    def test_absent_personal_environment_blocks_before_any_process(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(runtime.subprocess, "Popen") as spawn:
            self.assert_failure("IDENTITY_UNKNOWN", lambda: runtime.preflight(
                codex_binary=sys.executable, model="boundary-only", expected_account="missing@example.invalid"))
        spawn.assert_not_called()

    def test_missing_oauth_account_blocks_before_model_process(self):
        fake_home = self.root / "home"
        fake_home.mkdir()
        codex_home = fake_home / ".codex"
        codex_home.mkdir()
        policy_dir = fake_home / ".config/personal-project-guard"
        policy_dir.mkdir(parents=True)
        # guard 성공과 auth 관측 실패의 경계를 분리한다. 실제 guard 검증을 대신하지 않는다.
        (policy_dir / "local-policy.json").write_text(json.dumps({
            "personal_profile": str(codex_home), "personal_account_sha256": "0" * 64}))
        environment = {"CODEX_HOME": str(codex_home), "CODEX_AUTO_ACCOUNT_SELECTED": "personal",
                       "FORGE_GLOW_CODEX_ACCOUNT": "personal"}
        with patch.object(runtime.Path, "home", return_value=fake_home), \
                patch.dict(os.environ, environment, clear=True), \
                patch.object(runtime, "_guard"), patch.object(runtime.subprocess, "Popen") as spawn:
            self.assert_failure("IDENTITY_UNKNOWN", lambda: runtime.preflight(
                codex_binary=sys.executable, model="boundary-only", expected_account="missing@example.invalid"))
        spawn.assert_not_called()

    def test_ambiguous_final_objects_are_rejected(self):
        for value in (b'[]', b'{"candidate":1}', b'{"candidate":"x","extra":1}',
                      b'{"candidate":"x","candidate":"y"}'):
            with self.subTest(value=value):
                self.assert_failure("INVALID_FINAL_JSON", lambda: runtime.parse_candidate(value))

    def test_projection_on_missing_db_does_not_create_state(self):
        state = self.root / "absent-state"
        self.assertIsNone(cli.projection(state))
        self.assertFalse(state.exists())

    def test_projection_does_not_recover_or_reserve_a_call(self):
        fixture = oracle.write_workspace(self.root / "fixture-root")
        ledger = core.Core(self.root / "state")
        identity = {"provider": "synthetic-boundary", "model": "boundary-only", "account_fingerprint": "fixture"}
        work = ledger.create_work(Path(fixture["workspace"]), fixture["target_rel"], identity)
        before = ledger.events(work["work_id"])
        observer = cli.projection(self.root / "state")
        self.assertEqual(observer.get_work(work["work_id"]), work)
        self.assertEqual(observer.events(work["work_id"]), before)
        self.assertEqual(observer.list_work()[0]["used_units"], 0)
        self.assertEqual(ledger.events(work["work_id"]), before)

    def test_live_child_with_unobserved_exit_blocks_cli_actions_and_cannot_finish_cancel(self):
        ledger, attempt = self.running_work()
        processes = []

        def unobserved(process):
            # 종료 관측기 실패만 주입한다. 생성·JSONL·Core·projection은 실제 경계를 사용한다.
            processes.append(process)
            raise runtime.RuntimeFailure("EXIT_UNOBSERVED", "child process의 실제 종료를 관측하지 못했습니다.")

        child = self.child("""
import json, time
print(json.dumps({'type':'item.started','item':{'type':'command_execution'}}), flush=True)
time.sleep(30)
""")
        try:
            with patch.object(runtime, "terminate_group", side_effect=unobserved):
                failure = self.assert_failure("TOOL_USE_FORBIDDEN", lambda: self.execute(child))
            self.assertFalse(failure.metadata["process_exited"])
            self.assertIsNone(processes[0].poll())
            unknown = cli._record_runtime_failure(ledger, attempt, failure)
            self.assertEqual(unknown["state"], "RUNTIME_UNKNOWN")
            self.assertFalse(unknown["runtime_failure"]["process_exited"])
            observer = cli.projection(self.root / "state")
            self.assertEqual(observer.get_work(attempt["work_id"]), unknown)
            before = observer.events(attempt["work_id"])
            for command in (
                ["run", attempt["work_id"]],
                ["approve", attempt["work_id"], "--artifact-sha256", "0" * 64,
                 "--expected-revision", str(unknown["revision"])],
                ["apply", attempt["work_id"], "--approval-id", "absent", "--idempotency-key", "blocked"],
            ):
                with self.subTest(command=command[0]):
                    args = cli.parser().parse_args(["--state-dir", str(self.root / "state")] + command)
                    with patch.object(runtime.subprocess, "Popen") as spawn:
                        with self.assertRaises(core.CoreError) as raised:
                            {"run": cli.launch, "approve": cli.approve, "apply": cli.apply}[command[0]](args)
                    self.assertEqual(raised.exception.code, "RUNTIME_UNKNOWN")
                    spawn.assert_not_called()
            self.assertEqual(observer.events(attempt["work_id"]), before)
            self.assertEqual(observer.get_work(attempt["work_id"])["used_units"], 1)
            args = argparse.Namespace(state_dir=self.root / "state", work_id=attempt["work_id"])
            pending = cli.cancel(args)
            self.assertEqual(pending["state"], "RUNTIME_UNKNOWN")
            self.assertTrue(pending["cancel_requested"])
            self.assertIsNone(processes[0].poll())
            runtime.terminate_group(processes[0])
            self.assertIsNotNone(processes[0].returncode)
            cancelled = cli._finish_cancel(ledger, attempt)
            self.assertEqual(cancelled["state"], "CANCELLED")
            self.assertTrue(cancelled["runtime_failure"]["process_exited"])
            self.assertEqual(observer.get_work(attempt["work_id"]), cancelled)
        finally:
            for process in processes:
                runtime.terminate_group(process)

    def test_lost_worker_reconcile_records_unknown_and_projection_never_replays_or_cancels_it(self):
        ledger, attempt = self.running_work()
        args = argparse.Namespace(state_dir=self.root / "state", work_id=attempt["work_id"])
        unknown = cli.reconcile(args)
        self.assertEqual(unknown["state"], "RUNTIME_UNKNOWN")
        self.assertEqual(unknown["runtime_failure"]["error_code"], "WORKER_LOST")
        self.assertFalse(unknown["runtime_failure"]["process_exited"])
        before = ledger.events(attempt["work_id"])
        self.assertEqual(before[-1]["type"], "RUNTIME_UNKNOWN")
        # sidecar의 이전 완료 관측이 원장의 더 늦은 종료불명을 덮지 못한다.
        runtime.private_write(cli.metadata_path(self.root / "state", attempt["work_id"]),
                              {"phase": "REVIEW_READY", "process_exited": True, "exit_code": 0,
                               "turn_completed": True, "usage": {"input_tokens": 999}})
        observer = cli.projection(self.root / "state")
        for _ in range(2):
            self.assertEqual(observer.get_work(attempt["work_id"]), unknown)
            observation = cli.view(self.root / "state", unknown)["runtime_observation"]
            self.assertEqual(observation["phase"], "RUNTIME_UNKNOWN")
            self.assertFalse(observation["process_exited"])
            self.assertNotIn("exit_code", observation)
            self.assertNotIn("usage", observation)
            self.assertTrue(observation["worker_lease_released"])
            self.assertEqual(cli.reconcile(args), unknown)
        self.assertEqual(observer.events(attempt["work_id"]), before)
        self.assertEqual(observer.list_work()[0]["used_units"], 1)
        self.assertEqual((self.root / "workspace/target.py").read_bytes(), b"print('PASS')\n")


if __name__ == "__main__":
    unittest.main()
