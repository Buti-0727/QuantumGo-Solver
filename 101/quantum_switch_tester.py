#!/usr/bin/env python3
"""
QuantumGo 2-Stone Switch Difficulty Optimizer
=============================================
Evaluates all pairs (Black Stone b_i, White Stone w_j) switched to Quantum pieces
to find the configuration that maximizes game-state complexity, search expansion,
and entanglement cascade volatility.
"""

import math
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict, deque

# 9x9 standard coordinates
COORD_9X9_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J"]
SGF_LETTERS = "abcdefghjklmnopqrst"


def coord_to_9x9_str(col: int, row: int) -> str:
    """Convert (col, row) 0-indexed to 9x9 label e.g. (3, 2) -> 'D3'."""
    if 0 <= col < 9 and 0 <= row < 9:
        return f"{COORD_9X9_LETTERS[col]}{row + 1}"
    return "??"


def coord_to_sgf(col: int, row: int) -> str:
    """Convert (col, row) 0-indexed to SGF string e.g. (3, 2) -> 'dc'."""
    if 0 <= col < len(SGF_LETTERS) and 0 <= row < len(SGF_LETTERS):
        return f"{SGF_LETTERS[col]}{SGF_LETTERS[row]}"
    return "??"


def sgf_to_coord(sgf_str: str) -> Tuple[int, int]:
    """Convert SGF string e.g. 'dp' to (col, row) 0-indexed."""
    if len(sgf_str) >= 2 and sgf_str[0] in SGF_LETTERS and sgf_str[1] in SGF_LETTERS:
        return SGF_LETTERS.index(sgf_str[0]), SGF_LETTERS.index(sgf_str[1])
    return -1, -1


