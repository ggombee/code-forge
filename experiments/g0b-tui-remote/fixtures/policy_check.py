"""G0b 수정 대상: 설정 읽기 실패와 도구 부재를 잘못 통과시키는 baseline."""

import argparse
import json
from pathlib import Path
import shutil
import sys


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, f"FAIL: {message}\n")


def main():
    parser = Parser(description="합성 정책과 필수 도구의 가용성을 확인합니다.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--tool", required=True)
    args = parser.parse_args()

    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("WARNING: 설정을 읽을 수 없습니다.", file=sys.stderr)
        print("PASS")
        return 0

    if not isinstance(config, dict) or config.get("enabled") is not True:
        print("FAIL: enabled는 true여야 합니다.", file=sys.stderr)
        return 1

    if shutil.which(args.tool) is None:
        print("WARNING: 필수 도구를 찾을 수 없습니다.", file=sys.stderr)
        print("PASS")
        return 0

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
