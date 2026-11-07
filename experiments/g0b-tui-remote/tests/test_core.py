"""임시 합성 파일만 사용하는 Core 소비자 회귀 검사. 네트워크/모델 호출 없음."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


CORE_PATH = Path(__file__).resolve().parents[1] / "core.py"
_spec = importlib.util.spec_from_file_location("g0b_core_regression", CORE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
Core, CoreError = _module.Core, _module.CoreError

IDENTITY = {"provider": "synthetic", "model": "fixed-local", "account_fingerprint": "synthetic-user"}
BASELINE = b"status = 'before'\n"
CANDIDATE = b"status = 'after'\n"
ORACLE = hashlib.sha256(b"fixed-synthetic-oracle-v1").hexdigest()


class CoreRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="g0b-core-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(mode=0o700)
        self.target = self.workspace / "target.txt"
        self.target.write_bytes(BASELINE)
        self.target.chmod(0o644)
        self.state_dir = self.root / "state"
        self.core = Core(self.state_dir)

    def assert_code(self, code, function, *args, **kwargs):
        with self.assertRaises(CoreError) as raised:
            function(*args, **kwargs)
        self.assertEqual(raised.exception.code, code)
        self.assertIsInstance(raised.exception.message, str)
        self.assertTrue(raised.exception.message)

    def new(self, *, budget=1, target_rel="target.txt"):
        return self.core.create_work(self.workspace, target_rel, IDENTITY, budget)

    def running(self, *, budget=1, target_rel="target.txt"):
        work = self.new(budget=budget, target_rel=target_rel)
        return self.core.start_attempt(work["work_id"], expected_revision=work["revision"],
                                       identity=IDENTITY, executor_pid=os.getpid())

    def record(self, running, *, passed=True, candidate=CANDIDATE):
        return self.core.record_candidate(
            running["work_id"], expected_revision=running["revision"],
            attempt_id=running["attempt_id"], lease_generation=running["lease_generation"],
            candidate=candidate,
            verification={"passed": passed, "oracle_sha256": ORACLE,
                          "cases": [{"name": "synthetic-output", "passed": passed}]},
        )

    def ready(self, *, budget=1, target_rel="target.txt"):
        return self.record(self.running(budget=budget, target_rel=target_rel))

    def fail_runtime(self, attempt, *, process_exited=True, **overrides):
        arguments = dict(expected_revision=attempt["revision"], attempt_id=attempt["attempt_id"],
                         lease_generation=attempt["lease_generation"], error_code="TURN_FAILED",
                         error_message="CLI가 turn 실패를 보고했습니다.",
                         runtime_metadata={"process_exited": process_exited}, process_exited=process_exited)
        arguments.update(overrides)
        return self.core.runtime_failure(attempt["work_id"], **arguments)

    def approved(self, *, target_rel="target.txt"):
        ready = self.ready(target_rel=target_rel)
        return self.core.approve(
            ready["work_id"], expected_revision=ready["revision"],
            artifact_sha256=ready["candidate_sha256"], identity=IDENTITY,
        )

    def apply_arguments(self, approved, *, key="effect-1"):
        return dict(expected_revision=approved["revision"], approval_id=approved["approval_id"],
                    identity=IDENTITY, idempotency_key=key)

    def crash_after_replace(self, approved):
        # 별도 Python 프로세스가 실제 교체 뒤 예외로 종료한다. LLM 실행은 없다.
        program = """
