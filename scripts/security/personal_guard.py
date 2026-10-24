#!/usr/bin/env python3
"""개인 프로젝트의 문서 반입·외부 전송을 로컬에서 검사한다."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import urllib.request
from urllib.parse import urlparse

VERSION = 1
MAX_FILE = 5 * 1024 * 1024
MAX_COMMITS = 500
MAX_BYTES = 100 * 1024 * 1024
RUNTIME = Path.home() / ".config/personal-project-guard"
TEXT_SUFFIXES = set(".md .txt .json .jsonl .html .htm .css .scss .js .mjs .cjs .jsx .ts .tsx .py .sh .bash .zsh .ps1 .yml .yaml .toml .sql .xml .csv .svg .ini .cfg .conf .gitignore .gitattributes .rules .lock .ipynb .c .h .go .rs".split())
PATTERNS = [
    ("개인키", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub 자격", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("API 자격", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b|\bAIza[A-Za-z0-9_-]{30,}\b")),
    ("AWS 자격", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b")),
    ("URL 자격", re.compile(r"https?://[^\s/@:]+:[^\s/@]{8,}@")),
]
ASSIGNMENT = re.compile(r'''(?im)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret)\s*[=:]\s*["']([A-Za-z0-9_./+=-]{12,})["']''')


class Blocked(Exception):
    """사용자 정보 원문 없이 차단 사유만 전달한다."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv, cwd=None, data=None, env=None):
    try:
        result = subprocess.run(argv, cwd=cwd, input=data, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=25, env=env)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Blocked("검사 명령을 실행하지 못했습니다.") from error
    if result.returncode:
        raise Blocked("검사 명령이 실패했습니다. 실패를 통과로 처리하지 않습니다.")
    return result.stdout


def load_policy():
    try:
        policy = json.loads((RUNTIME / "local-policy.json").read_text())
        if policy["version"] != VERSION or not policy["repositories"]:
            raise ValueError()
        if policy["runtime_sha256"] != digest((RUNTIME / "guard.py").read_bytes()):
            raise Blocked("설치 검사기 버전이 달라졌습니다. 승인 후 재설치하세요.")
        return policy
    except (OSError, ValueError, KeyError) as error:
        raise Blocked("개인 보호 설정이 없거나 올바르지 않습니다.") from error


def repository(policy, cwd):
    target = Path(cwd).resolve()
    for entry in policy["repositories"]:
        for root in entry["roots"]:
            if target == Path(root) or Path(root) in target.parents:
                return entry, Path(root)
    return None, None


