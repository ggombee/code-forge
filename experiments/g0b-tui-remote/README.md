# G0b — 개인 Codex CLI와 원격 TUI 첫 실험

개발자 TUI·원격 사용을 먼저 검증하는 좁은 실행 단면이다. 통제된 합성 Python CLI의 false PASS 결함을 실제 모델로 수정하고, 독립 검사 → 후보 승인 → 별도 파일 반영 → readback → SSH 재접속으로 같은 Work 확인을 연결했다. 제품의 전체 G0a/G0b gate나 출시 완료를 뜻하지 않는다. 방향과 다음 단계는 [CURRENT](../../docs/improvement-plan-2026-09.md), gate는 [기존 실행 계획](../../plan/code-forge-final-improvement-plan-2026-10-18.md)을 따른다.

## 구현 범위와 첫 runtime

- 단일 OS 사용자 전용 SQLite WAL 원장, Work revision·attempt/lease 세대·호출 예약 상한, 독립 oracle과 후보 digest 고정.
- detached worker의 실제 개인 Codex CLI 1회 실행, 읽기 전용 status/events와 terminal TUI, 접속 수명과 작업 수명 분리.
- 후보·base·policy·identity에 묶인 만료 승인, 별도 apply, durable intent·동일 key 영수증·파일 digest readback·명시적 reconcile.
- runtime 종료가 관측된 실패와 종료 불명, 취소 요청과 취소 완료를 구분하고 stale 승인·경로 우회·중복 반영을 거부.

사용자가 별도로 선택한 **첫 runtime은 개인 `codex-cli 0.167.0`**이다. 명시 요청 모델은 `gpt-6.1-sol`이며 실제 backend effective model은 관측하지 못했다. 계정·모델 자동 fallback과 자동 재호출은 없다. OMP RPC를 경유한 실행이 아니다.

