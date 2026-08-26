#!/usr/bin/env python3
"""Render initial position + main correct answer for all 101weiqi problems."""

import re
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.resolve()
SGF_DIR = ROOT / "extracted" / "sgf"
JSON_DIR = ROOT / "extracted" / "json"
OUT = ROOT / "extracted" / "review" / "solutions_text.md"
LABEL_MAP = ROOT / "extracted" / "label_map.json"

SGF_LETTERS = "abcdefghjklmnopqrst"


def sgf_to_idx(coord):
    return (SGF_LETTERS.index(coord[0]), SGF_LETTERS.index(coord[1]))


def parse_sgf(sgf):
    ab = re.findall(r'AB((?:\[[a-z]{2}\])*)', sgf)
    aw = re.findall(r'AW((?:\[[a-z]{2}\])*)', sgf)
    black = set()
    white = set()
    for grp in ab:
        for c in re.findall(r'\[([a-z]{2})\]', grp):
            black.add(sgf_to_idx(c))
    for grp in aw:
        for c in re.findall(r'\[([a-z]{2})\]', grp):
            white.add(sgf_to_idx(c))

    branches = re.findall(r'\((;[BW]\[[a-z]{2}\][^)]*?)\)', sgf)
    parsed_branches = []
    for branch_text in branches:
        label_match = re.search(r'N\[([^\]]*)\]', branch_text)
        label = label_match.group(1) if label_match else ""
        seq = re.findall(r';([BW])\[([a-z]{2})\]', branch_text)
        parsed_branches.append({"label": label, "moves": seq})
    return black, white, parsed_branches


def render_board(black, white, moves, size=19, crop_margin=2):
    """Render a compact ASCII board with initial stones and numbered answer moves."""
    # Compute occupied region to crop
    all_pts = black | white | {sgf_to_idx(c) for _, c in moves}
    if not all_pts:
        return "(empty)"
    cols = [c for c, _ in all_pts]
    rows = [r for _, r in all_pts]
    c0, c1 = max(0, min(cols) - crop_margin), min(size - 1, max(cols) + crop_margin)
    r0, r1 = max(0, min(rows) - crop_margin), min(size - 1, max(rows) + crop_margin)

    # Place initial stones
    board = {}
    for c, r in black:
        board[(c, r)] = 'X'
    for c, r in white:
        board[(c, r)] = 'O'

    # Numbered answer moves (1-based); later moves overwrite earlier ones if
    # they happen to land on the same point (rare in life-and-death answers).
    for i, (color, coord) in enumerate(moves, start=1):
        idx = sgf_to_idx(coord)
        board[idx] = str(i)

    # Build output
    header = '   ' + ' '.join(SGF_LETTERS[c] for c in range(c0, c1 + 1))
    lines = [header]
    for r in range(r0, r1 + 1):
        row = [board.get((c, r), '.') for c in range(c0, c1 + 1)]
        lines.append(f'{SGF_LETTERS[r]:2} ' + ' '.join(row))
    return '\n'.join(lines)


def main():
    label_map = json.loads(LABEL_MAP.read_text()) if LABEL_MAP.exists() else {}

    sections = []
    sections.append("# 101围棋死活题 - 初始局面与正解进程\n")
    sections.append("""
每道题给出：
- 题号（Q-xxx）与对应截图编号；
- 缩小的 ASCII 棋盘，`.` 为空点，`X` 为黑子，`O` 为白子，数字 `1/2/3...`
  为正解进程的落子顺序（奇数为该题先手方，偶数为对方）。

> 注：SGF 坐标为标准 19×19（a–t，跳过 i），y=0 在上方。网站 viewers
> 可能旋转截图，因此截图方向与 ASCII 棋盘的角落方向不一定完全一致。
""")

    for sgf_path in sorted(SGF_DIR.glob("q_*.sgf")):
        sgf = sgf_path.read_text()
        black, white, branches = parse_sgf(sgf)
        if not branches:
            continue
        main = next((b for b in branches if b["label"] == "正解"), branches[0])
        qid = sgf_path.stem
        label = label_map.get(qid, "-")

        # Determine first mover from PL property or first move
        pl_match = re.search(r'PL\[([BW])\]', sgf)
        first_color = pl_match.group(1) if pl_match else (main["moves"][0][0] if main["moves"] else "B")
        first_color_name = "黑" if first_color == "B" else "白"

        seq_str = " → ".join(f"{c}[{pt}]" for c, pt in main["moves"])
        sections.append(f"\n## 截图 {label} — {qid}（{first_color_name}先，正解 {len(main['moves'])} 手）\n")
        sections.append(f"**正解进程**：{seq_str}\n")
        sections.append("```text\n")
        sections.append(render_board(black, white, main["moves"]))
        sections.append("\n```\n")

    OUT.write_text(''.join(sections), encoding='utf-8')
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