class BoardGraph:
    """Helper for Go tactical topology, liberties, and connected components."""

    def __init__(self, black: List[Tuple[int, int]], white: List[Tuple[int, int]], board_size: int = 9):
        self.board_size = board_size
        self.black = set(black)
        self.white = set(white)
        self.occupied = self.black | self.white

    def neighbors(self, c: int, r: int) -> List[Tuple[int, int]]:
        res = []
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < self.board_size and 0 <= nr < self.board_size:
                res.append((nc, nr))
        return res

    def get_group_and_liberties(self, start: Tuple[int, int]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        if start not in self.occupied:
            return set(), set()
        color = "B" if start in self.black else "W"
        target_set = self.black if color == "B" else self.white

        group = set()
        liberties = set()
        queue = deque([start])
        visited = {start}

        while queue:
            curr = queue.popleft()
            group.add(curr)
            for n in self.neighbors(curr[0], curr[1]):
                if n in target_set and n not in visited:
                    visited.add(n)
                    queue.append(n)
                elif n not in self.occupied:
                    liberties.add(n)
        return group, liberties


class QuantumSwitchOptimizer:
    """
    Exhaustively benchmarks all (b_i, w_j) candidate switches from classical Go to QuantumGo.
    """

    def __init__(self, problem: Dict[str, Any], board_size: int = 9):
        self.problem = problem
        self.board_size = board_size
        self.black = [tuple(p) for p in problem.get("initial_black", [])]
        self.white = [tuple(p) for p in problem.get("initial_white", [])]
        self.solution_moves = problem.get("solution_moves", [])
        self.first_player = problem.get("first_player", "B")
        self.vital_coord = self.solution_moves[0][1] if self.solution_moves else None

        self.bg = BoardGraph(self.black, self.white, self.board_size)

    def find_candidate_partner(self, coord: Tuple[int, int], color: str, excluded: Set[Tuple[int, int]]) -> Tuple[int, int]:
        """Find the optimal secondary coordinate on B2 for superposition partner."""
        c, r = coord
        occupied = (set(self.black) | set(self.white) | excluded) - {coord}

        # Prefer adjacent empty liberties or vital diagonal points
        candidates = []
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < self.board_size and 0 <= nr < self.board_size and (nc, nr) not in occupied:
                # prioritize points closer to vital move or opponent contact
                dist_vital = abs(nc - self.vital_coord[0]) + abs(nr - self.vital_coord[1]) if self.vital_coord else 9
                candidates.append(((nc, nr), dist_vital))

        if candidates:
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        # Fallback to any empty spot
        for nc in range(self.board_size):
            for nr in range(self.board_size):
                if (nc, nr) not in occupied:
                    return (nc, nr)
        return ((c + 1) % self.board_size, r)

    def evaluate_pair(self, b_stone: Tuple[int, int], w_stone: Tuple[int, int]) -> Dict[str, Any]:
        """
        Calculates multi-factor difficulty score D(b, w).
        """
        bc, br = b_stone
        wc, wr = w_stone

        b_partner = self.find_candidate_partner(b_stone, "B", {w_stone})
        w_partner = self.find_candidate_partner(w_stone, "W", {b_stone, b_partner})

        # 1. Base Tactical Criticality of individual stones
        b_group, b_libs = self.bg.get_group_and_liberties(b_stone)
        w_group, w_libs = self.bg.get_group_and_liberties(w_stone)

        b_adj_opp = sum(1 for n in self.bg.neighbors(bc, br) if n in self.bg.white)
        w_adj_opp = sum(1 for n in self.bg.neighbors(wc, wr) if n in self.bg.black)

        # Distance to vital move
        b_vital_dist = (abs(bc - self.vital_coord[0]) + abs(br - self.vital_coord[1])) if self.vital_coord else 9
        w_vital_dist = (abs(wc - self.vital_coord[0]) + abs(wr - self.vital_coord[1])) if self.vital_coord else 9

        # Tactical Vitality Score (V_vital)
        v_vital = 40.0
        v_vital += (b_adj_opp + w_adj_opp) * 12.0
        if b_vital_dist <= 1:
            v_vital += 30.0
        elif b_vital_dist <= 2:
            v_vital += 15.0

        if w_vital_dist <= 1:
            v_vital += 35.0
        elif w_vital_dist <= 2:
            v_vital += 20.0

        # 2. Entanglement Cascade Potential (C_cascade)
        # Low liberties mean atari triggers cross-board removal cascade immediately
        c_cascade = 20.0
        if len(b_libs) <= 2:
            c_cascade += (3 - len(b_libs)) * 25.0
        if len(w_libs) <= 2:
            c_cascade += (3 - len(w_libs)) * 25.0

        # Inter-stone distance (mutual interference between BQ and WQ)
        bw_dist = abs(bc - wc) + abs(br - wr)
        if bw_dist <= 1:
            c_cascade += 35.0  # Direct contact entanglement pair
            interference_desc = "Direct contact between Black Quantum and White Quantum stones."
        elif bw_dist <= 2:
            c_cascade += 20.0
            interference_desc = "Tight local proximity causing overlapping liberty contention."
        else:
            interference_desc = "Distributed cross-board perimeter influence."

        # 3. Search Tree Node Expansion (N_search)
        # Superposition creates 2^2 = 4 classical branch states: (B1,W1), (B1,W2), (B2,W1), (B2,W2)
        # Calculate divergence between board 1 and board 2 liberties
        b_p_group, b_p_libs = BoardGraph(list((set(self.black) - {b_stone}) | {b_partner}), self.white, self.board_size).get_group_and_liberties(b_partner)
        w_p_group, w_p_libs = BoardGraph(self.black, list((set(self.white) - {w_stone}) | {w_partner}), self.board_size).get_group_and_liberties(w_partner)

        liberty_delta_b = abs(len(b_libs) - len(b_p_libs))
        liberty_delta_w = abs(len(w_libs) - len(w_p_libs))

        branch_expansion = 1.0 + (liberty_delta_b * 0.45) + (liberty_delta_w * 0.45) + ((b_adj_opp + w_adj_opp) * 0.3)
        n_search = min(150.0, branch_expansion * 35.0)

        # 4. Branch Outcome Entropy (H_entropy)
        # High entropy when primary vs secondary placement yields different tactical life/death prospects
        state_probs = [0.25, 0.25, 0.25, 0.25]
        # Weight divergence by liberty deltas
        h_entropy = 2.0 * math.log2(2) * (1.0 + (liberty_delta_b + liberty_delta_w) * 0.25)
        h_entropy_score = min(60.0, h_entropy * 20.0)

        # Total Composite Difficulty
        total_score = round(v_vital + c_cascade + n_search + h_entropy_score, 1)

        # Tactical Rationale
        reasons = []
        if b_vital_dist <= 1 or w_vital_dist <= 1:
            reasons.append("Crucial vital point adjacency")
        if len(b_libs) <= 2 or len(w_libs) <= 2:
            reasons.append(f"High atari cascade sensitivity (B libs: {len(b_libs)}, W libs: {len(w_libs)})")
        if bw_dist <= 2:
            reasons.append("Direct cross-color quantum interference")
        if liberty_delta_b + liberty_delta_w >= 2:
            reasons.append("Large dual-board liberty disparity inducing deep search tree branching")

        rationale = "; ".join(reasons) if reasons else "Perimeter boundary superposition."

        return {
            "black_stone": {
                "coord_9x9": coord_to_9x9_str(bc, br),
                "coord_sgf": coord_to_sgf(bc, br),
                "xy": [bc, br],
                "partner_9x9": coord_to_9x9_str(b_partner[0], b_partner[1]),
                "partner_xy": list(b_partner),
                "liberties": len(b_libs),
            },
            "white_stone": {
                "coord_9x9": coord_to_9x9_str(wc, wr),
                "coord_sgf": coord_to_sgf(wc, wr),
                "xy": [wc, wr],
                "partner_9x9": coord_to_9x9_str(w_partner[0], w_partner[1]),
                "partner_xy": list(w_partner),
                "liberties": len(w_libs),
            },
            "difficulty_score": total_score,
            "metrics": {
                "tactical_vitality": round(v_vital, 1),
                "cascade_volatility": round(c_cascade, 1),
                "search_expansion": round(n_search, 1),
                "entropy_divergence": round(h_entropy_score, 1),
                "estimated_node_multiplier": round(branch_expansion * 2.8, 2),
            },
            "interference_desc": interference_desc,
            "rationale": rationale,
        }

    def evaluate_all(self) -> Dict[str, Any]:
        """
        Runs exhaustive evaluation over all |S_B| x |S_W| stone switch pairs.
        """
        results = []
        matrix = []

        b_labels = [coord_to_9x9_str(c, r) for c, r in self.black]
        w_labels = [coord_to_9x9_str(c, r) for c, r in self.white]

        for b_idx, b_stone in enumerate(self.black):
            row_scores = []
            for w_idx, w_stone in enumerate(self.white):
                res = self.evaluate_pair(b_stone, w_stone)
                results.append(res)
                row_scores.append(res["difficulty_score"])
            matrix.append(row_scores)

        results.sort(key=lambda x: x["difficulty_score"], reverse=True)
        top_switch = results[0] if results else None

        return {
            "total_pairs_tested": len(results),
            "black_stones_count": len(self.black),
            "white_stones_count": len(self.white),
            "black_labels": b_labels,
            "white_labels": w_labels,
            "difficulty_matrix": matrix,
            "top_switch": top_switch,
            "leaderboard": results[:5],
        }


def format_cli_report(eval_data: Dict[str, Any], problem_id: str = "custom") -> str:
    """Produces human-readable markdown report for the stone switch optimization."""
    top = eval_data.get("top_switch")
    if not top:
        return "No stone switches evaluated."

    lines = []
    lines.append(f"# QuantumGo 2-Stone Switch Optimization Report — Problem `{problem_id}`")
    lines.append(f"- **Combinatorial Search Space**: {eval_data['total_pairs_tested']} pairs ({eval_data['black_stones_count']} Black × {eval_data['white_stones_count']} White)")
    lines.append("")
    lines.append("## 🏆 Optimal 2-Stone Quantum Switch (Maximum Difficulty)")
    lines.append(f"- **Black Quantum Stone (BQ)**: `{top['black_stone']['coord_9x9']}` (SGF `{top['black_stone']['coord_sgf']}`) $\\rightarrow$ Superposed with `{top['black_stone']['partner_9x9']}`")
    lines.append(f"- **White Quantum Stone (WQ)**: `{top['white_stone']['coord_9x9']}` (SGF `{top['white_stone']['coord_sgf']}`) $\\rightarrow$ Superposed with `{top['white_stone']['partner_9x9']}`")
    lines.append(f"- **Max Quantum Difficulty Score**: **`{top['difficulty_score']}`** (Estimated Search Expansion: **`{top['metrics']['estimated_node_multiplier']}×`**)")
    lines.append(f"- **Tactical Rationale**: {top['rationale']}")
    lines.append("")
    lines.append("### Score Component Breakdown")
    lines.append(f"| Metric Component | Score Contribution | Detail |")
    lines.append(f"| :--- | :--- | :--- |")
    lines.append(f"| Tactical Vitality ($\\mathcal{{V}}$) | `{top['metrics']['tactical_vitality']}` | Mutual group contact & vital eye proximity |")
    lines.append(f"| Cascade Volatility ($\\mathcal{{C}}$) | `{top['metrics']['cascade_volatility']}` | Atari coupling & cross-board capture chain |")
    lines.append(f"| Search Tree Expansion ($\\mathcal{{N}}$) | `{top['metrics']['search_expansion']}` | Branch factor increase & legal move bifurcation |")
    lines.append(f"| Entropy Divergence ($\\mathcal{{H}}$) | `{top['metrics']['entropy_divergence']}` | Dual-board branch outcome uncertainty |")
    lines.append("")
    lines.append("## 📊 Top-5 Ranked Stone Switch Pairs")
    lines.append("| Rank | Black Stone | White Stone | Difficulty Score | Node Multiplier | Rationale |")
    lines.append("| :---: | :---: | :---: | :---: | :---: | :--- |")
    for idx, item in enumerate(eval_data.get("leaderboard", []), start=1):
        lines.append(
            f"| **#{idx}** | `{item['black_stone']['coord_9x9']}` | `{item['white_stone']['coord_9x9']}` | **`{item['difficulty_score']}`** | `{item['metrics']['estimated_node_multiplier']}×` | {item['rationale']} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Test and optimize 2-stone Quantum switch for Go positions.")
    parser.add_argument("--sgf", type=str, help="Path to SGF file to evaluate.")
    parser.add_argument("--json-out", type=str, help="Export result as JSON to path.")
    args = parser.parse_args()

    # Default fallback demo if no SGF provided
    if args.sgf and Path(args.sgf).exists():
        from quantum_tsumego_toolkit import process_complete_tsumego
        res = process_complete_tsumego(str(args.sgf))
        problem = res.get("problem_data", {})
    else:
        # Benchmark tsumego sample: 9x9 corner snapback
        problem = {
            "initial_black": [[4, 4], [5, 4], [6, 4], [4, 5], [6, 5], [5, 6], [6, 6]],
            "initial_white": [[6, 1], [6, 3], [7, 3], [7, 4], [6, 6], [6, 7], [7, 7]],
            "solution_moves": [("B", [6, 5]), ("W", [7, 5])],
            "first_player": "B",
        }

    optimizer = QuantumSwitchOptimizer(problem, board_size=9)
    eval_data = optimizer.evaluate_all()

    report = format_cli_report(eval_data, problem_id=Path(args.sgf).stem if args.sgf else "demo_tsumego")
    print(report)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved JSON evaluation to {args.json_out}")


if __name__ == "__main__":
    main()
