#!/usr/bin/env python3
"""
Fetch 101weiqi daily problem pages, decode qqdata, and produce:
  - extracted/sgf/<qid>.sgf
  - extracted/json/<qid>.json
  - extracted/review/pattern_review.md

Run from the 101/ directory.
"""

import re
import json
import base64
import time
import urllib.request
from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).parent.resolve()
OUT_DIR = ROOT / "extracted"
SGF_DIR = OUT_DIR / "sgf"
JSON_DIR = OUT_DIR / "json"
REVIEW_DIR = OUT_DIR / "review"

SGF_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

SGF_LETTERS = "abcdefghjklmnopqrst"


def letter_to_index(ch: str) -> int:
    return ord(ch) - ord('a')


def to_sgf(coord: str, size: int = 19) -> str:
    """Convert 101weiqi coordinate (full alphabet, y=0 bottom) to SGF."""
    if not coord or len(coord) != 2:
        return "tt"
    col_idx = letter_to_index(coord[0])
    row_idx = letter_to_index(coord[1])
    sgf_col = SGF_LETTERS[col_idx]
    sgf_row = SGF_LETTERS[(size - 1) - row_idx]
    return sgf_col + sgf_row


def decode_c(encoded: str, r: int) -> list:
    """XOR decode the qqdata.c field into [[black_stones], [white_stones]]."""
    key = "101" + str(r + 1) * 3
    decoded = base64.b64decode(encoded)
    key_bytes = key.encode()
    out = []
    for i, b in enumerate(decoded):
        out.append(chr(b ^ key_bytes[i % len(key_bytes)]))
    return json.loads(''.join(out))


def fetch_qqdata(year: int, month: int, day: int, qindex: int):
    url = f"https://www.101weiqi.com/qday/{year}/{month}/{day}/{qindex}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8')
    m = re.search(r'var qqdata = (\{.*?\});\s*\n', html, re.DOTALL)
    if not m:
        raise RuntimeError(f"qqdata not found in {url}")
    return json.loads(m.group(1))


def build_sgf(publicid: int, content: list, answers: list, blackfirst: bool,
              size: int = 19, category: str = "TOLIVE") -> str:
    """Build an SGF with initial position and answer/variation tree."""
    # Initial position
    ab = [to_sgf(c, size) for c in content[0]]
    aw = [to_sgf(c, size) for c in content[1]]

    # Determine turn color
    turn = "B" if blackfirst else "W"

    # Categorize answers
    correct = [a for a in answers if a['st'] == 2]
    variations = [a for a in answers if a['st'] == 1]
    failed = [a for a in answers if a['st'] == 0]

    # Pick the "main" correct answer: prefer shortest correct, then lowest nu
    if correct:
        main = min(correct, key=lambda a: (len(a['pts']), a['nu']))
    else:
        main = None

    def answer_to_sgf(answer: dict, label: str) -> str:
        nodes = []
        color = turn
        for pt in answer['pts']:
            coord = to_sgf(pt['p'], size)
            nodes.append(f";{color}[{coord}]")
            color = "W" if color == "B" else "B"
        return ''.join(nodes) + f"N[{label}]"

    # Each answer is a separate top-level branch from the initial position
    branch_nodes = []
    if main:
        branch_nodes.append("(" + answer_to_sgf(main, "正解") + ")")
    for ans in variations[:8]:  # limit to keep SGF manageable
        label = f"変化{ans['nu']}"
        branch_nodes.append("(" + answer_to_sgf(ans, label) + ")")
    for ans in failed[:3]:
        label = f"失敗{ans['nu']}"
        branch_nodes.append("(" + answer_to_sgf(ans, label) + ")")

    header = f"(;GM[1]FF[4]CA[UTF-8]SZ[{size}]GN[Q-{publicid}]PL[{turn}]"
    header += f"KM[6.5]"
    if category:
        header += f"GC[{category}]"
    if ab:
        header += "AB" + ''.join(f"[{c}]" for c in ab)
    if aw:
        header += "AW" + ''.join(f"[{c}]" for c in aw)

    if branch_nodes:
        sgf = header + '\n' + '\n'.join(branch_nodes) + ")"
    else:
        sgf = header + ")"
    return sgf


