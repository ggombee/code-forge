#!/usr/bin/env python3
"""
정책 매트릭스 매칭 + TC 파일 추출

언어/프레임워크 무관. config.json에서 테스트 실행 명령을 읽음.
"""
import json
import glob
import sys
import os


def load_config(policy_dir):
    """프로젝트별 config.json 로드"""
    config_path = os.path.join(policy_dir, "config.json")
    if os.path.exists(config_path):
        return json.load(open(config_path))
    return None


def match_file(policy_dir, changed_file):
    """변경된 파일과 매칭되는 정책 + testFiles 반환"""
    results = []

    for pf in sorted(glob.glob(os.path.join(policy_dir, "*.json"))):
        basename = os.path.basename(pf)
        if "schema" in basename or "config" in basename:
            continue

        d = json.load(open(pf))
        files = d.get("affectedFiles", [])

        matched = any(
            changed_file.endswith(f) or f.endswith(changed_file)
            or f in changed_file or changed_file in f
            for f in files
        )
        if not matched:
            continue

        page = d.get("page", "")
        flows = [f["name"] for f in d.get("flows", [])]
        test_files = d.get("testFiles", [])

        results.append({
            "page": page,
            "flows": flows,
            "testFiles": test_files,
        })

    return results


def get_run_command(config, test_file):
    """config.json 기반으로 테스트 파일 실행 명령 생성"""
    if not config:
        return None

    runner = config.get("testRunner", {})
    basename = os.path.splitext(os.path.basename(test_file))[0]
    # .test.tsx → basename에서 .test 제거
    basename = basename.replace(".test", "").replace(".spec", "")

    # e2e 파일인지 유닛 파일인지 판단
    if "e2e" in test_file or ".spec." in test_file:
        e2e = runner.get("e2e", {})
        template = e2e.get("runSingle", "")
    elif "integration" in test_file:
        integ = runner.get("integration", {})
        template = integ.get("runSingle", "")
    else:
        unit = runner.get("unit", {})
        template = unit.get("runSingle", "")

    if not template:
        return None

    return template.replace("{basename}", basename).replace("{file}", test_file)


def run_all(policy_dir):
    """모든 정책의 testFiles 반환"""
    all_files = set()
    for pf in sorted(glob.glob(os.path.join(policy_dir, "*.json"))):
        basename = os.path.basename(pf)
        if "schema" in basename or "config" in basename:
            continue
        d = json.load(open(pf))
        all_files.update(d.get("testFiles", []))
    return sorted(all_files)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    policy_dir = os.environ.get("POLICY_DIR", "")

    if not policy_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        policy_dir = os.path.join(script_dir, "..", ".policy")

    config = load_config(policy_dir)

    if mode == "--run-all":
        files = run_all(policy_dir)
        for f in files:
            cmd = get_run_command(config, f)
            print(f"FILE={f}")
            if cmd:
                print(f"CMD={cmd}")
    elif mode == "--match":
        changed = sys.argv[2] if len(sys.argv) > 2 else ""
        # 상대 경로 정규화 (프로젝트별 prefix 제거)
        for prefix in ["apps/ad-web/", "src/main/java/", "cmd/", "internal/"]:
            if prefix in changed:
                changed = changed.split(prefix)[-1]
                break
        if not changed.startswith("src/") and not changed.startswith("e2e/"):
            changed = "src/" + changed

        results = match_file(policy_dir, changed)
        if not results:
            sys.exit(1)

        for r in results:
            print(f"PAGE={r['page']}")
            print(f"FLOWS={len(r['flows'])}개: {', '.join(r['flows'][:5])}")
            test_files = r["testFiles"]
            print(f"TEST_FILES={' '.join(test_files)}")
            # 각 테스트 파일의 실행 명령도 출력
            for tf in test_files:
                cmd = get_run_command(config, tf)
                if cmd:
                    print(f"CMD_{tf}={cmd}")
    elif mode == "--config":
        # config.json 내용 출력 (디버깅용)
        if config:
            print(json.dumps(config, indent=2, ensure_ascii=False))
        else:
            print("config.json 없음")
    else:
        print(f"Usage: {sys.argv[0]} --match <file> | --run-all | --config")