def check_session(policy, env=None):
    env = os.environ if env is None else env
    if env.get("CLAUDE_AUTO_ACCOUNT_SELECTED"):
        raise Blocked("이 프로젝트는 개인 Codex 전용입니다.")
    if env.get("CODEX_AUTO_ACCOUNT_SELECTED") != "personal":
        raise Blocked("개인 Codex 실행 여부를 확인할 수 없습니다.")
    if env.get("FORGE_GLOW_CODEX_ACCOUNT", "personal") != "personal":
        raise Blocked("계정 표시가 개인 Codex와 일치하지 않습니다.")
    personal = Path(policy["personal_profile"]).resolve()
    if Path(env.get("CODEX_HOME", str(Path.home() / ".codex"))).resolve() != personal:
        raise Blocked("승인된 개인 프로필이 아닙니다.")
    # 회사 인증 파일은 열지 않는다. 개인 계정 ID의 해시만 비교한다.
    try:
        auth = json.loads((personal / "auth.json").read_text())
        account = auth["tokens"]["account_id"]
        if not account or digest(account.encode()) != policy["personal_account_sha256"]:
            raise Blocked("개인 프로필의 계정이 승인 당시와 달라졌습니다.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Blocked("개인 프로필의 계정을 확인하지 못했습니다.") from error


def skill_sync_mappings(policy, entry, root):
    """Return validated source/destination pairs for the narrow CodeForge exception."""
    config = policy.get("skill_sync_exception")
    if not isinstance(config, dict) or config.get("enabled") is not True:
        return []
    if config.get("repository") != entry.get("id"):
        return []
    raw_mappings = config.get("mappings")
    if not isinstance(raw_mappings, list) or not raw_mappings:
        raise Blocked("스킬 동기화 예외 설정이 올바르지 않습니다.")
    mappings = []
    resolved_root = root.resolve()
    for raw in raw_mappings:
        if not isinstance(raw, dict):
            raise Blocked("스킬 동기화 예외 설정이 올바르지 않습니다.")
        source_value = raw.get("source")
        destination_value = raw.get("destination")
        if not isinstance(source_value, str) or not isinstance(destination_value, str):
            raise Blocked("스킬 동기화 예외 설정이 올바르지 않습니다.")
        source_path = Path(source_value).expanduser()
        destination_path = Path(destination_value)
        if not source_path.is_absolute() or destination_path.is_absolute() or ".." in destination_path.parts:
            raise Blocked("스킬 동기화 예외 경로가 올바르지 않습니다.")
        source = source_path.resolve()
        destination = (resolved_root / destination_path).resolve()
        if not destination.is_relative_to(resolved_root):
            raise Blocked("스킬 동기화 목적지가 저장소 밖입니다.")
        mappings.append((source, destination))
    return mappings


def session_mode(policy, entry, root, env=None):
    """Keep normal account verification, with one policy-declared path exception."""
    env = os.environ if env is None else env
    try:
        check_session(policy, env)
        return "personal"
    except Blocked:
        if env.get("CLAUDE_AUTO_ACCOUNT_SELECTED"):
            raise
        if not env.get("CODEX_HOME") or not skill_sync_mappings(policy, entry, root):
            raise
        return "skill-sync"


def path_in(path, roots):
    resolved = path.resolve()
    return any(resolved == allowed or resolved.is_relative_to(allowed) for allowed in roots)


def payload_path(value, root):
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def check_skill_sync_tool(payload, root, entry, policy):
    """Allow only the two user-owned skill trees while account identity is unverified."""
    mappings = skill_sync_mappings(policy, entry, root)
    sources = [source for source, _ in mappings]
    destinations = [destination for _, destination in mappings]
    allowed = sources + destinations
    tool = payload.get("tool_name", "")
    values = payload.get("tool_input", {})
    if not isinstance(values, dict):
        raise Blocked("스킬 동기화 도구 입력을 확인하지 못했습니다.")

    if tool in {"Read", "Glob", "Grep"}:
        paths = [values[key] for key in ("path", "file_path", "cwd", "workdir")
                 if isinstance(values.get(key), str)]
        if not paths or any(not path_in(payload_path(path, root), allowed) for path in paths):
            raise Blocked("스킬 동기화 예외에서는 승인된 두 스킬만 읽을 수 있습니다.")
        return

    if tool in {"Edit", "Write"}:
        paths = [values[key] for key in ("path", "file_path")
                 if isinstance(values.get(key), str)]
        if not paths or any(not path_in(payload_path(path, root), destinations) for path in paths):
            raise Blocked("스킬 동기화 예외에서는 두 대상 디렉터리만 편집할 수 있습니다.")
        return

    if tool == "apply_patch":
        patch_text = values.get("patch", values.get("input", ""))
        if not isinstance(patch_text, str):
            raise Blocked("스킬 동기화 패치 형식을 확인하지 못했습니다.")
        names = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", patch_text, re.M)
        if not names or any(not path_in(payload_path(name, root), destinations) for name in names):
            raise Blocked("스킬 동기화 예외에서는 두 대상 디렉터리만 패치할 수 있습니다.")
        return

    if tool not in {"Bash", "exec_command"}:
        raise Blocked("스킬 동기화 예외에서 허용되지 않은 도구입니다.")
    command = values.get("cmd", values.get("command", ""))
    if not isinstance(command, str) or re.search(r"[\n\r;|&<>`]", command) or "$(" in command:
        raise Blocked("스킬 동기화 예외에서는 단일 로컬 명령만 실행할 수 있습니다.")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise Blocked("스킬 동기화 명령을 해석하지 못했습니다.") from error
    if not tokens:
        raise Blocked("스킬 동기화 명령이 비어 있습니다.")

    def checked_path(value, roots):
        candidate = payload_path(value, root)
        if not path_in(candidate, roots):
            raise Blocked("스킬 동기화 명령의 경로가 승인 범위를 벗어납니다.")
        return candidate

    program = Path(tokens[0]).name
    if program == "pwd" and len(tokens) == 1:
        return
    if program == "mkdir" and len(tokens) >= 3 and tokens[1] == "-p":
        for value in tokens[2:]:
            checked_path(value, destinations)
        return
    if program == "cp":
        args = tokens[1:]
        while args and args[0] in {"-R", "-r", "-p", "-Rp", "-pR", "-rp", "-pr"}:
            args = args[1:]
        if len(args) != 2:
            raise Blocked("스킬 동기화 복사는 소스와 목적지 하나씩만 허용합니다.")
        source = checked_path(args[0], sources)
        destination = checked_path(args[1], destinations)
        if not any(path_in(source, [source_root]) and path_in(destination, [destination_root])
                   for source_root, destination_root in mappings):
            raise Blocked("스킬 소스와 목적지의 대응이 올바르지 않습니다.")
        return
    if program in {"cmp", "diff"}:
        args = [value for value in tokens[1:] if not value.startswith("-")]
        if len(args) != 2:
            raise Blocked("스킬 비교 명령은 두 경로만 허용합니다.")
        first = checked_path(args[0], allowed)
        second = checked_path(args[1], allowed)
        if not any((path_in(first, [source]) and path_in(second, [destination]))
                   or (path_in(second, [source]) and path_in(first, [destination]))
                   for source, destination in mappings):
            raise Blocked("승인된 소스와 목적지 사이의 비교만 허용합니다.")
        return
    if program in {"python3", "python"}:
        args = tokens[1:]
        if args[:1] == ["-B"]:
            args = args[1:]
        if not args or args[0] in {"-c", "-m", "-"}:
            raise Blocked("승인된 스킬 검사 스크립트만 실행할 수 있습니다.")
        checked_path(args[0], allowed)
        for value in args[1:]:
            if value.startswith("-"):
                continue
            checked_path(value, allowed)
        return
    if program == "git" and len(tokens) >= 4 and tokens[1] in {"status", "diff"} and "--" in tokens:
        separator = tokens.index("--")
        if separator == len(tokens) - 1:
            raise Blocked("Git 조회 범위를 두 스킬 디렉터리로 지정하세요.")
        allowed_git_options = {
            "status": {"--short", "--porcelain", "--branch", "-s", "-b"},
            "diff": {"--check", "--stat", "--name-only", "--name-status", "--no-ext-diff"},
        }
        if any(value not in allowed_git_options[tokens[1]] for value in tokens[2:separator]):
            raise Blocked("스킬 동기화 예외에서 허용되지 않은 Git 조회 옵션입니다.")
        for value in tokens[separator + 1:]:
            checked_path(value, destinations)
        return
    raise Blocked("스킬 동기화 예외에서는 복사·비교·검사와 범위가 지정된 Git 조회만 허용합니다.")


def scan(data, filename, deny_patterns=()):
    findings = []
    name = Path(filename).name.lower()
    if name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template"))):
        findings.append({"rule": "환경설정 파일", "line": 0})
    if name in {"auth.json", "credentials", "credentials.json", "contact_db.json", "send_log.json", "id_rsa", "id_ed25519"} or name.endswith((".pem", ".p12", ".pfx", ".key", ".sqlite", ".db", ".dump")):
        findings.append({"rule": "자격·실데이터 파일", "line": 0})
    if len(data) > MAX_FILE:
        return findings + [{"rule": "파일 크기 검사 한도 초과", "line": 0}]
    if b"\x00" in data:
        return findings + [{"rule": "바이너리 별도 검토 필요", "line": 0}]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return findings + [{"rule": "UTF-8 텍스트 아님", "line": 0}]
    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in TEXT_SUFFIXES and not name.endswith((".example", ".sample", ".template")):
        findings.append({"rule": "지원하지 않는 파일 형식", "line": 0})
    if text.startswith("version https://git-lfs.github.com/spec/v1"):
        findings.append({"rule": "LFS 실파일 별도 검토 필요", "line": 1})
    checks = PATTERNS + [("로컬 금지 패턴", re.compile(p)) for p in deny_patterns]
    for rule, pattern in checks:
        for match in pattern.finditer(text):
            findings.append({"rule": rule, "line": text[:match.start()].count("\n") + 1})
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1).lower()
        if not any(word in value for word in ("example", "placeholder", "changeme", "your_", "test_", "dummy", "process.env")):
            findings.append({"rule": "자격 값 직접 대입 검토", "line": text[:match.start()].count("\n") + 1})
    return findings


