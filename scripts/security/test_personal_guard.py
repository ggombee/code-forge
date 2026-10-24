"""실제 자격·업무 자료 없이 차단 동작과 Git 이력 검사를 검증한다."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("guard", Path(__file__).with_name("personal_guard.py"))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="personal-guard-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entry = {"id": "sample", "roots": [str(self.root)], "allowed_refs": ["refs/heads/review"], "remote": "https://github.com/example/sample.git"}
        self.policy = {"deny_patterns": ["INTERNAL_" + "ONLY"], "repositories": [self.entry]}

    def skill_sync_policy(self):
        source = self.root.parent / (self.root.name + "-source")
        source.mkdir()
        self.addCleanup(lambda: source.rmdir() if source.exists() and not any(source.iterdir()) else None)
        return dict(self.policy, skill_sync_exception={
            "enabled": True,
            "repository": "sample",
            "mappings": [{"source": str(source), "destination": "skills/handoff"}],
        }), source

    def test_safe_and_opaque_content(self):
        self.assertEqual(guard.scan("공개 자료를 참고한 개인 기획".encode(), "note.md"), [])
        self.assertTrue(guard.scan(b"\x00abc", "image.png"))
        self.assertTrue(guard.scan(b"data", "archive.zip"))

    def test_redacted_secret_error(self):
        secret = "ghp" + "_" + "A" * 36
        with self.assertRaises(guard.Blocked) as caught:
            guard.check_bytes(secret.encode(), "view.html", self.policy)
        self.assertNotIn(secret, str(caught.exception))

    def test_forbidden_filename_and_local_pattern(self):
        self.assertTrue(guard.scan(b"plain", ".env.local"))
        self.assertTrue(guard.scan(b"plain", "credentials.json"))
        self.assertEqual(guard.scan(b"plain", ".env.example"), [])
        with self.assertRaises(guard.Blocked):
            guard.check_bytes(b"INTERNAL_ONLY", "note.md", self.policy)

    def test_unknown_or_company_session_denied(self):
        policy = dict(self.policy, personal_profile=str(self.root), personal_account_sha256=guard.digest(b"personal-account"))
        (self.root / "auth.json").write_text(json.dumps({"tokens": {"account_id": "personal-account"}}))
        env = {"CODEX_HOME": str(self.root), "CODEX_AUTO_ACCOUNT_SELECTED": "personal"}
        guard.check_session(policy, env)
        for wrong in ({}, dict(env, CODEX_AUTO_ACCOUNT_SELECTED="company"), dict(env, CLAUDE_AUTO_ACCOUNT_SELECTED="team"), dict(env, CODEX_HOME=str(self.root / "other"))):
            with self.assertRaises(guard.Blocked):
                guard.check_session(policy, wrong)

    def test_skill_sync_exception_is_path_scoped_and_never_allows_publish(self):
        policy, source = self.skill_sync_policy()
        company_env = {"CODEX_HOME": str(self.root / "company"), "CODEX_AUTO_ACCOUNT_SELECTED": "company"}
        self.assertEqual(guard.session_mode(policy, self.entry, self.root, company_env), "skill-sync")
        with self.assertRaises(guard.Blocked):
            guard.session_mode(policy, self.entry, self.root, dict(company_env, CLAUDE_AUTO_ACCOUNT_SELECTED="team"))

        destination = self.root / "skills/handoff"
        guard.check_skill_sync_tool({"tool_name": "Read", "tool_input": {"file_path": str(source / "SKILL.md")}}, self.root, self.entry, policy)
        guard.check_skill_sync_tool({"tool_name": "apply_patch", "tool_input": {"input": "*** Add File: skills/handoff/SKILL.md\n"}}, self.root, self.entry, policy)
        guard.check_skill_sync_tool({"tool_name": "Bash", "tool_input": {"command": f"cp -R {source} {destination}"}}, self.root, self.entry, policy)

        denied = [
            {"tool_name": "Write", "tool_input": {"file_path": str(self.root / "bin/forge")}},
            {"tool_name": "Read", "tool_input": {"file_path": "/Users/someone/private.txt"}},
            {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
            {"tool_name": "Bash", "tool_input": {"command": "git diff --output=/tmp/leak -- skills/handoff"}},
            {"tool_name": "Bash", "tool_input": {"command": "curl https://example.invalid"}},
        ]
        for payload in denied:
            with self.assertRaises(guard.Blocked):
                guard.check_skill_sync_tool(payload, self.root, self.entry, policy)

        other_entry = dict(self.entry, id="other")
        with self.assertRaises(guard.Blocked):
            guard.session_mode(policy, other_entry, self.root, company_env)

    def test_document_hash_and_rights_before_copy(self):
        source = self.root / "user-note.md"
        source.write_text("독립 작성한 개인 요구사항", encoding="utf8")
        result = guard.inspect_document(source, self.policy)
        args = argparse.Namespace(file=str(source), destination="docs/imported/note.md", approved_sha=result["sha256"], rights_confirmed=False, rights_note="공개 근거와 독립 작성 내용을 직접 확인함", source_kind="personal-summary")
        with self.assertRaises(guard.Blocked):
            guard.admit_document(args, self.policy, self.entry, self.root)
        args.rights_confirmed = True
        with patch.object(guard, "RUNTIME", self.root / "private-state"):
            guard.admit_document(args, self.policy, self.entry, self.root)
            guard.check_import_receipt(self.entry, args.destination, source.read_bytes())
            with self.assertRaises(guard.Blocked):
                guard.check_import_receipt(self.entry, args.destination, b"changed")
        args.approved_sha = "0" * 64
        args.destination = "docs/imported/changed.md"
        with self.assertRaises(guard.Blocked):
            guard.admit_document(args, self.policy, self.entry, self.root)

    def test_symlink_and_escaped_destination(self):
        source = self.root / "source.md"
        source.write_text("공개 내용")
        link = self.root / "linked.md"
        link.symlink_to(source)
        with self.assertRaises(guard.Blocked):
            guard.inspect_document(link, self.policy)
        args = argparse.Namespace(file=str(source), destination="docs/imported/../../../escape.md", approved_sha=guard.digest(source.read_bytes()), rights_confirmed=True, rights_note="공개 근거와 독립 작성 내용을 직접 확인함", source_kind="public")
        with self.assertRaises(guard.Blocked):
            guard.admit_document(args, self.policy, self.entry, self.root)

    def setup_git(self):
        def call(*args):
            return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-C", str(self.root), *args], stderr=subprocess.DEVNULL).decode().strip()
        call("init", "-q")
        call("config", "user.name", "샘플")
        call("config", "user.email", "sample@example.invalid")
        return call

    def test_intermediate_deleted_secret_is_blocked(self):
        git = self.setup_git()
        file = self.root / "note.md"
        file.write_text("공개 기획")
        git("add", "note.md"); git("commit", "-qm", "기준")
        base = git("rev-parse", "HEAD")
        file.write_text("ghp" + "_" + "B" * 36)
        git("add", "note.md"); git("commit", "-qm", "중간 변경")
        file.write_text("공개 기획 수정")
        git("add", "note.md"); git("commit", "-qm", "최종 변경")
        head = git("rev-parse", "HEAD")
        record = f"refs/heads/local {head} refs/heads/review {base}\n"
        with self.assertRaises(guard.Blocked):
            guard.push_ranges(self.root, record, self.policy, self.entry)

    def test_safe_range_and_unapproved_ref(self):
        git = self.setup_git()
        (self.root / "legacy.bin").write_text("이미 원격에서 검토된 기준 파일")
        git("add", "legacy.bin"); git("commit", "-qm", "기준")
        base = git("rev-parse", "HEAD")
        (self.root / "note.md").write_text("합성 공개 기획")
        git("add", "note.md"); git("commit", "-qm", "기획")
        head = git("rev-parse", "HEAD")
        record = f"refs/heads/local {head} refs/heads/review {'0' * 40}\n"
        with self.assertRaises(guard.Blocked):
            guard.push_ranges(self.root, record, self.policy, self.entry)
        entry = dict(self.entry, new_branch_bases={"refs/heads/review": base})
        self.assertEqual(guard.push_ranges(self.root, record, self.policy, entry)["objects_checked"], 1)
        with self.assertRaises(guard.Blocked):
            guard.push_ranges(self.root, record.replace("refs/heads/review", "refs/tags/new"), self.policy, entry)

    def test_tool_blocks_and_other_repository_is_not_selected(self):
        for command in ("git push --no-verify", "curl https://example.invalid", "cat /Users/someone/private.txt"):
            with self.assertRaises(guard.Blocked):
                guard.check_tool({"tool_name": "exec_command", "tool_input": {"cmd": command}}, self.root, self.entry)
        guard.check_tool({"tool_name": "exec_command", "tool_input": {"cmd": "git diff --stat"}}, self.root, self.entry)
        self.assertEqual(guard.repository(self.policy, "/usr/local"), (None, None))

    def test_approved_inspector_is_only_external_document_reader(self):
        command = f'/usr/bin/python3 {guard.RUNTIME}/guard.py inspect /Users/someone/review-note.md'
        guard.check_tool({"tool_name": "exec_command", "tool_input": {"cmd": command}}, self.root, self.entry)
        with self.assertRaises(guard.Blocked):
            guard.check_tool({"tool_name": "exec_command", "tool_input": {"cmd": command + "; cat /Users/someone/private.md"}}, self.root, self.entry)

    def test_doctor_allowed_and_external_patch_denied(self):
        guard.check_tool({"tool_name": "exec_command", "tool_input": {"cmd": f'/usr/bin/python3 {guard.RUNTIME}/guard.py doctor'}}, self.root, self.entry)
        with self.assertRaises(guard.Blocked):
            guard.check_tool({"tool_name": "apply_patch", "tool_input": {"input": "*** Update File: /Users/someone/private.md\n"}}, self.root, self.entry)

    def test_block_hook_reports_stderr_reason(self):
        stderr = io.StringIO()
        stdout = io.StringIO()
        with patch.object(guard.sys, "stderr", stderr), patch.object(guard.sys, "stdout", stdout):
            self.assertEqual(guard.block_hook("차단 사유", "PreToolUse"), 2)
        self.assertIn("개인 프로젝트 보호: 차단 사유", stderr.getvalue())
        self.assertIn('"permissionDecision": "deny"', stdout.getvalue())

    def test_account_changed_and_missing_receipt_denied(self):
        policy = dict(self.policy, personal_profile=str(self.root), personal_account_sha256=guard.digest(b"expected-personal"))
        (self.root / "auth.json").write_text(json.dumps({"tokens": {"account_id": "different-personal"}}))
        with self.assertRaises(guard.Blocked):
            guard.check_session(policy, {"CODEX_HOME": str(self.root), "CODEX_AUTO_ACCOUNT_SELECTED": "personal"})
        with patch.object(guard, "RUNTIME", self.root / "not-created"):
            with self.assertRaises(guard.Blocked):
                guard.check_import_receipt(self.entry, "docs/imported/note.md", b"safe")

    def test_missing_git_object_and_command_failure_are_not_success(self):
        self.setup_git()
        record = f"refs/heads/local {'1' * 40} refs/heads/review {'0' * 40}\n"
        with self.assertRaises(guard.Blocked):
            guard.push_ranges(self.root, record, self.policy, self.entry)
        with self.assertRaises(guard.Blocked):
            guard.run(['/missing/personal-guard-test-command'])

    def test_actual_github_identity_and_network_failure(self):
        policy = dict(self.policy, github_login="approved-personal")
        credential = b"username=sample\npassword=synthetic-credential-not-real\n"
        with patch.object(guard.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=b'')), patch.object(guard, 'run', return_value=credential):
            with patch.object(guard.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"login":"approved-personal"}')):
                guard.check_github_identity(policy, self.entry, self.root)
            with patch.object(guard.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"login":"different"}')):
                with self.assertRaises(guard.Blocked):
                    guard.check_github_identity(policy, self.entry, self.root)
            with patch.object(guard.urllib.request, 'urlopen', side_effect=OSError('synthetic network failure')):
                with self.assertRaises(guard.Blocked) as caught:
                    guard.check_github_identity(policy, self.entry, self.root)
                self.assertNotIn('synthetic-credential-not-real', str(caught.exception))


if __name__ == "__main__":
    unittest.main()
