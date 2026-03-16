---
name: setup-notifier
description: Mac 알림 설정. Claude Code에서 승인 요청 시 terminal-notifier로 배너 알림을 보낸다.
---

# /setup-notifier

Claude Code에서 사용자 승인이 필요할 때 Mac 알림(배너 + 소리)을 보내도록 설정한다.

## 실행 워크플로우

아래 단계를 순서대로 즉시 실행한다.

### Step 1. terminal-notifier 설치

```bash
which terminal-notifier || brew install terminal-notifier
```

### Step 2. notify.sh 권한 설정

```bash
chmod +x hooks/notify.sh
```

### Step 3. settings.local.json 훅 설정

`.claude/settings.local.json` 파일을 확인하고 `hooks.PermissionRequest` 항목을 추가한다.

**파일이 없는 경우** → 신규 생성:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ./hooks/notify.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**파일이 있는 경우** → 기존 내용에 `hooks.PermissionRequest` 병합 (중복 체크).

### Step 4. 완료 확인

```
terminal-notifier 설치 완료
settings.local.json 훅 설정 완료
설정 반영을 위해 Claude Code를 재시작하세요
```