def check_bytes(data, filename, policy):
    findings = scan(data, filename, policy.get("deny_patterns", []))
    if findings:
        # 발견한 문자열·파일 본문을 출력하지 않는다.
        rules = ", ".join(sorted({item["rule"] for item in findings}))
        raise Blocked("내용 검사 차단: " + rules)


def read_regular(filename):
    path = Path(filename).absolute()
    # macOS의 표준 별칭만 정규화한다. 사용자 링크는 따라가지 않는다.
    for alias, actual in (("/tmp/", "/private/tmp/"), ("/var/", "/private/var/")):
        if str(path).startswith(alias):
            path = Path(actual + str(path)[len(alias):])
    # 사용자가 직접 지정한 문서만 검사하며 링크를 따라 읽지 않는다.
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise Blocked("일반 파일만 지정할 수 있습니다. 링크와 디렉터리는 허용하지 않습니다.")
    if path.stat().st_size > MAX_FILE:
        raise Blocked("파일 크기 검사 한도를 넘었습니다.")
    return path.read_bytes()


def receipt_path(entry, content_hash):
    return RUNTIME / "receipts" / entry["id"] / (content_hash + ".json")


def check_import_receipt(entry, name, data):
    if not name.startswith("docs/imported/"):
        return
    try:
        receipt = json.loads(receipt_path(entry, digest(data)).read_text())
        if receipt["sha256"] != digest(data) or receipt["destination"] != name or receipt["repository"] != entry["id"]:
            raise ValueError()
        if receipt["rights_confirmed"] is not True:
            raise ValueError()
    except (OSError, ValueError, KeyError) as error:
        raise Blocked("반입 문서의 내용·목적지와 일치하는 권한 확인 기록이 없습니다.") from error


