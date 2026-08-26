#!/usr/bin/env python3
"""Analyze extracted 101weiqi SGFs and write a pattern review."""

import re
import json
from pathlib import Path
from collections import Counter, defaultdict


ROOT = Path(__file__).parent.resolve()
SGF_DIR = ROOT / "extracted" / "sgf"
JSON_DIR = ROOT / "extracted" / "json"
OUT = ROOT / "extracted" / "review" / "pattern_review.md"

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

    # Branches are top-level variations from the initial position, e.g.:
    #   (;B[rp];W[tp]N[正解])
    # Capture everything between the opening '(;' and the closing ')', then
    # extract each move node (;COLOR[coord]).
    branches = re.findall(r'\((;[BW]\[[a-z]{2}\][^)]*?)\)', sgf)
    parsed_branches = []
    for branch_text in branches:
        label_match = re.search(r'N\[([^\]]*)\]', branch_text)
        label = label_match.group(1) if label_match else ""
        seq = re.findall(r';([BW])\[([a-z]{2})\]', branch_text)
        parsed_branches.append({"label": label, "moves": seq})
    return black, white, parsed_branches


def classify_region(black, white):
    all_stones = black | white
    if not all_stones:
        return "unknown"
    xs = [c for c, _ in all_stones]
    ys = [r for _, r in all_stones]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    # Region based on bounding box and edges
    touches_top = miny < 3
    touches_bottom = maxy > 15
    touches_left = minx < 3
    touches_right = maxx > 15
    if (touches_left and touches_top) or (touches_right and touches_top) or \
       (touches_left and touches_bottom) or (touches_right and touches_bottom):
        return "corner"
    elif touches_top or touches_bottom or touches_left or touches_right:
        return "side"
    return "center"


def main():
    stats = {
        "total": 0,
        "regions": Counter(),
        "first_moves": Counter(),
        "answer_lengths": [],
        "black_first": 0,
        "white_first": 0,
    }
    per_problem = []
    # Map publicid -> screenshot label from the fetcher output if available.
    label_map = {}
    label_file = ROOT / "extracted" / "label_map.json"
    if label_file.exists():
        label_map = json.loads(label_file.read_text())

    for sgf_path in sorted(SGF_DIR.glob("q_*.sgf")):
        sgf = sgf_path.read_text()
        black, white, branches = parse_sgf(sgf)
        if not branches:
            print(f"  WARN: no branches found in {sgf_path.name}")
            continue
        # Prefer the branch labeled 正解 as the main answer; otherwise first branch.
        main = next((b for b in branches if b["label"] == "正解"), branches[0])
        first_move = main["moves"][0] if main["moves"] else (None, None)
        region = classify_region(black, white)
        stats["total"] += 1
        stats["regions"][region] += 1
        stats["answer_lengths"].append(len(main["moves"]))
        stats["first_moves"][first_move[1]] += 1
        is_black = first_move[0] == "B"
        if is_black:
            stats["black_first"] += 1
        else:
            stats["white_first"] += 1

        json_path = JSON_DIR / sgf_path.name.replace(".sgf", ".json")
        qid = sgf_path.stem
        screenshot = label_map.get(qid)
        if json_path.exists():
            data = json.loads(json_path.read_text())
            qid = data.get("filename", qid).replace(".sgf", "")

        per_problem.append({
            "qid": qid,
            "screenshot": screenshot or "-",
            "region": region,
            "first": first_move,
            "length": len(main["moves"]),
            "stones": f"{len(black)}B/{len(white)}W",
            "main_seq": main["moves"],
        })

    avg_len = sum(stats["answer_lengths"]) / len(stats["answer_lengths"]) if stats["answer_lengths"] else 0

    lines = []
    lines.append("# 101围棋死活题提取与模式分析\n")
    lines.append("## 概述\n")
    lines.append(f"- 截图总数：27 张\n")
    lines.append(f"- 唯一题目：{stats['total']} 道\n")
    lines.append(f"- 先手：黑棋 {stats['black_first']} 道，白棋 {stats['white_first']} 道\n")
    lines.append(f"- 平均正解手数：{avg_len:.1f}\n")
    lines.append("")
    lines.append("## 区域分布\n")
    for region, count in stats["regions"].most_common():
        lines.append(f"- {region}: {count} 道\n")
    lines.append("")
    lines.append("## 第一手常见落点（正解）\n")
    for move, count in stats["first_moves"].most_common(15):
        lines.append(f"- `{move}`: {count} 次\n")
    lines.append("")
    lines.append("## 题目明细\n")
    lines.append("| 截图 | 题目 | 区域 | 正解首手 | 正解长度 | 正解进程 | 初始子数 |\n")
    lines.append("|------|------|------|----------|----------|----------|----------|\n")
    for p in per_problem:
        color, coord = p["first"]
        seq_str = " → ".join(f"{c}[{pt}]" for c, pt in p["main_seq"])
        lines.append(f"| {p['screenshot']} | {p['qid']} | {p['region']} | {color}[{coord}] | {p['length']} | {seq_str} | {p['stones']} |\n")
    lines.append("")
    lines.append("## 说明\n")
    lines.append("- 截图编号对应 `101/Weixin Image_*_<编号>_8.png`。\n")
    lines.append("- 27 张截图中只有 24 道唯一题目；同题不同答案标签的截图会指向同一道 Q 题。\n")
    lines.append("- SGF 采用标准 19×19 坐标（a–t，跳过 i）。实际截图中的棋盘可能经过网站 viewers 的旋转，\n")
    lines.append("  因此截图中的「上下左右」与 SGF 的固定角位（如右下角）不一定完全一致，请以 SGF 中的坐标为准。\n")
    lines.append("- 正解进程里的 `B[坐标]` / `W[坐标]` 就是截图上标有数字的落子顺序。\n")
    lines.append("")
    lines.append("## 常见解题模式\n")
    lines.append("""
1. **缩小眼位 (Eye-space reduction)**：第一手常下在对方棋形要害，
   压缩做活空间。在边角题中，第一手多在第二线或第三线的急所。
2. **扑与倒扑 (Throw-in / Snapback)**：当对方棋形气紧时，利用扑入
   制造劫材或让对方自紧一气。
3. **对杀与紧气 (Capturing race)**：部分题目属于对杀题，关键是
   先收紧对方的气，注意公气与眼形。
4. **靠与扳 (Hane / Bump)**：在边角做活/杀棋时，靠、扳、断是
   常见手段，用于制造破绽或扩大眼位。
5. **劫争 (Ko)**：少数题目正确解包含劫争，需要在后续变化中保留
   劫材。
6. **变化与失败图**：每题都附带多个变化图和失败图，学习时应
   对比正解与失败图的差异，理解"为什么这手棋不对"。
""")
    lines.append("\n## 文件输出\n")
    lines.append("- `extracted/sgf/`：每题一个 `.sgf`，包含初始局面和正解/变化/失败分支。\n")
    lines.append("- `extracted/json/`：每题一个 `.json`，兼容 `study-LD-RZ-solver` 的 `rawsgf` 字段。\n")

    OUT.write_text(''.join(lines), encoding='utf-8')
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
