#!/usr/bin/env python3
"""
Batch Pipeline Runner for QuantumGo Tsumego Analysis.
Processes all problems in 101/ and outputs a consolidated report with A, B, C, D, E details.
"""

from pathlib import Path
import json
from quantum_tsumego_toolkit import process_complete_tsumego

ROOT = Path(__file__).parent.resolve()
SGF_DIR = ROOT / "extracted" / "sgf"
OUT_MD = ROOT / "extracted" / "review" / "quantum_tsumego_full_analysis.md"
LABEL_MAP_FILE = ROOT / "extracted" / "label_map.json"


def main():
    label_map = {}
    if LABEL_MAP_FILE.exists():
        label_map = json.loads(LABEL_MAP_FILE.read_text())

    sections = [
        "# QuantumGo 死活题全功能综合分析报告 (A–E 闭环)\n",
        "本报告展示了针对 101 题库死活题的五大核心功能处理结果：\n",
        "- **A. 信息提取 (Extraction)**: 棋盘网格、黑白子坐标与正解步骤序列提取\n",
        "- **B. 死活模式诊断 (Tsumego Patterns)**: 点眼破眼、缩小眼位、倒扑与扑、对杀紧气等模式分类\n",
        "- **C. 量子围棋转换 (Quantum Conversion)**: 将传统题型映射为叠加态 $|\\psi\\rangle = \\frac{1}{\\sqrt{2}}(|p_1\\rangle + |p_2\\rangle)$ 与纠缠图\n",
        "- **D. 量子难度灵敏度分析 (Quantum Difficulty)**: 评估将黑/白哪颗棋子或步骤变为量子手时难度最高\n",
        "- **E. 自动解题与验算 (Self-Solving Trace)**: 按照 1, 2, 3... 步骤推进、提子判定与 ASCII 终局展示\n\n",
        "---\n\n"
    ]

    sgf_files = sorted(SGF_DIR.glob("q_*.sgf"))
    for sgf in sgf_files:
        qid = sgf.stem
        label = label_map.get(qid, "-")
        res = process_complete_tsumego(str(sgf))

        pdata = res["problem_data"]
        pat = res["pattern_analysis"]
        qver = res["quantum_version"]
        diff = res["difficulty_analysis"]
        sol = res["solution_trace"]

        mb = diff["most_difficult_black_stone"]
        mw = diff["most_difficult_white_stone"]
        mm = diff["most_difficult_solution_move"]

        sections.append(f"## 题目 {qid} (截图编号: {label}) — {pdata['first_player']}先\n")
        sections.append(f"- **【B. 战术模式】**: `{pat['pattern_name']}` ({pat['region']})\n")
        sections.append(f"  - **要害急所**: `{', '.join(pat['vital_points'])}`\n")
        sections.append(f"  - **模式说明**: {pat['explanation']}\n")
        sections.append(f"- **【C. 量子围棋转换】**: 首手量子对 `{qver['quantum_moves'][0]['coord_a']}` 与 `{qver['quantum_moves'][0]['coord_b']}` 形成叠加态\n")
        sections.append(f"- **【D. 最大量子难度分析】**:\n")
        if mb:
            sections.append(f"  - **黑棋最具难度量子化棋子**: `{mb['coord']}` (难度分: {mb['difficulty_score']} - {mb['rationale']})\n")
        if mw:
            sections.append(f"  - **白棋最具难度量子化棋子**: `{mw['coord']}` (难度分: {mw['difficulty_score']} - {mw['rationale']})\n")
        if mm:
            sections.append(f"  - **最具分支难度的解题手**: 第 {mm['move_index']} 手 `{mm['coord']}` ({mm['impact']})\n")
        sections.append(f"- **【E. 解题与验证】**: {sol['status_text']}，共 {sol['total_steps']} 手\n")
        sections.append("```text\n")
        sections.append(sol["final_board_ascii"])
        sections.append("\n```\n\n---\n\n")

    OUT_MD.write_text("".join(sections), encoding="utf-8")
    print(f"Successfully wrote full analysis for {len(sgf_files)} problems to {OUT_MD}")


if __name__ == "__main__":
    main()