def inspect_document(filename, policy):
    data = read_regular(filename)
    check_bytes(data, Path(filename).name, policy)
    return {"status": "자동 검사 통과·권한 확인 필요", "sha256": digest(data), "bytes": len(data)}


def admit_document(args, policy, entry, root):
    if Path(args.file).suffix.lower() not in {".md", ".txt"}:
        raise Blocked("반입 문서는 첫 버전에서 Markdown·텍스트만 지원합니다.")
    data = read_regular(args.file)
    check_bytes(data, Path(args.file).name, policy)
    if digest(data) != args.approved_sha:
        raise Blocked("승인한 내용과 현재 파일이 달라졌습니다. 다시 검사하세요.")
    if not args.rights_confirmed or len(args.rights_note.strip()) < 12:
        raise Blocked("공개 이용 또는 독립 작성·사용 권한 확인 근거를 기록하세요.")
    rel = Path(args.destination)
    if rel.is_absolute() or ".." in rel.parts or not rel.as_posix().startswith("docs/imported/"):
        raise Blocked("목적지는 이 저장소의 docs/imported 아래로 지정하세요.")
    if rel.suffix.lower() not in {".md", ".txt"}:
        raise Blocked("반입 목적지 형식이 올바르지 않습니다.")
    destination = root / rel
    if not destination.resolve().is_relative_to(root.resolve()):
        raise Blocked("반입 목적지가 저장소 밖입니다.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # x 모드로 기존 문서·링크를 덮어쓰지 않는다.
    with destination.open("xb") as output:
        output.write(data)
    receipt = {"repository": entry["id"], "destination": rel.as_posix(), "sha256": digest(data),
               "rights_confirmed": True, "source_kind": args.source_kind,
               "rights_note": args.rights_note, "scanner_version": VERSION}
    record = receipt_path(entry, digest(data))
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    record.chmod(0o600)
    return {"status": "반입 완료", "destination": rel.as_posix(), "sha256": digest(data)}


def git(root, *args):
    return run(["git", "-C", str(root), *args])


def check_tree_paths(root, revision, paths, policy, entry):
    seen = set()
    total = 0
    for name in paths:
        raw = git(root, "ls-tree", "-z", revision, "--", name)
        if not raw:
            continue  # 삭제된 파일이다. 앞선 커밋에 들어간 내용은 별도로 검사한다.
        for record in raw.rstrip(b"\0").split(b"\0"):
            header, filename = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            label = filename.decode("utf-8", "strict")
            if kind != "blob" or mode == "120000":
                raise Blocked("링크·submodule 전송은 별도 검증이 필요합니다.")
            if (oid, label) in seen:
                continue
            seen.add((oid, label))
            size = int(git(root, "cat-file", "-s", oid))
            if size > MAX_FILE or total + size > MAX_BYTES:
                raise Blocked("전송 내용의 검사 용량을 넘었습니다.")
            data = git(root, "cat-file", "blob", oid)
            total += len(data)
            try:
                check_bytes(data, label, policy)
                check_import_receipt(entry, label, data)
            except Blocked as error:
                # 파일명도 민감할 수 있어 본문과 함께 출력하지 않는다.
                raise Blocked(str(error) + " (파일명 해시 " + digest(filename)[:12] + ")") from error
    return len(seen)


def check_repository_scope(root, entry, mode, reference=None, paths=None):
    # 계정·자료 출처 검사는 기존 보호 절차가 담당한다. 이 검사는 저장소의 작업 종류를 제한한다.
    if entry["remote"] != "https://github.com/ggombee/kkombee.git":
        return
    script = root / "scripts/check-project-scope.py"
    if not script.is_file() or script.is_symlink():
        raise Blocked("작업 범위 검사기가 없거나 올바르지 않아 중단합니다.")
    command = [sys.executable, "-B", str(script), mode]
    if reference is not None:
        command.append(reference)
    command.extend(["--root", str(root)])
    data = json.dumps(paths, ensure_ascii=False).encode() if paths is not None else None
    try:
        run(command, cwd=root, data=data)
    except Blocked as error:
        raise Blocked("작업 범위 검사 차단: 이력서·면접·연봉협상 자료는 resume-editor에서 관리합니다. 검사 오류도 통과로 처리하지 않습니다.") from error


def check_staged(root, policy, entry):
    check_repository_scope(root, entry, "index")
    paths = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split(b"\0")
    count = 0
    for raw in filter(None, paths):
        name = raw.decode()
        entry_raw = git(root, "ls-files", "--stage", "-z", "--", name)
        if not entry_raw.startswith((b"100644 ", b"100755 ")):
            raise Blocked("일반 파일만 자동 검사할 수 있습니다.")
        data = git(root, "show", ":" + name)
        check_bytes(data, name, policy)
        check_import_receipt(entry, name, data)
        count += 1
    return {"status": "staged 검사 통과", "files": count}


def check_github_identity(policy, entry, root):
    url = urlparse(entry["remote"])
    if url.scheme != "https" or url.hostname != "github.com" or url.username or url.password:
        raise Blocked("첫 버전의 인증 검증은 승인된 GitHub HTTPS만 지원합니다.")
    # 추가 Authorization 헤더가 credential 경로를 덮어쓰면 인증 주체가 달라질 수 있다.
    names = subprocess.run(["git", "-C", str(root), "config", "--name-only", "--get-regexp", r"^http.*\.extraheader$"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if names.returncode not in (0, 1):
        raise Blocked("Git 인증 설정을 검사하지 못했습니다.")
    if names.stdout.strip() or os.environ.get("GIT_CONFIG_COUNT"):
        raise Blocked("추가 HTTP 인증 설정은 별도 검증이 필요합니다.")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    credential = run(["git", "credential", "fill"], cwd=root, env=env,
                     data=("protocol=https\nhost=github.com\npath=" + url.path.lstrip("/") + "\n\n").encode())
    fields = dict(line.split("=", 1) for line in credential.decode().splitlines() if "=" in line)
    token = fields.get("password")
    if not token:
        raise Blocked("GitHub 전송용 자격정보를 확인하지 못했습니다.")
    request = urllib.request.Request("https://api.github.com/user", headers={
        "Authorization": "Bearer " + token, "User-Agent": "personal-project-local-guard",
        "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            login = json.load(response).get("login")
    except Exception as error:
        raise Blocked("GitHub 실제 인증 계정을 확인하지 못해 전송을 중단합니다.") from error
    if login != policy["github_login"]:
        raise Blocked("GitHub 인증 계정이 승인된 개인 계정과 다릅니다.")


def push_ranges(root, records, policy, entry):
    count = 0
    for line in records.splitlines():
        values = line.split()
        if len(values) != 4:
            raise Blocked("Git 전송 범위를 해석하지 못했습니다.")
        local_ref, local_oid, remote_ref, remote_oid = values
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", local_oid) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", remote_oid):
            raise Blocked("Git 객체 ID 형식이 올바르지 않습니다.")
        if set(local_oid) == {"0"} or remote_ref not in entry["allowed_refs"]:
            raise Blocked("승인되지 않은 ref·삭제·태그 전송입니다.")
        if git(root, "cat-file", "-t", local_oid).strip() != b"commit":
            raise Blocked("브랜치 커밋만 자동 검사할 수 있습니다.")
        revisions = [local_oid]
        if set(remote_oid) != {"0"}:
            git(root, "cat-file", "-e", remote_oid + "^{commit}")
            revisions.append("^" + remote_oid)
        else:
            base_oid = entry.get("new_branch_bases", {}).get(remote_ref)
            if not isinstance(base_oid, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base_oid) or set(base_oid) == {"0"}:
                raise Blocked("새 브랜치의 승인 기준 커밋이 없습니다.")
            git(root, "cat-file", "-e", base_oid + "^{commit}")
            try:
                git(root, "merge-base", "--is-ancestor", base_oid, local_oid)
            except Blocked as error:
                raise Blocked("새 브랜치가 승인된 기준 커밋에서 이어지지 않습니다.") from error
            revisions.append("^" + base_oid)
        commits = git(root, "rev-list", *revisions, "--").decode().splitlines()
        if len(commits) > MAX_COMMITS:
            raise Blocked("커밋 검사 한도를 넘었습니다. 기준 이력 검토가 필요합니다.")
        for commit in commits:
            check_repository_scope(root, entry, "tree", reference=commit)
            metadata = git(root, "show", "-s", "--format=%B%n%an%n%ae", commit)
            check_bytes(metadata, "commit.txt", policy)
            names = git(root, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-m", "-z", commit)
            paths = [name.decode() for name in names.split(b"\0") if name]
            count += check_tree_paths(root, commit, paths, policy, entry)
    return {"status": "전송 전 내용 검사 통과", "objects_checked": count}


def block_hook(reason, event):
    print("개인 프로젝트 보호: " + reason, file=sys.stderr)
    if event == "SessionStart":
        print(json.dumps({"continue": False, "stopReason": reason}, ensure_ascii=False))
    else:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}, ensure_ascii=False))
    return 2


def check_tool(payload, root, entry):
    tool_name = payload.get("tool_name", "")
    tool_values = payload.get("tool_input", {})
    edit_paths = []
    if tool_name in {"Edit", "Write"}:
        edit_paths = [tool_values[key] for key in ("path", "file_path")
                      if isinstance(tool_values.get(key), str)]
    if tool_name == "apply_patch":
        patch_text = tool_values.get("patch", tool_values.get("input", ""))
        if isinstance(patch_text, str):
            edit_paths += re.findall(r"^\*\*\* (?:Add File|Update File|Move to): (.+)$", patch_text, re.M)
    if edit_paths:
        relative_paths = []
        for path in edit_paths:
            resolved = (root / Path(path).expanduser()).resolve()
            try:
                relative_paths.append(str(resolved.relative_to(root.resolve())))
            except ValueError as error:
                raise Blocked("허용된 개인 저장소 밖의 파일 편집입니다.") from error
        check_repository_scope(root, entry, "paths", paths=relative_paths)
    values = payload.get("tool_input", {})
    tool = payload.get("tool_name", "")
    # 구조화된 경로를 검사한다. 임의 프로그램 내부 동작을 해석하는 샌드박스는 아니다.
    for key in ("path", "file_path", "cwd", "workdir", "target_path"):
        value = values.get(key)
        if isinstance(value, str):
            candidate = Path(value).expanduser()
            resolved = (root / candidate).resolve()
            if not any(resolved.is_relative_to(Path(p)) for p in entry["roots"]):
                raise Blocked("허용된 개인 저장소 밖 경로입니다.")
    patch_text = values.get("patch", values.get("input", ""))
    if tool in {"apply_patch", "Edit", "Write"} and isinstance(patch_text, str):
        for name in re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", patch_text, re.M):
            resolved = (root / name).resolve()
            if not any(resolved.is_relative_to(Path(p)) for p in entry["roots"]):
                raise Blocked("허용된 저장소 밖의 파일 편집입니다.")
    command = values.get("cmd", values.get("command", ""))
    if not isinstance(command, str):
        raise Blocked("도구 명령 형식을 검사하지 못했습니다.")
    tokens = shlex.split(command, posix=True)
    # 지정 문서는 검사기만 읽는다. 해당 명령을 다른 쉘 명령과 합칠 수 없다.
    guarded = len(tokens) >= 3 and tokens[0] in {"python3", "/usr/bin/python3"} and tokens[1] == str(RUNTIME / "guard.py")
    intake = guarded and len(tokens) >= 4 and tokens[2] in {"inspect", "admit"}
    status = guarded and len(tokens) == 3 and tokens[2] in {"doctor", "staged"}
    if (intake or status) and not re.search(r"[\n;|&<>`]|\$\(", command):
        return
    if re.search(r"--no-verify|core\.hooksPath\s*=|GIT_CONFIG_COUNT\s*=", command):
        raise Blocked("보호 훅 우회 명령은 허용하지 않습니다.")
    if re.search(r"\b(?:curl|wget|scp|sftp|rsync|ftp)\b|\bgh\s+(?:api|release|gist|pr\s+(?:create|edit)|issue\s+(?:create|edit))\b|\b(?:npm|pnpm)\s+publish\b", command):
        raise Blocked("직접 외부 전송은 자동 허용하지 않습니다. 전송 내용을 먼저 검토하세요.")
    if tool.startswith("mcp__") and "herdr" not in tool:
        raise Blocked("이 프로젝트의 외부 연결 도구는 별도 승인이 필요합니다.")
    for token in tokens:
        if token.startswith(("/Users/", "~/", "../")):
            candidate = Path(token).expanduser()
            candidate = (root / candidate).resolve()
            if not any(candidate.is_relative_to(Path(p)) for p in entry["roots"]):
                raise Blocked("명령에 허용 범위 밖 개인·업무 경로가 있습니다.")


def main():
    parser = argparse.ArgumentParser(description="개인 프로젝트의 로컬 반입·전송 검사")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("codex-hook")
    forward = commands.add_parser("forward-hook")
    forward.add_argument("command", nargs=argparse.REMAINDER)
    push = commands.add_parser("pre-push")
    push.add_argument("remote_name")
    push.add_argument("remote_url")
    dispatch = commands.add_parser("git-dispatch")
    dispatch.add_argument("git_event", choices=["pre-push", "pre-commit"])
    dispatch.add_argument("git_args", nargs=argparse.REMAINDER)
    commands.add_parser("staged")
    commands.add_parser("doctor")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("file")
    admit = commands.add_parser("admit")
    admit.add_argument("file")
    admit.add_argument("--destination", required=True)
    admit.add_argument("--approved-sha", required=True)
    admit.add_argument("--source-kind", choices=["public", "personal-summary"], required=True)
    admit.add_argument("--rights-confirmed", action="store_true")
    admit.add_argument("--rights-note", required=True)
    args = parser.parse_args()
    policy = load_policy()
    hook_data = sys.stdin.buffer.read() if args.action in {"codex-hook", "forward-hook"} else None
    payload = json.loads(hook_data or b"{}") if hook_data is not None else {}
    cwd = payload.get("cwd", os.getcwd())
    entry, root = repository(policy, cwd)
    if args.action == "git-dispatch":
        if not entry:
            if args.git_event == "pre-push" and any(url == item["remote"] for url in args.git_args for item in policy["repositories"]):
                raise Blocked("등록되지 않은 작업 경로에서 보호 저장소로 전송할 수 없습니다.")
            legacy = policy.get("legacy_" + args.git_event.replace("-", "_"))
            if legacy:
                return subprocess.run([legacy, *args.git_args], input=sys.stdin.buffer.read(), timeout=60).returncode
            return 0
        check_session(policy)
        if args.git_event == "pre-commit":
            print(json.dumps(check_staged(root, policy, entry), ensure_ascii=False))
            return 0
        if len(args.git_args) != 2 or args.git_args[1] != entry["remote"]:
            raise Blocked("승인된 원격 목적지와 다릅니다.")
        records = sys.stdin.read()
        if records.strip():
            check_github_identity(policy, entry, root)
            print(json.dumps(push_ranges(root, records, policy, entry), ensure_ascii=False))
        return 0
    if args.action == "forward-hook":
        if entry:
            session_mode(policy, entry, root)
            return 0  # 대상 개인 프로젝트에서는 회사 연동·자동 계정 전환 훅을 호출하지 않는다.
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            raise Blocked("기존 훅 명령이 없습니다.")
        result = subprocess.run(command, input=hook_data, timeout=45)
        return result.returncode
    if args.action == "codex-hook":
        if not entry:
            return 0
        event = payload.get("hook_event_name", "PreToolUse")
        try:
            mode = session_mode(policy, entry, root)
            if event == "PreToolUse":
                if mode == "skill-sync":
                    check_skill_sync_tool(payload, root, entry, policy)
                else:
                    check_tool(payload, root, entry)
            if event == "SessionStart":
                if mode == "skill-sync":
                    context = "계정을 확인하지 못해 CodeForge의 handoff와 polish-korean 동기화만 허용합니다. 두 스킬 외의 파일 편집, 회사 연동, 네트워크 전송, 커밋과 푸시는 차단됩니다."
                else:
                    context = "개인 Codex 전용 프로젝트입니다. 회사 폴더·메모리·연동을 사용하지 않습니다. docs/personal-project-security.md를 따르고 외부 문서는 inspect 후 사용 권한 확인과 admit 절차로 반입합니다."
                print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}, ensure_ascii=False))
            return 0
        except Blocked as error:
            return block_hook(str(error), event)
    if not entry:
        raise Blocked("승인된 개인 저장소 안에서 실행하세요.")
    check_session(policy)
    if args.action == "doctor":
        result = {"status": "개인 프로필·설정 확인", "repository": entry["id"], "scope": "규칙·전송 검사이며 OS 읽기 격리는 아님"}
    elif args.action == "inspect":
        result = inspect_document(args.file, policy)
    elif args.action == "admit":
        result = admit_document(args, policy, entry, root)
    elif args.action == "staged":
        result = check_staged(root, policy, entry)
    else:
        if args.remote_url != entry["remote"]:
            raise Blocked("승인된 원격 목적지와 다릅니다.")
        records = sys.stdin.read()
        if not records.strip():
            return 0
        check_github_identity(policy, entry, root)
        result = push_ranges(root, records, policy, entry)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Blocked, OSError, ValueError, KeyError, UnicodeError) as error:
        message = str(error) if isinstance(error, Blocked) else "검사 자체에 오류가 발생해 중단했습니다."
        print("개인 프로젝트 보호: " + message, file=sys.stderr)
        sys.exit(2)
