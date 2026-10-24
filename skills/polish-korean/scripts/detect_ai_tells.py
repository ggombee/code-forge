#!/usr/bin/env python3
"""한국어 업무·기술 문서의 AI 티 패턴을 검출한다.

references/style-rules.md 의 패턴 ID 와 1:1 대응한다.
코드 블록, 인라인 코드, 링크 URL, 표 구분선은 검사 대상에서 뺀다.

사용법:
    python3 detect_ai_tells.py <file.md> [--severity S1|S2|all] [--json]

종료 코드:
    0  S1 잔존 없음
    1  S1 잔존 있음 (윤문 미완료)
"""
import argparse
import json
import re
import sys
from pathlib import Path

# (id, 심각도, 설명, 정규식, 임계값) — 임계값 이상일 때만 보고한다.
PATTERNS = [
    ("A-1", "S1", "~에 있어(서)", r"에\s*있어서?\b", 1),
    ("A-2", "S1", "이중 피동 ~되어진다/~지게 된다", r"되어지|지게\s*된다", 1),
    ("A-3", "S2", "~에 의해 피동", r"에\s*의해", 3),
    ("A-4", "S2", "~를 통해", r"[을를]\s*통(해|하여)", 3),
    ("A-5", "S1", "가지고 있다 직역", r"[을를]\s*가지고\s*있", 1),
    ("A-6", "S2", "~을 위해 목적절", r"[을를]\s*위해", 4),
    ("A-7", "S2", "이중 조사 ~에서의/~으로의", r"(에서의|으로의|에의|로부터의)", 2),

    ("B-1", "S1", "공간·구조 비유(경계·자리·축·계층·무게·한 벌·떠 있는)",
     r"(경계|자리와|자리를|지점에서|축을|축이|계층으로|무게를|무게가|한\s*벌|떠\s*있)", 1),
    ("B-2", "S1", "억지 동사(굴리다·걷어내다·덜어내다·짐이 되다)",
     r"(굴리|굴려|걷어내|덜어내|짐이\s*되|묻힙니다|묻힌다)", 1),
    ("B-3", "S2", "어려운 한자어(정본·게이트·산출물·관측·전수)",
     r"(정본|게이트|산출물|관측|전수\s*조회)", 1),

    ("C-1", "S1", "대구 'A가 아니라 B' / '~것이 아니다'",
     r"(가\s*아니라|이\s*아니라|것이\s*아닙니다|것이\s*아니다|는\s*아닙니다)", 2),
    ("C-3", "S2", "문단 첫머리 먼저/반면/결국 공식", r"^(먼저|반면|결국)[\s,]", 3),
    ("C-4", "S2", "소제목 기계적 병렬(대시 제목·번호 축)", r"^#{2,4}\s+.*(—|축\s*\d)", 3),
    ("C-5", "S2", "연결어미 직후 쉼표", r"(하고|하며|지만|면서|아서|어서),", 4),

    ("D-1", "S1", "결산 어휘(결론적으로·요약하면·이를 통해)",
     r"(결론적으로|요약하면|정리하자면|이를\s*통해)", 3),
    ("D-2", "S1", "의의 과장(시사하는 바·주목할 만·매우 중요)",
     r"(시사하는\s*바|주목할\s*만|매우\s*중요)", 1),
    ("D-3", "S1", "열거 도입(크게 N가지·다음과 같다)",
     r"(크게\s*[일이삼사오\d]\s*가지|다음과\s*같습니다|다음과\s*같다)", 1),
    ("D-4", "S1", "분열문(문제는·핵심은·필요한 것은·~라는 점이다)",
     r"(문제는\s|핵심은\s|핵심입니다|필요한\s*것은|라는\s*점(이다|입니다))", 2),
    ("D-5", "S1", "의인화 추상 주어",
     r"(문제가\s*서로|시대가\s*|기술이\s*묻|가\s*맡으면|가\s*갖습니다|가\s*담습니다)", 1),
    ("D-6", "S2", "hype 어휘", r"(혁신적|획기적|압도적|전례\s*없는|파격적)", 1),
    ("D-7", "S2", "~하는 이유다 / 결국", r"(하는\s*이유다|이유입니다|결국)", 2),
    ("D-8", "S2", "사전 은유(잠식·청사진·적신호·신호탄)",
     r"(잠식|청사진|적신호|신호탄|주춧돌|뿌리내리)", 1),

    ("F-1", "S2", "~한 것이다/~일 것이다", r"(한\s*것이다|일\s*것이다|한\s*것입니다)", 3),
    ("F-2", "S2", "~다는 것이다/~다는 뜻이다", r"(다는\s*것(이다|입니다)|다는\s*뜻)", 2),
    ("F-3", "S2", "-적 추상 체인", r"[가-힣]적\s+[가-힣]{2,}", 6),
    ("F-4", "S2", "범용 정책동사", r"(확대|강화|개선|확보|구축|마련)(한다|합니다|하고|해야)", 4),

    ("G-2", "S1", "이중 완곡", r"(가능성이\s*있을\s*수|보여질\s*수|될\s*수도\s*있을)", 1),
    ("G-3", "S2", "문두 접속사", r"^(또한|따라서|즉|게다가|나아가|아울러)[\s,]", 3),
    ("G-4", "S2", "유보 문단 반복(다만/단,)", r"^(다만|단,)", 3),

    # N-3(제목↔결론 불일치)과 N-4·N-5(반복), N-6(장르 불일치)은 절 전체를 읽어야
    # 판정할 수 있어 검출기에 넣지 않는다. style-rules.md 의 "읽어서 확인하는 것" 에서 다룬다.
    ("N-1", "S1", "부정으로 설명하기 — 독자가 하지 않은 오해를 부정하는 불릿",
     r"^\s*[*\-]\s+\*\*[^*]{0,70}(아니다|아닙니다|없다|없습니다|않는다|않습니다)[.。]?\*\*", 2),

    ("H-5", "S1", "글쓴이를 위한 방어 절(측정 방법·미리 답하기)",
     r"^#{2,4}\s+.*(이렇게 셌|측정 방법|한계와 전제|질문이 나오면)", 1),
    ("H-5b", "S1", "아무도 묻지 않은 것에 미리 답하기",
     r"(질문이\s*나오면|물어보시면|그 자리에서 다시 뽑)", 1),
    ("H-6", "S1", "실행 주체·방법 없는 계측 약속",
     r"\d+\s*(주|개월|달)\s*동안[^.]{0,40}(세어|재어|측정해)", 1),
    ("H-7", "S2", "구어체 의문형 제목(다른 제목과 섞이면 어색)",
     r"^#{2,4}\s+.*(했나|됐나|일까|할까요|좋겠습니다)\s*$", 2),

    ("H-1", "S1", "측정 가능한 자리의 어림말(상당 부분·대부분·거의)",
     r"(상당\s*부분|대부분의|거의\s*모든|크게\s*늘)", 1),
    ("H-2", "S2", "행동 없는 제안", r"(하는\s*것이\s*좋겠|개선이\s*필요|검토가\s*필요)", 2),
    ("H-3", "S2", "자기 문서 참조 상투구", r"(앞서\s*언급|아래에서\s*다룬|위에서\s*살펴)", 2),
]

