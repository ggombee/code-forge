#!/bin/bash
# package-changed.sh — package.json 변경 감지
# FileChanged hook

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('file', ''))
except:
    print('')
" 2>/dev/null)

echo "[FileChanged] $FILE 변경 감지"
echo "의존성 변경이 있을 수 있습니다. 필요시 yarn install을 실행하세요."
exit 0
