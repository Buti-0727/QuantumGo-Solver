#!/usr/bin/env python3
"""
Scrapes brand-new daily problems from https://www.101weiqi.com/qday/
Extracts the complete multi-step answer sequences (1, 2, 3, 4, 5...) with both
attacker and defender branches (st=2 正解, st=1 变化, st=0 失败).
Saves new SGF and JSON files and updates the 9x9 QuantumGo registry.
"""

import sys
import re
import json
import base64
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
OUT_DIR = ROOT / "extracted"
SGF_DIR = OUT_DIR / "sgf"
JSON_DIR = OUT_DIR / "json"

SGF_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

SGF_LETTERS = "abcdefghjklmnopqrst"


def letter_to_index(ch: str) -> int:
    return ord(ch) - ord('a')


def to_sgf(coord: str, size: int = 19) -> str:
    if not coord or len(coord) != 2:
        return "tt"
    col_idx = letter_to_index(coord[0])
    row_idx = letter_to_index(coord[1])
    sgf_col = SGF_LETTERS[col_idx]
    sgf_row = SGF_LETTERS[(size - 1) - row_idx]
    return sgf_col + sgf_row


def decode_c(encoded: str, r: int) -> list:
    key = "101" + str(r + 1) * 3
    decoded = base64.b64decode(encoded)
    key_bytes = key.encode()
    out = []
    for i, b in enumerate(decoded):
        out.append(chr(b ^ key_bytes[i % len(key_bytes)]))
    return json.loads(''.join(out))


def fetch_links(page: int):
    url = f"https://www.101weiqi.com/qday/?page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8')
    links = sorted(list(set(re.findall(r'/qday/(\d+)/(\d+)/(\d+)/(\d+)/', html))))
    return [(int(y), int(m), int(d), int(q)) for y, m, d, q in links]


def fetch_qqdata(year: int, month: int, day: int, qindex: int):
    url = f"https://www.101weiqi.com/qday/{year}/{month}/{day}/{qindex}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8')
    m = re.search(r'var qqdata = (\{.*?\});\s*\n', html, re.DOTALL)
    if not m:
        return None
    return json.loads(m.group(1))


def build_sgf(publicid: int, content: list, answers: list, blackfirst: bool,
              size: int = 19, category: str = "TOLIVE") -> str:
    ab = [to_sgf(c, size) for c in content[0]]
    aw = [to_sgf(c, size) for c in content[1]]
    turn = "B" if blackfirst else "W"

    correct = [a for a in answers if a.get('st') == 2]
    variations = [a for a in answers if a.get('st') == 1]
    failed = [a for a in answers if a.get('st') == 0]

    # Select comprehensive multi-step correct answer
    main = max(correct, key=lambda a: len(a.get('pts', []))) if correct else (answers[0] if answers else None)

    def answer_to_sgf(answer: dict, label: str) -> str:
        nodes = []
        color = turn
        for pt in answer['pts']:
            coord = to_sgf(pt['p'], size)
            nodes.append(f";{color}[{coord}]")
            color = "W" if color == "B" else "B"
        return ''.join(nodes) + f"N[{label}]"

    branch_nodes = []
    if main:
        branch_nodes.append("(" + answer_to_sgf(main, "正解") + ")")
    for ans in correct:
        if ans != main:
            branch_nodes.append("(" + answer_to_sgf(ans, f"正解变例{ans.get('nu', '')}") + ")")
    for ans in variations[:4]:
        branch_nodes.append("(" + answer_to_sgf(ans, f"变化{ans.get('nu', '')}") + ")")
    for ans in failed[:2]:
        branch_nodes.append("(" + answer_to_sgf(ans, f"失败{ans.get('nu', '')}") + ")")

    header = f"(;GM[1]FF[4]CA[UTF-8]SZ[{size}]GN[Q-{publicid}]PL[{turn}]"
    if category:
        header += f"GC[{category}]"
    if ab:
        header += "AB" + ''.join(f"[{c}]" for c in ab)
    if aw:
        header += "AW" + ''.join(f"[{c}]" for c in aw)

    if branch_nodes:
        return header + '\n' + '\n'.join(branch_nodes) + ")"
    return header + ")"


def main(target_new_problems: int = 15):
    existing = {p.stem for p in SGF_DIR.glob("q_*.sgf")}
    print(f"Current existing problems in database: {len(existing)}")

    new_extracted = 0
    for page in range(2, 6):
        if new_extracted >= target_new_problems:
            break
        print(f"Fetching 101weiqi catalog page {page}...")
        try:
            items = fetch_links(page)
        except Exception as e:
            print(f"  Error loading page {page}: {e}")
            continue

        for y, m, d, q in items:
            if new_extracted >= target_new_problems:
                break
            try:
                data = fetch_qqdata(y, m, d, q)
                if not data:
                    continue
                pid = data.get("publicid") or data.get("id")
                stem = f"q_{pid}"
                if stem in existing:
                    continue

                content = decode_c(data["c"], data["r"])
                answers = data.get("answers", [])
                blackfirst = bool(data.get("blackfirst", True))
                cat = data.get("type", "TOLIVE")

                sgf_text = build_sgf(pid, content, answers, blackfirst, size=19, category=cat)
                (SGF_DIR / f"{stem}.sgf").write_text(sgf_text, encoding="utf-8")
                (JSON_DIR / f"{stem}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

                existing.add(stem)
                new_extracted += 1

                # Show extracted multi-step solution
                correct_answers = [a for a in answers if a.get('st') == 2]
                longest_seq = max((len(a.get('pts', [])) for a in correct_answers), default=0)
                print(f"  [+] Extracted Q-{pid}: {len(content[0])}B/{len(content[1])}W, {len(answers)} answer branches (Max Correct Steps: {longest_seq})")
                time.sleep(0.3)
            except Exception as err:
                print(f"  [-] Skip ({y}/{m}/{d} #{q}): {err}")

    print(f"\nCompleted: Extracted {new_extracted} new problems with multi-step solution sequences.")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    main(count)