import importlib.util, json, pathlib, sys
spec = importlib.util.spec_from_file_location('g0b_child', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
core = module.Core(pathlib.Path(sys.argv[2]))
core.apply(sys.argv[3], **json.loads(sys.argv[4]), fail_after_replace=True)
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", program, str(CORE_PATH), str(self.state_dir),
             approved["work_id"], json.dumps(self.apply_arguments(approved))],
            capture_output=True, text=True, timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RuntimeError", result.stderr)
        self.assertEqual(self.target.read_bytes(), CANDIDATE)

    def test_reopen_and_projection_preserve_state_without_running_or_recovering(self):
        work = self.new()
        observer = Core(self.state_dir)
        self.assertEqual(observer.get_work(work["work_id"]), work)
        self.assertEqual(observer.list_work(), [work])
        events = observer.events(work["work_id"])
        self.assertEqual([event["type"] for event in events], ["WORK_CREATED"])
        self.assertEqual(observer.get_work(work["work_id"])["used_units"], 0)
        self.assertEqual(observer.events(work["work_id"]), events)
        self.assertEqual(self.target.read_bytes(), BASELINE)
        self.assertEqual(stat.S_IMODE(self.state_dir.stat().st_mode), 0o700)
        self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600
                            for path in self.state_dir.iterdir()))

    def test_apply_before_approval_and_unverified_approval_have_no_effect(self):
        ready = self.ready()
        self.assert_code("STALE_APPROVAL", self.core.apply, ready["work_id"],
                         expected_revision=ready["revision"], approval_id="invented",
                         identity=IDENTITY, idempotency_key="before-approval")
        new = self.new()
        self.assert_code("VERIFICATION_FAILED", self.core.approve, new["work_id"],
                         expected_revision=new["revision"], artifact_sha256=hashlib.sha256(CANDIDATE).hexdigest(),
                         identity=IDENTITY)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_unknown_identity_and_identity_changes_are_rejected(self):
        for field in IDENTITY:
            bad = dict(IDENTITY, **{field: "unknown"})
            self.assert_code("IDENTITY_UNKNOWN", self.core.create_work,
                             self.workspace, "target.txt", bad)
        new = self.new()
        other = dict(IDENTITY, account_fingerprint="another-user")
        self.assert_code("IDENTITY_MISMATCH", self.core.start_attempt, new["work_id"],
                         expected_revision=new["revision"], identity=other)
        ready = self.ready()
        self.assert_code("IDENTITY_MISMATCH", self.core.approve, ready["work_id"],
                         expected_revision=ready["revision"], artifact_sha256=ready["candidate_sha256"],
                         identity=other)
        approved = self.approved()
        args = self.apply_arguments(approved)
        args["identity"] = dict(IDENTITY, model="other-model")
        self.assert_code("IDENTITY_MISMATCH", self.core.apply, approved["work_id"], **args)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_revision_cas_and_single_active_attempt(self):
        running = self.running(budget=2)
        self.assert_code("STALE_REVISION", self.core.start_attempt, running["work_id"],
                         expected_revision=running["revision"] - 1, identity=IDENTITY)
        self.assert_code("ATTEMPT_RUNNING", self.core.start_attempt, running["work_id"],
                         expected_revision=running["revision"], identity=IDENTITY)
        ready = self.record(running)
        self.assert_code("STALE_REVISION", self.core.approve, ready["work_id"],
                         expected_revision=running["revision"], artifact_sha256=ready["candidate_sha256"],
                         identity=IDENTITY)
        approved = self.core.approve(ready["work_id"], expected_revision=ready["revision"],
                                     artifact_sha256=ready["candidate_sha256"], identity=IDENTITY)
        self.assertGreater(approved["revision"], ready["revision"])
        args = self.apply_arguments(approved)
        args["expected_revision"] = ready["revision"]
        self.assert_code("STALE_REVISION", self.core.apply, ready["work_id"], **args)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_verification_failure_is_durable_and_budget_reservation_is_not_refunded(self):
        failed = self.record(self.running(), passed=False)
        self.assertEqual(failed["state"], "VERIFICATION_FAILED")
        self.assertEqual(failed["used_units"], 1)
        self.assertEqual(Core(self.state_dir).get_work(failed["work_id"]), failed)
        self.assertEqual(self.core.events(failed["work_id"])[-1]["type"], "VERIFICATION_FAILED")
        self.assert_code("VERIFICATION_FAILED", self.core.approve, failed["work_id"],
                         expected_revision=failed["revision"], artifact_sha256=failed["candidate_sha256"],
                         identity=IDENTITY)
        self.assert_code("BUDGET_EXHAUSTED", self.core.start_attempt, failed["work_id"],
                         expected_revision=failed["revision"], identity=IDENTITY)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_zero_call_budget_blocks_attempt_without_reservation(self):
        work = self.new(budget=0)
        self.assert_code("BUDGET_EXHAUSTED", self.core.start_attempt, work["work_id"],
                         expected_revision=work["revision"], identity=IDENTITY)
        self.assertEqual(self.core.get_work(work["work_id"])["used_units"], 0)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_runtime_failure_survives_reopen_and_fences_late_candidate_without_verification(self):
        running = self.running()
        failed = self.fail_runtime(running, runtime_metadata={
            "process_exited": True, "exit_code": 0, "turn_completed": False,
            "usage": {"input_tokens": 11, "output_tokens": 7},
            "untrusted_payload": {"text": "기록하면_안_되는_외부_문자열"},
        })
        self.assertEqual(failed["state"], "RUNTIME_FAILED")
        self.assertEqual(failed["used_units"], 1)
        self.assertIsNone(failed["verification"])
        self.assertIsNone(failed["candidate_sha256"])
        self.assertIsNone(failed["executor_pid"])
        failure = failed["runtime_failure"]
        self.assertEqual(failure["error_code"], "TURN_FAILED")
        self.assertEqual(failure["error_message"], "CLI가 turn 실패를 보고했습니다.")
        self.assertEqual(failure["runtime_metadata"]["usage"], {"input_tokens": 11, "output_tokens": 7})
        self.assertNotIn("untrusted_payload", failure["runtime_metadata"])
        observer = Core(self.state_dir)
        events = observer.events(failed["work_id"])
        self.assertEqual(events[-1]["type"], "RUNTIME_FAILED")
        self.assertEqual(events[-1]["state"], "RUNTIME_FAILED")
        self.assertEqual(events[-1]["details"], failure)
        self.assertEqual(observer.get_work(failed["work_id"]), failed)
        self.assertEqual(observer.list_work(), [failed])
        self.assert_code("STALE_REVISION", self.record, running)
        self.assert_code("STALE_ATTEMPT", self.record, dict(running, revision=failed["revision"]))
        self.assert_code("RUNTIME_FAILED", self.core.approve, failed["work_id"],
                         expected_revision=failed["revision"], artifact_sha256=hashlib.sha256(CANDIDATE).hexdigest(),
                         identity=IDENTITY)
        self.assert_code("RUNTIME_FAILED", self.core.apply, failed["work_id"],
                         expected_revision=failed["revision"], approval_id="not-approved",
                         identity=IDENTITY, idempotency_key="failed-runtime")
        self.assert_code("BUDGET_EXHAUSTED", self.core.start_attempt, failed["work_id"],
                         expected_revision=failed["revision"], identity=IDENTITY)
        self.assertEqual(observer.get_work(failed["work_id"]), failed)
        self.assertEqual(observer.events(failed["work_id"]), events)
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_runtime_failure_retry_keeps_budget_and_rejects_old_revision_attempt_and_lease(self):
        old = self.running(budget=2)
        failed = self.fail_runtime(old)
        current = self.core.start_attempt(failed["work_id"], expected_revision=failed["revision"], identity=IDENTITY)
        self.assertEqual(current["used_units"], 2)
        self.assertIsNone(current["runtime_failure"])
        self.assertNotEqual(current["attempt_id"], old["attempt_id"])
        events = self.core.events(current["work_id"])
        self.assert_code("STALE_REVISION", self.fail_runtime, old)
        self.assert_code("STALE_ATTEMPT", self.fail_runtime, old, expected_revision=current["revision"])
        self.assert_code("STALE_ATTEMPT", self.fail_runtime, current, lease_generation=old["lease_generation"])
        self.assertEqual(self.core.get_work(current["work_id"]), current)
        self.assertEqual(self.core.events(current["work_id"]), events)
        ready = self.record(current)
        self.assertEqual(ready["state"], "REVIEW_READY")
        self.assertEqual(ready["used_units"], 2)

    def test_unobserved_exit_blocks_calls_approval_apply_and_candidate_until_exit_is_observed(self):
        running = self.running(budget=2)
        unknown = self.fail_runtime(running, process_exited=False)
        self.assertEqual(unknown["state"], "RUNTIME_UNKNOWN")
        self.assertEqual(unknown["executor_pid"], running["executor_pid"])
        self.assertEqual(unknown["lease_generation"], running["lease_generation"])
        events = self.core.events(unknown["work_id"])
        self.assertEqual(events[-1]["type"], "RUNTIME_UNKNOWN")
        observer = Core(self.state_dir)
        self.assertEqual(observer.get_work(unknown["work_id"]), unknown)
        self.assertEqual(observer.reconcile(unknown["work_id"]), unknown)
        self.assert_code("RUNTIME_UNKNOWN", observer.start_attempt, unknown["work_id"],
                         expected_revision=unknown["revision"], identity=IDENTITY)
        self.assert_code("RUNTIME_UNKNOWN", observer.approve, unknown["work_id"],
                         expected_revision=unknown["revision"], artifact_sha256=hashlib.sha256(CANDIDATE).hexdigest(),
                         identity=IDENTITY)
        self.assert_code("RUNTIME_UNKNOWN", observer.apply, unknown["work_id"],
                         expected_revision=unknown["revision"], approval_id="not-approved",
                         identity=IDENTITY, idempotency_key="must-not-apply")
        self.assert_code("STALE_ATTEMPT", self.record, dict(running, revision=unknown["revision"]))
        self.assertEqual(observer.events(unknown["work_id"]), events)
        self.assertEqual(observer.get_work(unknown["work_id"]), unknown)
        failed = self.fail_runtime(unknown)
        self.assertEqual(failed["state"], "RUNTIME_FAILED")
        self.assertTrue(failed["runtime_failure"]["process_exited"])
        self.assert_code("STALE_ATTEMPT", self.record, dict(running, revision=failed["revision"]))
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_cancelled_runtime_requires_observed_exit_and_keeps_failure_evidence(self):
        running = self.running()
        pending = self.core.request_cancel(running["work_id"], expected_revision=running["revision"])
        self.assert_code("STALE_REVISION", self.fail_runtime, running)
        unknown = self.fail_runtime(pending, process_exited=False)
        self.assertEqual(unknown["state"], "RUNTIME_UNKNOWN")
        self.assertTrue(unknown["cancel_requested"])
        self.assertFalse(unknown["runtime_failure"]["process_exited"])
        self.assertEqual(Core(self.state_dir).get_work(unknown["work_id"]), unknown)
        cancelled = self.fail_runtime(unknown)
        self.assertEqual(cancelled["state"], "CANCELLED")
        self.assertTrue(cancelled["runtime_failure"]["process_exited"])
        self.assertGreater(cancelled["lease_generation"], unknown["lease_generation"])
        self.assertEqual(self.core.events(cancelled["work_id"])[-1]["details"]["error_code"], "TURN_FAILED")
        self.assert_code("STALE_ATTEMPT", self.record, dict(running, revision=cancelled["revision"]))

    def test_cancel_requested_after_unknown_stays_unknown_until_finish_cancel_observes_exit(self):
        unknown = self.fail_runtime(self.running(), process_exited=False)
        pending = self.core.request_cancel(unknown["work_id"], expected_revision=unknown["revision"])
        self.assertEqual(pending["state"], "RUNTIME_UNKNOWN")
        self.assertTrue(pending["cancel_requested"])
        waiting = self.core.finish_cancel(pending["work_id"], expected_revision=pending["revision"],
                                         attempt_id=pending["attempt_id"], lease_generation=pending["lease_generation"],
                                         process_exited=False)
        self.assertEqual(waiting["state"], "RUNTIME_UNKNOWN")
        cancelled = self.core.finish_cancel(waiting["work_id"], expected_revision=waiting["revision"],
                                           attempt_id=waiting["attempt_id"], lease_generation=waiting["lease_generation"],
                                           process_exited=True)
        self.assertEqual(cancelled["state"], "CANCELLED")
        self.assertTrue(cancelled["runtime_failure"]["process_exited"])
        self.assertEqual(Core(self.state_dir).get_work(cancelled["work_id"]), cancelled)

    def test_runtime_failure_cannot_rewrite_applied_receipt_or_events(self):
        approved = self.approved()
        applied = self.core.apply(approved["work_id"], **self.apply_arguments(approved))
        events = self.core.events(applied["work_id"])
        inode = self.target.stat().st_ino
        self.assert_code("STALE_ATTEMPT", self.fail_runtime, applied)
        self.assertEqual(Core(self.state_dir).get_work(applied["work_id"]), applied)
        self.assertEqual(self.core.events(applied["work_id"]), events)
        self.assertEqual(self.target.read_bytes(), CANDIDATE)
        self.assertEqual(self.target.stat().st_ino, inode)

    def test_invalid_exit_observations_do_not_change_active_attempt(self):
        running = self.running()
        before = self.core.events(running["work_id"])
        for arguments in (
            {"process_exited": 1},
            {"runtime_metadata": {"process_exited": False}},
            {"process_exited": False, "runtime_metadata": {"process_exited": False, "exit_code": 0}},
            {"runtime_metadata": {"usage": {"input_tokens": True}}},
        ):
            with self.subTest(arguments=arguments):
                self.assert_code("INVALID_RUNTIME_OBSERVATION", self.fail_runtime, running, **arguments)
        self.assertEqual(self.core.get_work(running["work_id"]), running)
        self.assertEqual(self.core.events(running["work_id"]), before)

    def test_old_attempt_and_lease_cannot_supply_a_new_candidate(self):
        old = self.running(budget=2)
        failed = self.record(old, passed=False)
        current = self.core.start_attempt(failed["work_id"], expected_revision=failed["revision"], identity=IDENTITY)
        self.assertNotEqual(old["attempt_id"], current["attempt_id"])
        self.assertGreater(current["lease_generation"], old["lease_generation"])
        for attempt, generation in [(old["attempt_id"], old["lease_generation"]),
                                    (current["attempt_id"], old["lease_generation"])]:
            self.assert_code("STALE_ATTEMPT", self.core.record_candidate, current["work_id"],
                             expected_revision=current["revision"], attempt_id=attempt,
                             lease_generation=generation, candidate=CANDIDATE,
                             verification={"passed": True, "oracle_sha256": ORACLE, "cases": []})
        self.assertEqual(self.core.get_work(current["work_id"])["state"], "RUNNING")

    def test_candidate_digest_binding_and_changed_artifact_prevent_apply(self):
        ready = self.ready()
        self.assert_code("STALE_APPROVAL", self.core.approve, ready["work_id"],
                         expected_revision=ready["revision"], artifact_sha256="0" * 64, identity=IDENTITY)
        approved = self.core.approve(ready["work_id"], expected_revision=ready["revision"],
                                     artifact_sha256=ready["candidate_sha256"], identity=IDENTITY)
        (self.state_dir / approved["candidate_file"]).write_bytes(b"changed-after-approval")
        self.assert_code("STALE_APPROVAL", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_absolute_parent_reference_and_symlink_paths_are_rejected(self):
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside")
        (self.workspace / "link.txt").symlink_to(outside)
        (self.workspace / "linked-parent").symlink_to(self.root, target_is_directory=True)
        for target in [str(outside), "../outside.txt", "sub/../target.txt", "link.txt", "linked-parent/outside.txt"]:
            self.assert_code("INVALID_PATH", self.new, target_rel=target)
        self.assertEqual(outside.read_bytes(), b"outside")
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_symlink_parent_swap_after_approval_cannot_escape_workspace(self):
        sub = self.workspace / "sub"
        sub.mkdir(mode=0o700)
        (sub / "target.txt").write_bytes(BASELINE)
        approved = self.approved(target_rel="sub/target.txt")
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        (outside / "target.txt").write_bytes(b"protected-outside")
        sub.rename(self.workspace / "retired")
        sub.symlink_to(outside, target_is_directory=True)
        self.assert_code("INVALID_PATH", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual((outside / "target.txt").read_bytes(), b"protected-outside")
        self.assertEqual((self.workspace / "retired/target.txt").read_bytes(), BASELINE)

    def test_approval_expiry_has_zero_effect(self):
        ready = self.ready()
        with patch.object(_module.time, "time", return_value=1000.0):
            approved = self.core.approve(ready["work_id"], expected_revision=ready["revision"],
                                         artifact_sha256=ready["candidate_sha256"], identity=IDENTITY, expires_in=10)
        with patch.object(_module.time, "time", return_value=1011.0):
            self.assert_code("STALE_APPROVAL", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_external_baseline_or_mode_change_prevents_effect(self):
        approved = self.approved()
        self.target.write_bytes(b"external-edit")
        self.assert_code("STALE_BASE", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(self.target.read_bytes(), b"external-edit")
        self.target.write_bytes(BASELINE)
        self.target.chmod(0o600)
        self.assert_code("PERMISSION_DENIED", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_cancel_requires_exit_evidence_and_late_results_cannot_revive_candidate(self):
        running = self.running()
        pending = self.core.request_cancel(running["work_id"], expected_revision=running["revision"])
        self.assertEqual(pending["state"], "CANCEL_REQUESTED")
        pending = self.core.finish_cancel(pending["work_id"], expected_revision=pending["revision"],
                                         attempt_id=running["attempt_id"], lease_generation=running["lease_generation"],
                                         process_exited=False)
        self.assertEqual(pending["state"], "CANCEL_REQUESTED")
        late = dict(running, revision=pending["revision"])
        self.assert_code("STALE_ATTEMPT", self.record, late)
        cancelled = self.core.finish_cancel(pending["work_id"], expected_revision=pending["revision"],
                                           attempt_id=running["attempt_id"], lease_generation=running["lease_generation"],
                                           process_exited=True)
        self.assertEqual(cancelled["state"], "CANCELLED")
        self.assertIsNone(cancelled["executor_pid"])
        self.assertIsNone(cancelled["candidate_sha256"])
        self.assert_code("STALE_ATTEMPT", self.record, dict(running, revision=cancelled["revision"]))
        self.assertEqual(self.target.read_bytes(), BASELINE)

    def test_process_loss_reconcile_and_idempotent_retry_never_replace_twice(self):
        approved = self.approved()
        self.crash_after_replace(approved)
        target_inode = self.target.stat().st_ino
        restarted = Core(self.state_dir)
        unresolved = restarted.get_work(approved["work_id"])
        self.assertIn(unresolved["state"], {"APPLYING", "APPLY_UNKNOWN"})
        self.assertIsNone(unresolved["receipt"])
        before_events = restarted.events(approved["work_id"])
        restarted.list_work()
        self.assertEqual(restarted.events(approved["work_id"]), before_events)
        recovered = restarted.reconcile(approved["work_id"])
        self.assertEqual(recovered["state"], "APPLIED")
        receipt = recovered["receipt"]
        self.assertEqual(receipt["base_sha256"], hashlib.sha256(BASELINE).hexdigest())
        for field in ("artifact_sha256", "readback_sha256", "target_sha256"):
            self.assertEqual(receipt[field], hashlib.sha256(CANDIDATE).hexdigest())
        self.assertEqual(receipt["idempotency_key"], "effect-1")
        self.assertTrue(receipt["effect"]["recovered"])
        self.assertFalse(receipt["effect"]["replace_observed"])
        retry = restarted.apply(approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(retry["receipt"], receipt)
        self.assertEqual(restarted.reconcile(approved["work_id"])["receipt"], receipt)
        self.assertEqual(self.target.stat().st_ino, target_inode)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o644)
        args = self.apply_arguments(recovered, key="different-key")
        self.assert_code("STALE_APPROVAL", restarted.apply, approved["work_id"], **args)
        self.assertEqual(restarted.request_cancel(recovered["work_id"], expected_revision=recovered["revision"])["state"], "APPLIED")

    def test_apply_retry_reconciles_before_returning_receipt(self):
        approved = self.approved()
        with self.assertRaises(RuntimeError):
            self.core.apply(approved["work_id"], **self.apply_arguments(approved), fail_after_replace=True)
        inode = self.target.stat().st_ino
        retry = Core(self.state_dir).apply(approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(retry["state"], "APPLIED")
        self.assertTrue(retry["receipt"]["effect"]["recovered"])
        self.assertEqual(self.target.stat().st_ino, inode)

    def test_baseline_recovery_records_no_effect_and_requires_explicit_new_approval(self):
        approved = self.approved()
        with self.assertRaises(RuntimeError):
            self.core.apply(approved["work_id"], **self.apply_arguments(approved), fail_after_replace=True)
        self.target.write_bytes(BASELINE)
        reconciled = Core(self.state_dir).reconcile(approved["work_id"])
        self.assertEqual(reconciled["state"], "REVIEW_READY")
        self.assertEqual(reconciled["apply_intent"]["status"], "NOT_APPLIED")
        self.assertIsNone(reconciled["approval_id"])
        self.assertIsNone(reconciled["receipt"])
        inode = self.target.stat().st_ino
        self.assert_code("STALE_APPROVAL", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        self.assertEqual(self.target.stat().st_ino, inode)
        self.assertEqual(self.target.read_bytes(), BASELINE)
        renewed = self.core.approve(reconciled["work_id"], expected_revision=reconciled["revision"],
                                    artifact_sha256=reconciled["candidate_sha256"], identity=IDENTITY)
        applied = self.core.apply(renewed["work_id"], **self.apply_arguments(renewed, key="explicit-new-effect"))
        self.assertEqual(applied["state"], "APPLIED")
        self.assertFalse(applied["receipt"]["effect"]["recovered"])

    def test_unrelated_readback_remains_unknown_and_is_never_replayed(self):
        approved = self.approved()
        with self.assertRaises(RuntimeError):
            self.core.apply(approved["work_id"], **self.apply_arguments(approved), fail_after_replace=True)
        self.target.write_bytes(b"neither-baseline-nor-candidate")
        unknown = self.core.reconcile(approved["work_id"])
        self.assertEqual(unknown["state"], "APPLY_UNKNOWN")
        self.assertIsNone(unknown["receipt"])
        self.assert_code("APPLY_UNKNOWN", self.core.apply, approved["work_id"], **self.apply_arguments(approved))
        unknown = self.core.get_work(approved["work_id"])
        self.assert_code("APPLY_UNKNOWN", self.core.request_cancel, approved["work_id"], expected_revision=unknown["revision"])
        self.assertEqual(self.target.read_bytes(), b"neither-baseline-nor-candidate")

    def test_another_work_cannot_bypass_pending_intent_for_the_same_target(self):
        first = self.approved()
        other = self.approved()
        with self.assertRaises(RuntimeError):
            self.core.apply(first["work_id"], **self.apply_arguments(first), fail_after_replace=True)
        self.target.write_bytes(BASELINE)
        self.assert_code("APPLY_UNKNOWN", self.core.apply, other["work_id"],
                         **self.apply_arguments(other, key="other-work"))
        self.assertEqual(self.target.read_bytes(), BASELINE)
        self.assertEqual(self.core.get_work(other["work_id"])["state"], "REVIEW_READY")

    def test_nested_workspace_alias_cannot_bypass_pending_intent_after_target_replacement(self):
        nested = self.workspace / "sub"
        nested.mkdir(mode=0o700)
        target = nested / "target.txt"
        target.write_bytes(BASELINE)
        target.chmod(0o644)
        first = self.approved(target_rel="sub/target.txt")
        original_inode = target.stat().st_ino
        with self.assertRaises(RuntimeError):
            self.core.apply(first["work_id"], **self.apply_arguments(first), fail_after_replace=True)
        self.assertNotEqual(target.stat().st_ino, original_inode)
        target.write_bytes(BASELINE)
        unknown = self.core.get_work(first["work_id"])
        self.assertEqual(unknown["state"], "APPLY_UNKNOWN")

        other = self.core.create_work(nested, "target.txt", IDENTITY)
        running = self.core.start_attempt(other["work_id"], expected_revision=other["revision"],
                                          identity=IDENTITY, executor_pid=os.getpid())
        ready = self.record(running)
        approved = self.core.approve(ready["work_id"], expected_revision=ready["revision"],
                                     artifact_sha256=ready["candidate_sha256"], identity=IDENTITY)
        before_events = self.core.events(approved["work_id"])
        target_inode = target.stat().st_ino
        restarted = Core(self.state_dir)
        self.assert_code("APPLY_UNKNOWN", restarted.apply, approved["work_id"],
                         **self.apply_arguments(approved, key="nested-workspace-alias"))
        self.assertEqual(target.read_bytes(), BASELINE)
        self.assertEqual(target.stat().st_ino, target_inode)
        self.assertEqual(restarted.get_work(first["work_id"]), unknown)
        self.assertEqual(restarted.get_work(approved["work_id"]), approved)
        self.assertEqual(restarted.events(approved["work_id"]), before_events)

    def test_writer_lock_fences_cancel_and_reconcile_during_file_effect(self):
        entered, release = threading.Event(), threading.Event()
        failures = []

        class PausingCore(Core):
            def _replace(inner, work, candidate, *, fail_after_replace):
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("검사 동기화 시간이 초과됐습니다.")
                return super()._replace(work, candidate, fail_after_replace=fail_after_replace)

        applier = PausingCore(self.state_dir)
        approved = self.approved()

        def apply():
            try:
                applier.apply(approved["work_id"], **self.apply_arguments(approved))
            except Exception as exc:
                failures.append(exc)

        worker = threading.Thread(target=apply)
        worker.start()
        try:
            self.assertTrue(entered.wait(5))
            applying = self.core.get_work(approved["work_id"])
            self.assertEqual(applying["state"], "APPLYING")
            self.assert_code("CORE_BUSY", self.core.request_cancel, applying["work_id"], expected_revision=applying["revision"])
            self.assert_code("CORE_BUSY", self.core.reconcile, applying["work_id"])
        finally:
            release.set()
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(self.core.get_work(approved["work_id"])["state"], "APPLIED")
        self.assertEqual(self.target.read_bytes(), CANDIDATE)


if __name__ == "__main__":
    unittest.main()