def build_json(publicid: int, sgf_str: str, content: list, answers: list,
               blackfirst: bool, size: int = 19, label: str = "") -> dict:
    """Build a JSON descriptor compatible with study-LD-RZ-solver format."""
    ab = [to_sgf(c, size) for c in content[0]]
    aw = [to_sgf(c, size) for c in content[1]]
    turn = "B" if blackfirst else "W"

    def answer_to_raw(answer, label):
        color = turn
        out = f"(;{color}[{to_sgf(answer['pts'][0]['p'], size)}]"
        for pt in answer['pts'][1:]:
            color = "W" if color == "B" else "B"
            out += f";{color}[{to_sgf(pt['p'], size)}]"
        out += f"N[{label}])"
        return out

    # Build rawsgf in MultiGo style with initial position + answer branches
    correct = [a for a in answers if a['st'] == 2]
    variations = [a for a in answers if a['st'] == 1]
    failed = [a for a in answers if a['st'] == 0]

    rawsgf = f"(;CA[UTF-8]AP[MultiGo:4.2.1]SZ[{size}]"
    rawsgf += "AB" + ''.join(f"[{c}]" for c in ab) if ab else ""
    rawsgf += "AW" + ''.join(f"[{c}]" for c in aw) if aw else ""

    if correct:
        main = min(correct, key=lambda a: (len(a['pts']), a['nu']))
        rawsgf += answer_to_raw(main, "正解")
        for ans in variations[:3]:
            rawsgf += answer_to_raw(ans, f"変化{ans['nu']}")
        for ans in failed[:2]:
            rawsgf += answer_to_raw(ans, f"失敗{ans['nu']}")
    rawsgf += ")"

    return {
        "filename": f"q_{publicid}.sgf",
        "type": "masked",
        "rawsgf": rawsgf,
        "date": "2026-08-26",
        "category": "TOLIVE",
        "winning_color": "b" if blackfirst else "w",
        "turn_color": "b" if blackfirst else "w",
        "black_crucial_stone": "",
        "white_crucial_stone": "",
        "black_search_goal": "TOLIVE",
        "white_search_goal": "TOKILL",
        "black_ko_rule": "disallow_ko",
        "white_ko_rule": "allow_ko",
        "screenshot_label": label,
        "answer_firstmove": to_sgf(main['pts'][0]['p'], size) if correct else "",
        "mask_type": "automask",
        "distance2wall": 4,
        "mask_filename": "",
        "mask_sgf": "",
        "add_pieces_before_masked": "",
        "remove_pieces_before_masked": "",
        "add_pieces_after_masked": "",
        "remove_pieces_after_masked": "",
        "masked_sgf_str": "",
        "region": "",
    }


def process_problem(year: int, month: int, day: int, qindex: int, label: str):
    print(f"Fetching {label}: {year}-{month:0>2}-{day:0>2} No.{qindex}")
    data = fetch_qqdata(year, month, day, qindex)
    publicid = data['publicid']
    content = decode_c(data['c'], data['r'])
    answers = data['answers']
    blackfirst = data.get('blackfirst', True)
    size = data.get('lu', 19)

    sgf = build_sgf(publicid, content, answers, blackfirst, size)
    (SGF_DIR / f"q_{publicid}.sgf").write_text(sgf, encoding='utf-8')

    prob_json = build_json(publicid, sgf, content, answers, blackfirst, size, label)
    (JSON_DIR / f"q_{publicid}.json").write_text(json.dumps(prob_json, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"  -> Q-{publicid}, {len(content[0])}B/{len(content[1])}W, {len(answers)} answers")
    return {
        "publicid": publicid,
        "content": content,
        "answers": answers,
        "blackfirst": blackfirst,
        "size": size,
        "label": label,
    }


PROBLEMS = [
    # 2026-08-24 (screenshots 241, 243-249)
    (2026, 8, 24, 1, "241"),
    (2026, 8, 24, 2, "243"),
    (2026, 8, 24, 3, "244"),
    (2026, 8, 24, 4, "245"),
    (2026, 8, 24, 5, "246"),
    (2026, 8, 24, 6, "247"),
    (2026, 8, 24, 7, "248"),
    (2026, 8, 24, 8, "249"),
    # 2026-08-25 (screenshots 233-240)
    (2026, 8, 25, 1, "233"),
    (2026, 8, 25, 2, "234"),
    (2026, 8, 25, 3, "235"),
    (2026, 8, 25, 4, "236"),
    (2026, 8, 25, 5, "237"),
    (2026, 8, 25, 6, "238"),
    (2026, 8, 25, 7, "239"),
    (2026, 8, 25, 8, "240"),
    # 2026-08-26 (screenshots 222-232)
    (2026, 8, 26, 1, "232"),
    (2026, 8, 26, 2, "231"),
    (2026, 8, 26, 3, "230"),
    (2026, 8, 26, 4, "228"),
    (2026, 8, 26, 5, "226"),
    (2026, 8, 26, 6, "223"),
    (2026, 8, 26, 7, "224"),
    (2026, 8, 26, 8, "222"),
]


def main():
    results = []
    for year, month, day, qindex, label in PROBLEMS:
        try:
            results.append(process_problem(year, month, day, qindex, label))
            time.sleep(0.5)
        except Exception as e:
            print(f"  ERROR: {e}")

    # Save screenshot label -> qid mapping
    label_map = {f"q_{r['publicid']}": r['label'] for r in results}
    (OUT_DIR / "label_map.json").write_text(
        json.dumps(label_map, indent=2, ensure_ascii=False), encoding='utf-8'
    )

    # Build a pattern review
    review_path = REVIEW_DIR / "pattern_review.md"
    with open(review_path, "w", encoding='utf-8') as f:
        f.write("# 101围棋死活题模式分析\n\n")
        f.write(f"共提取 {len(results)} 道题目。\n\n")
        f.write("## 题目列表\n\n")
        f.write("| 截图 | Q号 | 初始黑/白 | 答案数 | 先手 |\n")
        f.write("|------|-----|-----------|--------|------|\n")
        for r in results:
            f.write(f"| {r['label']} | Q-{r['publicid']} | {len(r['content'][0])}/{len(r['content'][1])} | {len(r['answers'])} | {'黑' if r['blackfirst'] else '白'} |\n")
    print(f"Wrote review to {review_path}")


if __name__ == "__main__":
    main()
