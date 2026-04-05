---
name: stats
description: code-forge 사용량 통계. ~/.code-forge/usage.jsonl을 파싱하여 에이전트/스킬 사용 빈도 top 5와 요약을 터미널에 출력.
category: utility
user-invocable: false
---

# /stats — Bellows 사용량 통계

usage.jsonl 로그를 분석하여 에이전트/스킬 사용 통계를 보여준다.

**[즉시 실행]** 아래 절차를 따라 통계를 출력하세요.

**입력**: $ARGUMENTS

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| (없음) | 전체 통계 | `/stats` |
| `--week` | 최근 7일 | `/stats --week` |
| `--month` | 최근 30일 | `/stats --month` |
| `--project` | 현재 프로젝트만 | `/stats --project` |

---

## 실행 절차

### Step 1: 로그 파일 확인

```bash
LOG_FILE="$HOME/.code-forge/usage.jsonl"
```

파일이 없으면:
```
사용 기록이 없습니다. 에이전트나 스킬을 사용하면 자동으로 기록됩니다.
```

### Step 2: 통계 파싱

Bash로 usage.jsonl을 파싱한다.

**기간 필터링:**
- `--week`: 최근 7일의 타임스탬프만 필터
- `--month`: 최근 30일
- `--project`: `"project":"현재디렉토리명"`만 필터
- (없음): 전체

**파싱 방법:**

jq가 있으면 jq 사용:
```bash
# 에이전트 Top 5
jq -r 'select(.type=="agent") | .name' "$LOG_FILE" | sort | uniq -c | sort -rn | head -5

# 스킬 Top 5
jq -r 'select(.type=="skill") | .name' "$LOG_FILE" | sort | uniq -c | sort -rn | head -5
```

jq 없으면 grep/awk 폴백:
```bash
# 에이전트 Top 5
grep '"type":"agent"' "$LOG_FILE" | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | sort | uniq -c | sort -rn | head -5

# 스킬 Top 5
grep '"type":"skill"' "$LOG_FILE" | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | sort | uniq -c | sort -rn | head -5
```

### Step 3: 출력 형식

```markdown
## code-forge 사용 통계

**기간:** {시작일} ~ {종료일} ({총 N일})
**총 호출:** {총 횟수}회

### 에이전트 Top 5
| # | 에이전트 | 호출 | 비율 |
|---|---------|------|------|
| 1 | {name} | {count} | {%} |
| 2 | {name} | {count} | {%} |
| 3 | {name} | {count} | {%} |
| 4 | {name} | {count} | {%} |
| 5 | {name} | {count} | {%} |

### 스킬 Top 5
| # | 스킬 | 호출 | 비율 |
|---|------|------|------|
| 1 | {name} | {count} | {%} |
| 2 | {name} | {count} | {%} |
| 3 | {name} | {count} | {%} |
| 4 | {name} | {count} | {%} |
| 5 | {name} | {count} | {%} |

### 프로젝트별
| 프로젝트 | 에이전트 | 스킬 | 합계 |
|---------|---------|------|------|
| {name} | {count} | {count} | {total} |

### 일별 추이 (최근 7일)
{날짜}: {"█" * count} {count}
```

데이터가 적으면 (10건 미만) 간략 형식으로:
```
## code-forge 사용 통계

총 {N}회 사용 ({에이전트 X회, 스킬 Y회})

가장 많이 사용: {name} ({count}회)
```