기존 공개 source 조사에서는 설치된 OMP `18.16.0`의 [공식 태그 대응 commit](https://github.com/can1357/oh-my-pi/commit/650f3a108229ee11bf68ba3377f4e8c3391cd424)을 기준으로 JSONL `ready`/v2/`get_state`/`prompt_result`/`session_settled`와 독립 OAuth profile 필요를 확인했다. 공식 Codex auth importer는 확인하지 못해 사용자가 검증된 개인 Codex CLI를 첫 runtime으로 선택했다. 이 조사는 OMP RPC 접속·취소·복구의 실제 실증이 아니다. controlled OMP fork와 Tern SDK 연결은 구현하지 않았다.

## 실행 전제

이 가이드는 저장소 root에서 POSIX shell로 실행한다. Python 표준 라이브러리만 사용하지만 `fcntl`, `termios`, `dir_fd`, `O_NOFOLLOW`, `flock`, process group과 SQLite가 필요하다. Windows는 지원 검증하지 않았다. 코드에 최소 Python 버전 선언·검사는 없다. `from __future__ import annotations` 때문에 Python 3.7 미만은 사용할 수 없으며, SQLite의 UPSERT에는 SQLite 3.24.0 이상이 필요하다. 그 이상 모든 조합의 호환성을 검증했다는 뜻은 아니다. **실제 관측 환경은 macOS·Python 3.15**이며 아래 안내도 그 검증 환경을 기준으로 한다.

사전에 승인된 개인 프로젝트 보안 규칙(`docs/personal-project-security.md`; 현재 checkout에는 미포함)에 따라 실제 개인 Codex 로그인과 공식 personal-project-guard 설치·개인 정책 등록·doctor 통과가 선행되어야 한다. 보호된 개인 실행 환경에서 사용자가 직접 로그인하고 계정을 확인한다. 이 실험은 로그인·guard 설치·정책 등록을 대신하지 않는다. 회사 계정·미확인 계정에서는 실행하지 않는다. API key 인증은 이 adapter의 대상이 아니다.

```bash
# 사용자가 실제 개인 계정 email과 검증한 codex 실행 파일 경로를 넣는다.
ACCOUNT_EMAIL='본인의_개인_Codex_계정_email'
CODEX_BINARY='/본인이/확인한/codex'
export CODEX_HOME="$HOME/.codex"
export CODEX_AUTO_ACCOUNT_SELECTED=personal
export FORGE_GLOW_CODEX_ACCOUNT=personal
unset CLAUDE_AUTO_ACCOUNT_SELECTED

# 자격 파일 내용을 출력하지 않고 공식 로컬 검사를 수행한다.
python3 -B "$HOME/.config/personal-project-guard/guard.py" doctor
```

현재 adapter는 개인 profile을 `$HOME/.codex`로 확인한다. `CODEX_HOME` 또는 두 personal 선택 변수가 빠지거나 다르고, Claude 계정 선택 변수가 남아 있거나, guard·개인 OAuth claim·요청 email 대조가 실패하면 모델 호출 전에 `IDENTITY_UNKNOWN`으로 차단한다. 변수 설정만으로 실제 개인 로그인·정책 확인을 대신할 수 없다. 익명/default 모델이나 다른 계정으로 바꿔 통과시키지 않는다. 모델 요청 인자와 backend model 관측도 구별한다.

상태와 workspace는 Git 밖의 소유자 전용 canonical 경로로 분리한다. 경로 구성요소에 symlink·`..`를 사용하지 않고 공유·회사 자료를 넣지 않는다. 다음은 사용자 home을 기준으로 하는 예이며 실제 개인 절대 경로를 문서에 적을 필요가 없다.

```bash
umask 077
STATE_DIR="$HOME/.local/state/codeforge-g0b"
WORKSPACE_PARENT="$HOME/.local/share/codeforge-g0b/fixture-01"

# 공통 옵션은 subcommand 앞에 둔다. 모델·계정은 매번 명시한다.
g0b() {
  python3 -B experiments/g0b-tui-remote/run.py \
    --state-dir "$STATE_DIR" --codex-binary "$CODEX_BINARY" \
    --model gpt-6.1-sol --expected-account "$ACCOUNT_EMAIL" "$@"
}
```

`new`는 새 경로 또는 빈 `WORKSPACE_PARENT` 아래 합성 workspace를 만든다. 기존 작업 디렉터리를 넘기지 않는다. 상태 디렉터리는 0700, DB·artifact 등 상태 파일은 0600으로 관리한다. state 경로 아래에 workspace를 두지 않는다. 디렉터리 경계·소유권·symlink/hardlink를 검사하지만 같은 OS 사용자의 임의 쓰기를 차단하는 sandbox는 아니다.

## 생성·실행·검토·반영

```bash
# guard/identity 확인과 Work·합성 파일 생성. 모델 호출 없음.
g0b new --workspace "$WORKSPACE_PARENT"
g0b status

# 위 new 출력에서 자신의 work_id를 복사한다.
WORK_ID='new_출력의_work_id'
g0b status "$WORK_ID"
g0b run "$WORK_ID" --timeout 240
# 시작 응답 뒤 shell/SSH를 종료해도 detached worker는 계속 실행한다.
g0b tui "$WORK_ID" --timeout 240
```

`run`/TUI `r`은 호출 예약을 최대 1회 소비한다. timeout은 180~3600초이며 기본 240초다. 실패·취소해도 예약을 환불하지 않는다. 이는 **모델 호출 예약 횟수 cap**이며 USD·token hard cap이 아니다. `new`, `status`, TUI 접속·detach는 모델 호출이 아니다. TUI에 새 요청 입력기는 없으며 CLI `new`로 고정된 합성 작업을 만든다.

| 키 | 동작 |
|---|---|
| `r` → `y` | 현재 Work 모델 실행 요청 확인 |
| `v` | 화면의 검증 통과 후보 revision·digest를 승인 대상으로 선택 |
| `a` → `y` | 선택한 후보 승인. target 파일은 아직 원본 |
| `p` → `y` | 유효 승인으로 별도 반영하고 readback |
| `c` → `y` | 취소 요청. 실제 종료 관측 전 완료로 표시하지 않음 |
| `j` / `k` | 좁은 terminal에서 digest·근거·확인 메시지 스크롤 |
| `q` / `Ctrl-C` | 접속만 detach. Work·worker 유지 |

변경 동작은 `y` 확인이 필요하며 다른 키로 해제한다. 정상 검토 흐름은 `REVIEW_READY`에서 `v → a → y → q`, 다음 접속에서 `p → y → q`다. TUI의 digest·검사 결과와 비공개 로컬 후보 내용을 확인한 뒤 승인한다. 후보는 status의 `candidate_file`이 가리키는 state 디렉터리의 `candidate-<임의_ID>.bin`에 저장된다. TUI는 상태·근거·행동을 표시하는 최소 terminal UI이며 후보 source/diff viewer나 시각 디자인 완성본은 아니다.

CLI로도 승인과 반영을 나눌 수 있다. 다음 변수는 최신 status와 approve 출력에서 확인한 자기 작업 값으로 바꾼다. 전체 status JSON에는 로컬 경로·계정 fingerprint 등 개인 메타데이터가 있으므로 게시 문서나 공유 로그로 복사하지 않는다.

```bash
g0b status "$WORK_ID"
CANDIDATE_SHA='확인한_candidate_sha256'
REVIEW_REVISION='확인한_revision'
g0b approve "$WORK_ID" --artifact-sha256 "$CANDIDATE_SHA" \
  --expected-revision "$REVIEW_REVISION"

APPROVAL_ID='approve_출력의_approval_id'
# 한 논리적 반영에 하나를 정하고 응답 유실 뒤에도 같은 값을 보존한다.
APPLY_KEY='본인이_정한_이번_반영의_고유_key'
g0b apply "$WORK_ID" --approval-id "$APPROVAL_ID" --idempotency-key "$APPLY_KEY"
g0b status "$WORK_ID"
```

승인 만료·revision/base/후보 변경은 거부한다. `APPLIED`의 `receipt.readback_sha256`와 `candidate_sha256`를 대조한다. 같은 approval/key의 재요청은 기존 receipt를 반환하며 다시 교체하지 않는다. 다른 action에 key를 재사용하지 않는다.

## SSH에서 사용

사용자가 관리하고 신뢰하는 머신에 이 checkout·지원 Python·개인 Codex CLI·guard를 준비한다. SSH host는 사용자가 정한 일반 접속 대상이며 이 문서의 로컬 시험 서버를 뜻하지 않는다. host key를 검증하고 개인 로그인·모델 자격정보는 실행 호스트의 보호된 환경에 둔다. 키·credential·시험 SSH 설정을 저장소에 복사하지 않는다.

```bash
ssh YOUR_SSH_HOST
# 원격 shell에서 실제 checkout으로 이동한다.
cd /개인/checkout/code-forge
# 위 실행 전제의 환경변수와 g0b 함수를 이 호스트에서 다시 설정한다.
# 최초 한 번만 new를 실행하고 자신의 Work ID를 보존한다.
g0b new --workspace "$WORKSPACE_PARENT"
WORK_ID='new_출력의_work_id'
g0b run "$WORK_ID" --timeout 240
exit

ssh -t YOUR_SSH_HOST
cd /개인/checkout/code-forge
# 같은 환경·STATE_DIR·개인 모델/계정·g0b 함수를 다시 설정한다.
WORK_ID='앞서_보존한_work_id'
g0b status "$WORK_ID"
g0b tui "$WORK_ID"
```

실제 TTY가 필요하므로 원격에서 `tui`를 쓸 때는 PTY를 할당한다. 재접속은 같은 state와 Work를 조회하며 `new`/`run`을 자동 반복하지 않는다. 여기서 관측된 SSH는 한 macOS 호스트의 loopback OpenSSH에서 CLI 생성·실행·조회·재접속을 확인한 시험이다. TUI는 로컬 PTY에서 실제 조작했으며, 원격 SSH의 TUI 렌더링·실제 다른 머신·서버나 OS 차이의 검증은 남아 있다.

## 상태와 장애 복구

| 상태/관측 | 처리 |
|---|---|
| `NEW` | 생성됨, 모델 미호출 |
| `RUNNING` | worker 실행 중. SSH 단절·TUI q와 별개 |
| `REVIEW_READY` | 독립 검사 통과 후보. 승인 후에도 실제 apply 전까지 이 상태 |
| `VERIFICATION_FAILED` | 고정 검사 실패. 승인·반영 불가 |
| `RUNTIME_FAILED` | 실제 process 종료를 관측한 runtime 실패. 후보 승인·반영 불가 |
| `RUNTIME_UNKNOWN` | 종료·외부효과 불명. 새 호출·승인·반영 차단 |
| `CANCEL_REQUESTED` / `CANCELLED` | 요청 / 요청 후 실제 종료 관측. 접속 해제와 구별 |
| `APPLYING` / `APPLY_UNKNOWN` | durable intent 이후 반영 결과 조정 필요 |
| `APPLIED` | 실제 target digest readback과 receipt 기록 |
| `START_UNCONFIRMED` | launcher 시작 응답 미관측. 완료·미실행으로 단정하지 않음 |

```bash
g0b status "$WORK_ID"
g0b events "$WORK_ID"
# 조회 결과를 확인한 뒤 필요한 조정만 명시적으로 요청한다.
g0b reconcile "$WORK_ID"
# 중단 의사가 있을 때만 요청한다.
g0b cancel "$WORK_ID"
g0b status "$WORK_ID"
```

`status`/`events`는 실행·복구하지 않는다. 살아 있는 worker가 lease를 보유하면 reconcile은 `ATTEMPT_RUNNING`으로 거부한다. worker lease만 사라지고 child 종료를 관측할 수 없으면 `RUNTIME_UNKNOWN`으로 남긴다. PID 부재만으로 취소·종료를 확정하지 않으며 현재 CLI는 이 상태를 강제로 성공/종료 처리하는 명령을 제공하지 않는다. 보호된 실행 환경에서 실제 종료·외부효과를 별도 조사하기 전 새 Work로 같은 모델 호출을 우회 재생하지 않는다.

반영 reconcile은 target digest가 candidate면 `APPLIED` receipt로 조정하고, baseline이면 반영되지 않은 것으로 기록해 승인을 지우고 `REVIEW_READY`로 돌린다. 그 뒤 검토·새 승인·새 key가 필요하다. 어느 쪽도 아니거나 경계를 확인하지 못하면 `APPLY_UNKNOWN`을 유지한다. reconcile은 파일을 자동 재반영하지 않는다. state DB·intent·artifact를 수동 편집하거나 삭제해서 unknown을 지우지 않는다. provider 과금 취소·외부 effect rollback은 구현하지 않았다.

## 실제 검증 근거와 남은 gate

부모 실행에서 다음 명령으로 **47개, 16.084초, OK**를 관측했다. 이번 문서 마무리에서는 다시 실행하지 않았다.

```bash
python3 -B -m unittest discover -s experiments/g0b-tui-remote/tests -p 'test_*.py' -v
```

- 실제 개인 Codex CLI 호출 1회, 요청 모델 `gpt-6.1-sol`, backend model 미관측, 자동 fallback 없음.
- `/usr/sbin/sshd`의 `127.0.0.1` 전용 시험 서버에서 기존 SSH 계정설정·키·agent를 사용하지 않고 새 시험 key와 host key pin으로 실제 접속했다. 새 SSH에서 CLI로 NEW 생성·조회, 원격 run 뒤 연결 종료, 새 연결에서 같은 Work `REVIEW_READY`와 예약 1/1을 관측했다. TUI `q` detach 뒤 worker 완료는 로컬 PTY에서 확인했다.
- oracle 본문을 모델에 주지 않고 고정 [oracle.py](oracle.py)의 SHA256 `a13a995fcf9af7c0cec08a16c4444cae7e490347a9657f8fd24a368de33fd61c`를 기준으로 candidate를 실제 subprocess에서 16/16 검사했다. baseline의 설정 없음/JSON 오류 등 설정 실패와 도구 부재라는 두 부류의 false PASS를 검출했다.
- 로컬 PTY에서 실제 TUI `v → a → y → q` 뒤 target 원본 유지, 별도 `p → y → q` 뒤 새 SSH status `APPLIED`와 target/candidate digest 일치를 확인했다. 같은 approval/key 재요청에서 target device/inode/mtime_ns 불변·receipt 동일, 완료 TUI 재접속·q 정상도 관측했다.
- 독립 개인 코드 검토가 동일 target의 nested workspace alias 우회를 지적했다. 부모 throwaway 재현에서 수정 전 `rejected:false, target_unchanged:false, first_state:APPLY_UNKNOWN`, 최소 수정 후 `rejected:true, code:APPLY_UNKNOWN, target_unchanged:true`를 관측했고 [영구 회귀](tests/test_core.py)에 포함했다.
- 구현 중 `runtime_failure` 누락을 해결하고 placeholder gate를 제거했다. [Core](core.py)·[runtime 회귀](tests/test_runtime.py)는 종료 관측 실패/종료 불명/취소 완료를 구분한다. 모의·회귀 검사와 실제 1회 모델 성공 흐름의 범위를 혼동하지 않는다.

관측 출처는 로컬의 `g0b-live-smoke-report.json`, `g0b-tui-new.txt`, `g0b-tui-review.txt`, `g0b-tui-approved.txt`, `g0b-tui-apply-action.txt`, `g0b-tui-applied.txt`, `implement-review-core-result.txt`, `implement-fix-core-result.txt`다. 이들은 조사 당시의 비공개 근거이며 저장소에 반입하지 않았다. 위 기록과 가이드는 해당 tempdir·smoke helper를 필수 입력으로 삼지 않으며 원자료 전체의 이식·독립 감사 재현을 뜻하지 않는다.

통과 범위는 **단일 OS 사용자·private SQLite·controlled synthetic file**이다. 공개 multi-tenant 격리, 실제 외부 원격 서버, OMP RPC, Tern SDK, 네이티브 앱·웹·Telegram, 공급자 상업 OAuth 약관 확인, 금액 budget cap, provider 과금 취소·외부 effect rollback, OS 전체 sandbox는 미구현/미검증이다. CLI read-only·clean env·도구 이벤트 감시는 OS 전체 read/network sandbox가 아니다. provider identity의 충분한 증명·backend model 관측, 원가/금액 cap, 원격 OS 차이, packaging·기억·격리·복구 등 남은 gate는 기존 계획에서 계속 검토한다. raw terminal 기록의 모양을 제품의 시각 완성도나 사용성 평가 통과로 해석하지 않는다.

첫 구현은 별도 detached checkout에 있으며 아직 commit/push하지 않았다. 첫 실험 코드·회귀 테스트·실행 가이드와 기존 계획 상태 갱신을 `docs/agentops-platform-plan`에 게시하는 승인은 이미 받았다. 다음은 이 실험을 근거로 최소 실행 계약을 검토·확정하고, OMP isolated personal OAuth/RPC 접속 실증과 실제 다른 호스트 원격 실증 중 우선할 한 단계를 좁히는 것이다.