CODE_BLOCK = re.compile(r"^```")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_URL = re.compile(r"\]\([^)]*\)")
TABLE_SEP = re.compile(r"^\|[\s|:-]+\|$")


def strip_noise(line: str) -> str:
    line = INLINE_CODE.sub(" ", line)
    line = LINK_URL.sub("]( )", line)
    return line


def measure(path: Path):
    """비율로만 판정되는 항목(E-4 굵은 글씨, E-5 문장 길이)을 잰다."""
    body, in_code = [], False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if CODE_BLOCK.match(raw):
            in_code = not in_code
            continue
        if in_code or not raw.strip():
            continue
        if raw.lstrip().startswith(("#", "|", ">", "---")):
            continue
        body.append(raw)

    paragraphs = len(body)
    bolds = sum(line.count("**") for line in body) // 2
    sentences = [t.strip() for line in body for t in re.split(r"[.!?]\s|[.!?]$", line) if t.strip()]
    long_ones = [t for t in sentences if len(t) > 90]

    out = []
    if paragraphs and bolds * 4 > paragraphs:
        out.append(("E-4", f"굵은 글씨 {bolds}곳 / 문단 {paragraphs}개 — 4분의 1을 넘어 강조 구실을 못 한다"))
    if sentences and len(long_ones) * 2 > len(sentences):
        pct = len(long_ones) * 100 // len(sentences)
        out.append(("E-5", f"90자 초과 문장 {len(long_ones)}/{len(sentences)}개({pct}%) — 절반을 넘어 문장을 나눠야 한다"))
    return out, paragraphs, bolds, len(sentences), len(long_ones)


def scan(path: Path):
    hits = {}
    in_code = False
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if CODE_BLOCK.match(raw):
            in_code = not in_code
            continue
        if in_code or TABLE_SEP.match(raw):
            continue
        line = strip_noise(raw)
        for pid, sev, desc, rx, _ in PATTERNS:
            for m in re.finditer(rx, line, re.MULTILINE):
                hits.setdefault(pid, {"severity": sev, "desc": desc, "sites": []})
                hits[pid]["sites"].append({"line": lineno, "text": m.group(0).strip()})
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--severity", choices=["S1", "S2", "all"], default="all")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"파일을 찾을 수 없습니다: {path}", file=sys.stderr)
        return 2

    hits = scan(path)
    thresholds = {pid: th for pid, _, _, _, th in PATTERNS}
    reported = {
        pid: h for pid, h in hits.items()
        if len(h["sites"]) >= thresholds[pid]
        and (args.severity == "all" or h["severity"] == args.severity)
    }

    ratios, paras, bolds, sents, longs = measure(path)

    if args.json:
        payload = dict(reported)
        payload["_measure"] = {
            "paragraphs": paras, "bolds": bolds,
            "sentences": sents, "over_90": longs,
            "warnings": [{"id": i, "text": t} for i, t in ratios],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not reported and not ratios:
            print("검출된 패턴 없음")
        for pid in sorted(reported, key=lambda p: (reported[p]["severity"], p)):
            h = reported[pid]
            lines = ", ".join(str(s["line"]) for s in h["sites"][:8])
            more = "" if len(h["sites"]) <= 8 else f" 외 {len(h['sites']) - 8}건"
            print(f"[{h['severity']}] {pid} {h['desc']} — {len(h['sites'])}회 (줄 {lines}{more})")
        for pid, text in ratios:
            print(f"[S2] {pid} {text}")
        if args.severity == "all":
            print(f"     (문단 {paras} · 굵은 글씨 {bolds} · 문장 {sents} · 90자 초과 {longs})")

    s1 = [p for p, h in reported.items() if h["severity"] == "S1"]
    if s1:
        print(f"\nS1 잔존 {len(s1)}종: {', '.join(sorted(s1))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
