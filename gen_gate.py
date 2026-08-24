#!/usr/bin/env python3
"""
생성 게이트 검사기 (Generation Gate Checker)
────────────────────────────────────────────
43차(2026-08-24 · 14시 제작 회차 · build-kr) 산출물.

목적 — 러너(GitHub Actions)가 자기 생성한 dev.to 발행 원고를 `outbox/`에
쓰기 **전에** 통과해야 하는 코드 게이트. 통과분만 `outbox/`에 쓰고,
탈락분은 `notes/rejected/`(내부 기록)에만 남긴다.

⚠ 이 파일은 아직 `.github/workflows/agent-run.yml`에 박히지 않았다.
   지속 설정(R12 단서)이라 창업자 승인 1회가 있어야 러너에 들어간다.
   지금은 실물 + 재현 테스트로만 존재한다(§9-2 C 요구사항).

검사 두 갈래(둘 다 통과해야 최종 통과 — AND):
  1) P1 스캔      — 회사 내부 사실 낱말/마커 대조
  2) 형식 5축 검사 — §0-ⓨ 5축 (H1 · 수평선 · 태그수 · 제목 특수문자 · frontmatter 키)

핵심 설계 원칙(39차 §2-㊳의 반증에서 학습):
  「검사기가 파싱한 결과」가 아니라 **원문 줄 그대로**에서 검사한다.
  YAML을 파싱해 값만 꺼내 재검사하면, 파싱 단계가 이미 삼켜버린 문자
  (예: 큰따옴표)는 원리적으로 관측 불가능하다.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════
# 1. P1 스캔 — 회사 내부 사실 낱말/마커 대조
# ═══════════════════════════════════════════════════════════════════════
#
# 출처: build-kr SKILL.md 「절대 하지 말 것 1번」· 「2번이 이 종의 P1이다」.
# 범주 10개(이 회차 기준 최신 목록). 39차 이전 산출물이 「낱말 9개」라고
# 적은 것은 구판 목록이었다 — 「행사가」가 SKILL.md v0.2.0 이후 목록에
# 있는데 9개 집계에는 빠져 있었다. 이 회차가 10개로 맞춘다.
#
# ⚠ 한계 — 이 스캔은 「범주를 가리키는 일반 낱말·마커」만 잡는다.
#   법인명·서비스명·임직원 실명처럼 **고유명사**는 사전에 알 수 없으므로
#   일반 키워드 대조로는 원리적으로 못 잡는다. 이것이 "안 되는 지점"이다.
#   실제 고유명사 차단은 실행 시점에 BLOCKLIST_FILE(러너의 시크릿 경로)로
#   주입한다 — 이 저장소·이 프로젝트에는 어떤 실제 이름도 적지 않는다.

P1_KEYWORD_CATEGORIES: dict[str, list[str]] = {
    "전결한도": ["전결한도", "전결 한도", "전결권"],
    "결재선": ["결재선", "결재 라인"],
    "인감권한": ["인감권한", "인감 권한", "법인인감"],
    "정산기준": ["정산기준", "정산 기준"],
    "지분율": ["지분율", "지분비율", "지분 비율"],
    "주주": ["주주총회", "주주명부", "대주주", "주주 구성"],
    "행사가": ["행사가", "스톡옵션 행사가"],
    "임직원실명 마커": ["대표이사 성명", "이사회 의장 성명"],
}

# 법인명은 고유명사 자체는 못 잡지만, 법인격을 나타내는 표기 마커는 잡을 수 있다.
P1_ENTITY_MARKERS: list[str] = [
    "㈜", "주식회사", "(주)", "Co., Ltd", "Co.,Ltd", "Corp.", " Inc.",
]


@dataclass
class P1Hit:
    category: str
    keyword: str
    line_no: int
    line_text: str


def scan_p1(raw_text: str, blocklist: list[str] | None = None) -> list[P1Hit]:
    """원문 줄 단위로 P1 낱말/마커를 대조한다. blocklist는 실행 시점에
    주입되는 실제 고유명사 목록(이 코드에는 절대 포함하지 않는다)."""
    hits: list[P1Hit] = []
    lines = raw_text.splitlines()

    categories = dict(P1_KEYWORD_CATEGORIES)
    categories["법인격 마커"] = P1_ENTITY_MARKERS
    if blocklist:
        categories["실행시점 블록리스트"] = blocklist

    for i, line in enumerate(lines, start=1):
        for category, keywords in categories.items():
            for kw in keywords:
                if kw in line:
                    hits.append(P1Hit(category=category, keyword=kw, line_no=i, line_text=line))
    return hits


# ═══════════════════════════════════════════════════════════════════════
# 2. 형식 5축 검사 (§0-ⓨ)
# ═══════════════════════════════════════════════════════════════════════
#
# ① 본문 H1 0            — 본문(frontmatter 뒤)에 "# " 로 시작하는 줄이 없다
# ② 본문 수평선 `---` 0   — 본문에 정확히 "---" 인 줄이 없다
# ③ 태그 4개 이하          — frontmatter의 tags 값 개수가 4 이하
# ④ 제목에 큰따옴표·콜론 0  — **frontmatter의 title 원문 줄**에서 검사
#                            (파싱한 값이 아니라 원문 그대로 — 39차 교훈)
# ⑤ frontmatter 키는 title·tags 둘뿐

FRONTMATTER_FENCE = "---"


@dataclass
class FormatViolation:
    axis: str
    detail: str


@dataclass
class ParsedDraft:
    frontmatter_raw_lines: list[str]
    body_lines: list[str]
    title_raw_line: str | None
    tags_raw_line: str | None
    frontmatter_keys: list[str]
    ok: bool = True
    parse_error: str | None = None


def _split_frontmatter(raw_text: str) -> ParsedDraft:
    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return ParsedDraft([], lines, None, None, [], ok=False,
                            parse_error="frontmatter 시작 펜스(---)가 1행에 없다")

    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_FENCE:
            close_idx = i
            break
    if close_idx is None:
        return ParsedDraft([], lines, None, None, [], ok=False,
                            parse_error="frontmatter 닫는 펜스(---)를 못 찾았다")

    fm_lines = lines[1:close_idx]
    body_lines = lines[close_idx + 1:]

    title_line = None
    tags_line = None
    keys: list[str] = []
    for fm_line in fm_lines:
        if not fm_line.strip():
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", fm_line)
        if not m:
            continue
        key = m.group(1)
        keys.append(key)
        if key == "title":
            title_line = fm_line
        elif key == "tags":
            tags_line = fm_line

    return ParsedDraft(fm_lines, body_lines, title_line, tags_line, keys, ok=True)


def check_format_5axis(raw_text: str) -> list[FormatViolation]:
    violations: list[FormatViolation] = []
    parsed = _split_frontmatter(raw_text)

    if not parsed.ok:
        violations.append(FormatViolation("frontmatter 구조", parsed.parse_error or "파싱 실패"))
        return violations  # 나머지 축은 frontmatter가 있어야 판단 가능하므로 여기서 멈춘다

    # ① 본문 H1 0
    h1_lines = [i for i, l in enumerate(parsed.body_lines, start=1) if re.match(r"^#\s", l)]
    if h1_lines:
        violations.append(FormatViolation("①본문 H1", f"본문 {h1_lines}행에 H1(`# `) 발견"))

    # ② 본문 수평선 --- 0
    hr_lines = [i for i, l in enumerate(parsed.body_lines, start=1) if l.strip() == "---"]
    if hr_lines:
        violations.append(FormatViolation("②본문 수평선", f"본문 {hr_lines}행에 `---` 발견"))

    # ③ 태그 4개 이하
    if parsed.tags_raw_line is None:
        violations.append(FormatViolation("③태그수", "tags 키가 frontmatter에 없다"))
    else:
        value = parsed.tags_raw_line.split(":", 1)[1].strip()
        tag_list = [t.strip() for t in value.split(",") if t.strip()]
        if len(tag_list) > 4:
            violations.append(FormatViolation("③태그수", f"태그 {len(tag_list)}개 (한도 4)"))

    # ④ 제목에 큰따옴표·콜론 0 — title의 "원문 줄"에서 검사한다.
    #    파싱해서 얻은 값이 아니라 raw 문자열 그 자체를 스캔한다.
    if parsed.title_raw_line is None:
        violations.append(FormatViolation("④제목 특수문자", "title 키가 frontmatter에 없다"))
    else:
        title_value_part = parsed.title_raw_line.split(":", 1)[1] if ":" in parsed.title_raw_line else parsed.title_raw_line
        if '"' in title_value_part:
            violations.append(FormatViolation("④제목 특수문자", "제목 원문 줄에 큰따옴표(\") 존재"))
        # title: 뒤의 콜론(값 시작을 알리는 첫 콜론 1개)은 제외하고, 그 이후에 추가 콜론이 있는지 검사
        if ":" in title_value_part:
            violations.append(FormatViolation("④제목 특수문자", "제목 값 안에 콜론(:) 존재"))

    # ⑤ frontmatter 키는 title·tags 둘뿐
    key_set = set(parsed.frontmatter_keys)
    if key_set != {"title", "tags"}:
        extra = key_set - {"title", "tags"}
        missing = {"title", "tags"} - key_set
        detail = []
        if extra:
            detail.append(f"허용 안 된 키 {sorted(extra)}")
        if missing:
            detail.append(f"필수 키 누락 {sorted(missing)}")
        violations.append(FormatViolation("⑤frontmatter 키", " · ".join(detail)))

    return violations


# ═══════════════════════════════════════════════════════════════════════
# 3. 게이트 — P1 스캔 AND 형식 5축, 둘 다 통과해야 최종 통과
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class GateResult:
    passed: bool
    p1_hits: list[P1Hit] = field(default_factory=list)
    format_violations: list[FormatViolation] = field(default_factory=list)

    def reasons(self) -> list[str]:
        out = []
        for h in self.p1_hits:
            out.append(f"[P1] {h.category} — {h.line_no}행 '{h.keyword}'")
        for v in self.format_violations:
            out.append(f"[형식] {v.axis} — {v.detail}")
        return out


def run_gate(raw_text: str, blocklist: list[str] | None = None) -> GateResult:
    """중요 — 두 검사를 모두 끝까지 돌리고 나서 합친다.
    한쪽에서 위반이 나왔다고 다른 쪽 검사를 건너뛰지 않는다(단축 평가 금지).
    이것이 이 회차의 반증 테스트가 확인하는 지점이다(15차 정렬식 병합 버그의 재발 방지)."""
    p1_hits = scan_p1(raw_text, blocklist=blocklist)
    format_violations = check_format_5axis(raw_text)
    passed = (len(p1_hits) == 0) and (len(format_violations) == 0)
    return GateResult(passed=passed, p1_hits=p1_hits, format_violations=format_violations)


def gate_file(path: str, blocklist_file_env: str = "P1_BLOCKLIST_FILE") -> GateResult:
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    blocklist = None
    blocklist_path = os.environ.get(blocklist_file_env)
    if blocklist_path and os.path.exists(blocklist_path):
        with open(blocklist_path, "r", encoding="utf-8") as bf:
            blocklist = [line.strip() for line in bf if line.strip()]

    return run_gate(raw_text, blocklist=blocklist)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: gen_gate.py <draft.md>")
        raise SystemExit(2)

    result = gate_file(sys.argv[1])
    if result.passed:
        print("PASS — outbox/에 쓴다")
        raise SystemExit(0)
    else:
        print("REJECT — notes/rejected/에만 남긴다")
        for r in result.reasons():
            print(" -", r)
        raise SystemExit(1)
