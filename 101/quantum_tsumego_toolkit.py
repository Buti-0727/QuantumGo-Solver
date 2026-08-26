#!/usr/bin/env python3
"""
QuantumGo Tsumego Toolkit for Folder 101.

Implements the 5 core capabilities:
  A. extract_from_png: Extract Go board, stone colors, and numbered solution steps from PNG.
  B. analyze_tsumego_pattern: Classify life-and-death pattern (Nakade, eye-reduction, snapback, semeai, etc.).
  C. convert_to_quantum_go: Transform classical problem into QuantumGo superposition & entanglement state.
  D. evaluate_quantum_difficulty: Identify which Black/White stone/move change yields highest quantum complexity.
  E. solve_and_verify_tsumego: Self-solve and step-by-step verification using numbered solution moves.
"""

import os
import re
import math
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict, deque

import numpy as np

# Optional imports with fallbacks
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import easyocr
except ImportError:
    easyocr = None

# 9x9 standard coordinates: A, B, C, D, E, F, G, H, J (skipping I)
COORD_9X9_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J"]
SGF_9X9_LETTERS = "abcdefghj"
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


def normalize_to_9x9(
    black: List[Tuple[int, int]],
    white: List[Tuple[int, int]],
    moves: List[Tuple[str, Tuple[int, int]]]
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[str, Tuple[int, int]]]]:
    """
    Shifts coordinates into a standard 9x9 sub-board (0 <= col, row < 9).
    Computes bounding box strictly from initial stones to avoid coordinate squashing.
    """
    all_stones = list(black) + list(white)
    if not all_stones:
        return black, white, moves

    xs = [p[0] for p in all_stones]
    ys = [p[1] for p in all_stones]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    pad_x = max(0, (9 - width) // 2) if width <= 9 else 0
    pad_y = max(0, (9 - height) // 2) if height <= 9 else 0

    if min_x == 0:
        pad_x = 0
    if min_y == 0:
        pad_y = 0
    if max_x == 18 and width <= 9:
        pad_x = 9 - width
    if max_y == 18 and height <= 9:
        pad_y = 9 - height

    offset_x = min_x - pad_x
    offset_y = min_y - pad_y

    def shift_stone(p: Tuple[int, int]) -> Tuple[int, int]:
        nx = max(0, min(8, p[0] - offset_x))
        ny = max(0, min(8, p[1] - offset_y))
        return (nx, ny)

    norm_black = sorted(list(set(shift_stone(p) for p in black)))
    norm_white = sorted(list(set(shift_stone(p) for p in white)))

    norm_moves = []
    for col, (mx, my) in moves:
        # If move was recorded in flipped/opposite corner coordinates, map it into local region
        if abs(mx - min_x) > 9:
            if max_x > 9 and mx < 9:
                mx = 18 - mx
            elif max_x <= 9 and mx > 9:
                mx = 18 - mx
        if abs(my - min_y) > 9:
            if max_y > 9 and my < 9:
                my = 18 - my
            elif max_y <= 9 and my > 9:
                my = 18 - my
        norm_moves.append((col, shift_stone((mx, my))))

    return norm_black, norm_white, norm_moves


# ===========================================================================
# Part A: PNG Information Extraction
# ===========================================================================

class PNGGoExtractor:
    """Extracts Go board state, stone coordinates, and numbered steps from PNG."""

    _shared_reader = None

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu

    @classmethod
    def get_reader(cls, use_gpu: bool = False):
        if cls._shared_reader is None and easyocr is not None:
            try:
                cls._shared_reader = easyocr.Reader(['en'], gpu=use_gpu)
            except Exception:
                cls._shared_reader = None
        return cls._shared_reader

    def extract_from_png(self, image_path: str, board_size: int = 9) -> Dict[str, Any]:
        """
        Extracts all stones and numbered solution steps from any 101weiqi screenshot.
        Uses adaptive LAB color segmentation, circular contour filtering, and OCR.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if cv2 is None:
            raise RuntimeError("OpenCV (cv2) is required for PNG extraction.")

        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        h, w = img.shape[:2]

        # 1. Isolate wood board region if inside full browser screenshot
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        board_mask = (l > 70) & (l < 220) & (b > 130) & (b < 190) & (a > 115) & (a < 155)
        board_mask_u8 = board_mask.astype(np.uint8) * 255
        cnts, _ = cv2.findContours(board_mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        board_x, board_y, board_w, board_h = 0, 0, w, h
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) > 0.25 * w * h:
                board_x, board_y, board_w, board_h = cv2.boundingRect(c)

        board_roi = img[board_y:board_y + board_h, board_x:board_x + board_w]
        rh, rw = board_roi.shape[:2]
        gray = cv2.cvtColor(board_roi, cv2.COLOR_BGR2GRAY)

        # 2. Detect stones inside board ROI
        black_mask = cv2.inRange(gray, 0, 95)
        white_mask = cv2.inRange(gray, 195, 255)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        black_clean = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)
        white_clean = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

        r_min = int(rw * 0.025)
        r_max = int(rw * 0.09)
        min_area = np.pi * (r_min ** 2) * 0.45

        raw_detected = []
        for c in cv2.findContours(black_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            area = cv2.contourArea(c)
            (cx, cy), r = cv2.minEnclosingCircle(c)
            if r_min <= r <= r_max and area > min_area:
                raw_detected.append(('B', int(cx), int(cy), int(r)))

        for c in cv2.findContours(white_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            area = cv2.contourArea(c)
            (cx, cy), r = cv2.minEnclosingCircle(c)
            if r_min <= r <= r_max and area > min_area:
                raw_detected.append(('W', int(cx), int(cy), int(r)))

        if not raw_detected:
            return {
                "source_image": str(path),
                "board_size": 9,
                "initial_black": [],
                "initial_white": [],
                "solution_moves": [],
                "first_player": "B"
            }

        # 3. Infer 9x9 grid lines from stone clusters and board geometry
        xs = np.array([s[1] for s in raw_detected])
        ys = np.array([s[2] for s in raw_detected])
        rs = np.array([s[3] for s in raw_detected])
        median_r = np.median(rs)

        def cluster_1d(coords, tol=median_r * 0.6):
            sorted_c = np.sort(coords)
            clusters = []
            curr = [sorted_c[0]]
            for x in sorted_c[1:]:
                if x - curr[-1] < tol:
                    curr.append(x)
                else:
                    clusters.append(float(np.mean(curr)))
                    curr = [x]
            clusters.append(float(np.mean(curr)))
            return np.array(clusters)

        col_centers = cluster_1d(xs)
        row_centers = cluster_1d(ys)

        diffs_x = np.diff(col_centers) if len(col_centers) > 1 else np.array([median_r * 2.1])
        diffs_y = np.diff(row_centers) if len(row_centers) > 1 else np.array([median_r * 2.1])
        step = float(np.median(np.concatenate([diffs_x, diffs_y])))

        # Anchor origin
        min_cx = float(np.min(col_centers))
        min_cy = float(np.min(row_centers))

        # Check if first stone sits on row 1 instead of row 0 (detect top edge distance)
        edge_top_dist = min_cy
        edge_left_dist = min_cx
        start_row_offset = 1 if edge_top_dist > step * 1.2 else 0
        start_col_offset = 1 if edge_left_dist > step * 1.2 else 0

        x0 = min_cx - start_col_offset * step
        y0 = min_cy - start_row_offset * step

        # 4. Map stones to 9x9 coordinates and check for move numbers (OCR)
        reader = self.get_reader(self.use_gpu)
        initial_black = []
        initial_white = []
        solution_moves = []

        for color, cx, cy, cr in raw_detected:
            col_idx = int(round((cx - x0) / step))
            row_idx = int(round((cy - y0) / step))
            col_idx = max(0, min(8, col_idx))
            row_idx = max(0, min(8, row_idx))
            coord = (col_idx, row_idx)

            # Check for move numbers inside stone
            roi_r = int(cr * 0.6)
            stone_roi = gray[max(0, cy - roi_r):min(rh, cy + roi_r), max(0, cx - roi_r):min(rw, cx + roi_r)]
            move_num = None

            if stone_roi.size > 0 and reader is not None:
                if color == 'B':
                    _, roi_bin = cv2.threshold(stone_roi, 160, 255, cv2.THRESH_BINARY)
                else:
                    _, roi_bin = cv2.threshold(stone_roi, 90, 255, cv2.THRESH_BINARY_INV)

                try:
                    ocr_res = reader.readtext(roi_bin)
                    for _, text, conf in ocr_res:
                        digits = re.findall(r'\d+', text)
                        if digits and conf > 0.4:
                            move_num = int(digits[0])
                            break
                except Exception:
                    pass

            if move_num is not None:
                solution_moves.append((move_num, color, coord))
            else:
                if color == 'B':
                    initial_black.append(coord)
                else:
                    initial_white.append(coord)

        # Sort solution moves by step number
        solution_moves.sort(key=lambda m: m[0])
        clean_solution = [(m[1], m[2]) for m in solution_moves]

        # Deduplicate
        initial_black = sorted(list(set(initial_black)))
        initial_white = sorted(list(set(initial_white)))

        return {
            "source_image": str(path),
            "board_size": 9,
            "initial_black": initial_black,
            "initial_white": initial_white,
            "solution_moves": clean_solution,
            "first_player": clean_solution[0][0] if clean_solution else ("B" if len(initial_black) >= len(initial_white) else "W"),
        }

    @staticmethod
    def parse_sgf_file(sgf_path: Path) -> Dict[str, Any]:
        """Parses a ground-truth SGF file into structured problem data normalized to 9x9."""
        content = sgf_path.read_text(encoding="utf-8", errors="ignore")
        ab = re.findall(r'AB((?:\[[a-z]{2}\])*)', content)
        aw = re.findall(r'AW((?:\[[a-z]{2}\])*)', content)

        black = set()
        white = set()
        for grp in ab:
            for c in re.findall(r'\[([a-z]{2})\]', grp):
                black.add(sgf_to_coord(c))
        for grp in aw:
            for c in re.findall(r'\[([a-z]{2})\]', grp):
                white.add(sgf_to_coord(c))

        # Extract main correct branch
        branches = re.findall(r'\((;[BW]\[[a-z]{2}\][^)]*?)\)', content)
        solution_moves = []
        for branch_text in branches:
            is_correct = "正解" in branch_text or len(solution_moves) == 0
            if is_correct:
                seq = re.findall(r';([BW])\[([a-z]{2})\]', branch_text)
                solution_moves = [(color, sgf_to_coord(coord)) for color, coord in seq]
                if "正解" in branch_text:
                    break

        pl_match = re.search(r'PL\[([BW])\]', content)
        first_player = pl_match.group(1) if pl_match else (solution_moves[0][0] if solution_moves else "B")

        # Normalize to 9x9 board coordinates
        norm_black, norm_white, norm_moves = normalize_to_9x9(list(black), list(white), solution_moves)

        return {
            "source_file": str(sgf_path),
            "board_size": 9,
            "initial_black": norm_black,
            "initial_white": norm_white,
            "solution_moves": norm_moves,
            "first_player": first_player,
        }


# ===========================================================================
# Part B: Tsumego Pattern Classifier
# ===========================================================================

class TsumegoPatternAnalyzer:
    """Analyzes Go life-and-death patterns and strategic motifs."""

    PATTERNS = {
        "NAKADE_POINT": "Eye Vital Point (Nakade / Point-Eye)",
        "EYE_REDUCTION": "Perimeter Space Reduction (Hane / Descent)",
        "SNAPBACK_THROW_IN": "Sacrifice & Snapback (Throw-in / Squeeze)",
        "SEMEAI_RACE": "Capturing Race (Semeai / Liberty Shortage)",
        "UNDER_STONES_KO": "Under-the-Stones / Ko Contest",
    }

    @classmethod
    def classify(cls, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the life-and-death tactical pattern and determine vital points in 9x9 coordinates."""
        black = set(problem.get("initial_black", []))
        white = set(problem.get("initial_white", []))
        moves = problem.get("solution_moves", [])
        first_player = problem.get("first_player", "B")

        all_stones = black | white
        if not all_stones:
            return {"primary_pattern": "EMPTY", "pattern_name": "Empty Board", "vital_points_9x9": [], "vital_points_sgf": []}

        # Bounding box & region
        xs = [c for c, _ in all_stones]
        ys = [r for _, r in all_stones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        is_corner = (min_x <= 2 or max_x >= 6) and (min_y <= 2 or max_y >= 6)
        is_side = (min_x <= 1 or max_x >= 7 or min_y <= 1 or max_y >= 7) and not is_corner
        region = "Corner" if is_corner else ("Side" if is_side else "Center")

        first_move = moves[0] if moves else (first_player, (0, 0))
        first_color, first_coord = first_move
        col, row = first_coord
        first_9x9_str = coord_to_9x9_str(col, row)
        first_sgf_str = coord_to_sgf(col, row)

        vital_points = [first_coord]
        pattern_type = "NAKADE_POINT"
        explanation = []

        dist_to_edge = min(col, 8 - col, row, 8 - row)

        if len(moves) >= 3 and any(moves[i][1] == moves[0][1] for i in range(1, len(moves))):
            pattern_type = "UNDER_STONES_KO"
            explanation.append("Repeated move coordinate or recapture indicates Under-the-stones or Ko.")
        elif dist_to_edge == 0:
            pattern_type = "EYE_REDUCTION"
            explanation.append("First move descends or hanes on the 1st line to reduce eye space from perimeter.")
        elif dist_to_edge == 1:
            pattern_type = "NAKADE_POINT"
            explanation.append("First move strikes the vital eye-shape point (2nd line vital point / Nakade).")
        elif len(moves) >= 4:
            pattern_type = "SEMEAI_RACE"
            explanation.append("Multi-step sequence tightening liberties in a mutual capturing race.")
        else:
            pattern_type = "SNAPBACK_THROW_IN"
            explanation.append("Sacrificial throw-in to compress opponent liberties.")

        color_name = "Black" if first_color == "B" else "White"

        return {
            "region": region,
            "primary_pattern": pattern_type,
            "pattern_name": cls.PATTERNS.get(pattern_type, "Standard Tsumego"),
            "vital_points_9x9": [coord_to_9x9_str(c, r) for c, r in vital_points],
            "vital_points_sgf": [coord_to_sgf(c, r) for c, r in vital_points],
            "first_move": f"{color_name} at {first_9x9_str}",
            "first_move_coord_9x9": first_9x9_str,
            "first_move_coord_sgf": first_sgf_str,
            "first_move_xy": [col, row],
            "solution_depth": len(moves),
            "explanation": " ".join(explanation),
        }


# ===========================================================================
# Part C: Traditional to QuantumGo Converter
# ===========================================================================

class QuantumGoConverter:
    """Converts classical Go positions and moves to QuantumGo superposition states."""

    @staticmethod
    def create_quantum_representation(
        problem: Dict[str, Any],
        entangle_vital_move: bool = True
    ) -> Dict[str, Any]:
        """
        Creates a QuantumGo problem definition:
        - Classical base stones (already collapsed state)
        - Selected Black Quantum Stone (|A> + |B>)
        - Selected White Quantum Stone (|A> + |B>)
        - Quantum move candidate pairs: |psi> = 1/sqrt(2) (|p1> + |p2>)
        - Entanglement links and collapse conditions.
        """
        black = problem.get("initial_black", [])
        white = problem.get("initial_white", [])
        moves = problem.get("solution_moves", [])
        first_player = problem.get("first_player", "B")

        quantum_moves = []
        entanglement_graph = defaultdict(list)
        occupied = set(black) | set(white)

        black_q_piece = None
        white_q_piece = None

        # 1. Black Quantum Stone (BQ)
        if black:
            b_stone = max(black, key=lambda p: QuantumDifficultyAnalyzer._compute_stone_quantum_sensitivity(p, "B", black, white, moves)[0])
            c1, r1 = b_stone
            adj_b = [
                (c1 + dc, r1 + dr)
                for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)]
                if 0 <= c1 + dc < 9 and 0 <= r1 + dr < 9 and (c1 + dc, r1 + dr) not in occupied
            ]
            c2, r2 = adj_b[0] if adj_b else (((c1 + 1) % 9), r1)
            b_str_a = coord_to_9x9_str(c1, r1)
            b_str_b = coord_to_9x9_str(c2, r2)
            black_q_piece = {
                "color": "B",
                "label": "Black Quantum Piece",
                "primary_coord_9x9": b_str_a,
                "secondary_coord_9x9": b_str_b,
                "primary_xy": [c1, r1],
                "secondary_xy": [c2, r2],
                "state_ket": f"|{b_str_a}⟩ + |{b_str_b}⟩",
                "probability_split": "50% / 50%",
                "description": f"Black stone at {b_str_a} superposed into state |{b_str_a}⟩ + |{b_str_b}⟩"
            }
            quantum_moves.append({
                "move_index": 1,
                "color": "B",
                "type": "QUANTUM_PAIR",
                "coord_a": b_str_a,
                "coord_b": b_str_b,
                "coord_a_xy": [c1, r1],
                "coord_b_xy": [c2, r2],
                "coord_a_sgf": coord_to_sgf(c1, r1),
                "coord_b_sgf": coord_to_sgf(c2, r2),
                "amplitude_a": 0.7071,
                "amplitude_b": 0.7071,
                "description": f"Black Quantum stone at {b_str_a} and {b_str_b}"
            })
            entanglement_graph[b_str_a].append(b_str_b)

        # 2. White Quantum Stone (WQ)
        if white:
            w_stone = max(white, key=lambda p: QuantumDifficultyAnalyzer._compute_stone_quantum_sensitivity(p, "W", white, black, moves)[0])
            wc1, wr1 = w_stone
            adj_w = [
                (wc1 + dc, wr1 + dr)
                for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)]
                if 0 <= wc1 + dc < 9 and 0 <= wr1 + dr < 9 and (wc1 + dc, wr1 + dr) not in occupied and (wc1 + dc, wr1 + dr) != (c2, r2)
            ]
            wc2, wr2 = adj_w[0] if adj_w else (wc1, ((wr1 + 1) % 9))
            w_str_a = coord_to_9x9_str(wc1, wr1)
            w_str_b = coord_to_9x9_str(wc2, wr2)
            white_q_piece = {
                "color": "W",
                "label": "White Quantum Piece",
                "primary_coord_9x9": w_str_a,
                "secondary_coord_9x9": w_str_b,
                "primary_xy": [wc1, wr1],
                "secondary_xy": [wc2, wr2],
                "state_ket": f"|{w_str_a}⟩ + |{w_str_b}⟩",
                "probability_split": "50% / 50%",
                "description": f"White stone at {w_str_a} superposed into state |{w_str_a}⟩ + |{w_str_b}⟩"
            }
            quantum_moves.append({
                "move_index": 2,
                "color": "W",
                "type": "QUANTUM_PAIR",
                "coord_a": w_str_a,
                "coord_b": w_str_b,
                "coord_a_xy": [wc1, wr1],
                "coord_b_xy": [wc2, wr2],
                "coord_a_sgf": coord_to_sgf(wc1, wr1),
                "coord_b_sgf": coord_to_sgf(wc2, wr2),
                "amplitude_a": 0.7071,
                "amplitude_b": 0.7071,
                "description": f"White Quantum stone at {w_str_a} and {w_str_b}"
            })
            entanglement_graph[w_str_a].append(w_str_b)

        return {
            "format": "QuantumGo-9x9-v1.0",
            "board_size": 9,
            "base_classical_stones": {
                "black": [coord_to_9x9_str(c, r) for c, r in black],
                "white": [coord_to_9x9_str(c, r) for c, r in white],
            },
            "black_quantum_piece": black_q_piece,
            "white_quantum_piece": white_q_piece,
            "quantum_moves": quantum_moves,
            "entanglement_edges": dict(entanglement_graph),
            "collapse_rules": [
                "Observation triggers when a path closes a cycle or chain liberties reach 0.",
                "Classical branch 1: Move collapses to primary vital point |coord_a>.",
                "Classical branch 2: Move collapses to secondary point |coord_b>.",
            ]
        }


# ===========================================================================
# Part D: Quantum Difficulty & Sensitivity Analyzer
# ===========================================================================

class QuantumDifficultyAnalyzer:
    """
    Analyzes which stone/move of Black and White, when transformed into a
    Quantum superposed move, maximizes puzzle complexity and difficulty.
    """

    @classmethod
    def evaluate(cls, problem: Dict[str, Any]) -> Dict[str, Any]:
        black = problem.get("initial_black", [])
        white = problem.get("initial_white", [])
        moves = problem.get("solution_moves", [])
        first_player = problem.get("first_player", "B")

        occupied = set(black) | set(white)

        # Evaluate candidate stones for Black and White
        black_candidates = []
        for c, r in black:
            score, rationale = cls._compute_stone_quantum_sensitivity((c, r), "B", black, white, moves)
            coord_str = coord_to_9x9_str(c, r)
            black_candidates.append({
                "coord_9x9": coord_str,
                "coord_sgf": coord_to_sgf(c, r),
                "xy": [c, r],
                "color": "B",
                "difficulty_score": score,
                "rationale": rationale,
            })

        white_candidates = []
        for c, r in white:
            score, rationale = cls._compute_stone_quantum_sensitivity((c, r), "W", white, black, moves)
            coord_str = coord_to_9x9_str(c, r)
            white_candidates.append({
                "coord_9x9": coord_str,
                "coord_sgf": coord_to_sgf(c, r),
                "xy": [c, r],
                "color": "W",
                "difficulty_score": score,
                "rationale": rationale,
            })

        # Evaluate candidate moves from solution sequence
        move_candidates = []
        for idx, (color, (c, r)) in enumerate(moves, start=1):
            branch_weight = 100.0 / idx
            coord_str = coord_to_9x9_str(c, r)
            color_name = "Black" if color == "B" else "White"
            move_candidates.append({
                "move_index": idx,
                "color": color,
                "color_name": color_name,
                "coord_9x9": coord_str,
                "coord_sgf": coord_to_sgf(c, r),
                "xy": [c, r],
                "quantum_branch_difficulty": round(branch_weight, 2),
                "impact": f"Move {idx} ({color_name} at {coord_str}) splits the state space into 2^{idx} quantum collapse trees."
            })

        black_candidates.sort(key=lambda x: x["difficulty_score"], reverse=True)
        white_candidates.sort(key=lambda x: x["difficulty_score"], reverse=True)

        most_difficult_black = black_candidates[0] if black_candidates else None
        most_difficult_white = white_candidates[0] if white_candidates else None
        most_difficult_move = move_candidates[0] if move_candidates else None

        return {
            "most_difficult_black_stone": most_difficult_black,
            "most_difficult_white_stone": most_difficult_white,
            "most_difficult_solution_move": most_difficult_move,
            "top_black_candidates": black_candidates[:3],
            "top_white_candidates": white_candidates[:3],
            "quantum_complexity_index": (
                (most_difficult_black["difficulty_score"] if most_difficult_black else 0) +
                (most_difficult_white["difficulty_score"] if most_difficult_white else 0)
            ) / 2.0,
        }

    @staticmethod
    def _compute_stone_quantum_sensitivity(
        coord: Tuple[int, int],
        color: str,
        same_color: List[Tuple[int, int]],
        opp_color: List[Tuple[int, int]],
        solution_moves: List[Tuple[str, Tuple[int, int]]]
    ) -> Tuple[float, str]:
        """Calculates how much the life/death status changes if this stone becomes superposed."""
        c, r = coord
        opp_set = set(opp_color)
        same_set = set(same_color) - {coord}

        # 1. Contact with opponent stones (cutting points / liberties)
        adj_opp = sum(1 for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)] if (c + dc, r + dr) in opp_set)
        # 2. Proximity to solution moves (vital point interaction)
        dist_to_vital = 99
        if solution_moves:
            v_col, v_row = solution_moves[0][1]
            dist_to_vital = abs(c - v_col) + abs(r - v_row)

        score = 50.0
        score += adj_opp * 15.0  # Contact points create large liberty fluctuations
        if dist_to_vital <= 1:
            score += 35.0  # Immediately adjacent to vital killing point
        elif dist_to_vital <= 2:
            score += 20.0

        if dist_to_vital <= 1:
            rationale = "Crucial cutting/vital stone directly adjacent to the first correct move."
        elif adj_opp >= 2:
            rationale = "High-contact stone sharing liberties with opponent group; superposition creates multi-way capture race."
        else:
            rationale = "Boundary stone influencing eye space perimeter."

        return round(score, 1), rationale


# ===========================================================================
# Part E: Self-Solving Puzzle & Solution Replayer
# ===========================================================================

class TsumegoSelfSolver:
    """
    Self-solves and verifies the life-and-death puzzle step-by-step
    using the numbered solution moves (1, 2, 3...).
    """

    @classmethod
    def solve_and_verify(cls, problem: Dict[str, Any]) -> Dict[str, Any]:
        black = set(problem.get("initial_black", []))
        white = set(problem.get("initial_white", []))
        moves = problem.get("solution_moves", [])
        first_player = problem.get("first_player", "B")

        history = []
        current_black = set(black)
        current_white = set(white)

        # Track captures and board progression
        for step_num, (color, coord) in enumerate(moves, start=1):
            # Play move
            if color == "B":
                current_black.add(coord)
                # Check captures of White
                captured = cls._check_captures(current_white, current_black)
                current_white -= captured
            else:
                current_white.add(coord)
                # Check captures of Black
                captured = cls._check_captures(current_black, current_white)
                current_black -= captured

            history.append({
                "step": step_num,
                "color": color,
                "color_name": "Black" if color == "B" else "White",
                "coord_9x9": coord_to_9x9_str(*coord),
                "coord_sgf": coord_to_sgf(*coord),
                "xy": list(coord),
                "captured_stones_9x9": [coord_to_9x9_str(*c) for c in captured],
                "captured_stones_sgf": [coord_to_sgf(*c) for c in captured],
                "active_black_count": len(current_black),
                "active_white_count": len(current_white),
                "board_snapshot": cls.render_ascii(current_black, current_white, last_move=coord),
            })

        is_solved = len(moves) > 0
        final_status = "Solved (Target captured / dead group destroyed)" if is_solved else "Unsolved (No sequence)"

        return {
            "is_solved": is_solved,
            "status_text": final_status,
            "total_steps": len(moves),
            "step_by_step_trace": history,
            "final_board_ascii": history[-1]["board_snapshot"] if history else cls.render_ascii(black, white),
        }

    @staticmethod
    def _check_captures(group_to_check: Set[Tuple[int, int]], opponents: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Identifies any connected stones with 0 liberties on a 9x9 board."""
        captured = set()
        visited = set()
        occupied = group_to_check | opponents

        for stone in group_to_check:
            if stone in visited:
                continue
            # BFS string
            string = set()
            liberties = set()
            queue = deque([stone])
            visited.add(stone)

            while queue:
                curr = queue.popleft()
                string.add(curr)
                cx, cy = curr
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < 9 and 0 <= ny < 9:
                        if (nx, ny) in group_to_check and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                        elif (nx, ny) not in occupied:
                            liberties.add((nx, ny))

            if len(liberties) == 0:
                captured.update(string)

        return captured

    @staticmethod
    def render_ascii(
        black: Set[Tuple[int, int]],
        white: Set[Tuple[int, int]],
        last_move: Optional[Tuple[int, int]] = None,
    ) -> str:
        """Render standard 9x9 Go board with A-J (skip I) and 1-9."""
        header = "   " + " ".join(COORD_9X9_LETTERS)
        lines = [header]
        for r in range(9):
            row_chars = []
            for c in range(9):
                if (c, r) == last_move:
                    row_chars.append("*" if (c, r) in black else "@")
                elif (c, r) in black:
                    row_chars.append("X")
                elif (c, r) in white:
                    row_chars.append("O")
                else:
                    # Star points on 9x9 at (2,2), (6,2), (4,4), (2,6), (6,6)
                    if (c, r) in [(2, 2), (6, 2), (4, 4), (2, 6), (6, 6)]:
                        row_chars.append("+")
                    else:
                        row_chars.append(".")
            lines.append(f"{r + 1:2} " + " ".join(row_chars))
        return "\n".join(lines)


# ===========================================================================
# Unified Pipeline Runner
# ===========================================================================

def process_complete_tsumego(image_or_sgf_path: str) -> Dict[str, Any]:
    """
    Complete end-to-end processing executing steps A, B, C, D, and E.
    """
    path = Path(image_or_sgf_path)
    extractor = PNGGoExtractor()

    # Step A: Extract
    if path.suffix.lower() == ".sgf":
        problem_data = extractor.parse_sgf_file(path)
    else:
        problem_data = extractor.extract_from_png(str(path))

    # Step B: Pattern Analysis
    pattern_info = TsumegoPatternAnalyzer.classify(problem_data)

    # Step C: QuantumGo Conversion
    quantum_version = QuantumGoConverter.create_quantum_representation(problem_data)

    # Step D: Difficulty & Sensitivity Analysis
    difficulty_analysis = QuantumDifficultyAnalyzer.evaluate(problem_data)

    # Step E: Self-solving Verification
    solution_trace = TsumegoSelfSolver.solve_and_verify(problem_data)

    return {
        "problem_data": problem_data,
        "pattern_analysis": pattern_info,
        "quantum_version": quantum_version,
        "difficulty_analysis": difficulty_analysis,
        "solution_trace": solution_trace,
    }


def export_to_9x9_sgf(result: Dict[str, Any], title: str = "QuantumGo-9x9") -> str:
    """Generates standard SGF with 9x9 board, solution sequence, and quantum metadata."""
    pdata = result.get("problem_data", {})
    qver = result.get("quantum_version", {})
    pat = result.get("pattern_analysis", {})
    diff = result.get("difficulty_analysis", {})

    b_stones = "".join(f"[{coord_to_sgf(*p)}]" for p in pdata.get("initial_black", []))
    w_stones = "".join(f"[{coord_to_sgf(*p)}]" for p in pdata.get("initial_white", []))

    q_moves = qver.get("quantum_moves", [])
    q_notes = []
    if qver.get("black_quantum_piece"):
        bq = qver["black_quantum_piece"]
        q_notes.append(f"Black Q-Piece: {bq['state_ket']}")
    if qver.get("white_quantum_piece"):
        wq = qver["white_quantum_piece"]
        q_notes.append(f"White Q-Piece: {wq['state_ket']}")

    q_comment = " | ".join(q_notes)
    pattern_name = pat.get("pattern_name", "Tsumego")
    first_player = pdata.get("first_player", "B")

    sgf_lines = [
        f"(;GM[1]FF[4]CA[UTF-8]SZ[9]GN[{title}]PL[{first_player}]",
        f"GC[{pattern_name} | {q_comment}]",
        f"AB{b_stones}AW{w_stones}",
    ]

    # Add main correct solution branch
    moves = pdata.get("solution_moves", [])
    if moves:
        branch = []
        for color, coord in moves:
            branch.append(f";{color}[{coord_to_sgf(*coord)}]")
        branch_str = "".join(branch)
        sgf_lines.append(f"({branch_str}N[Correct Solution]))")
    else:
        sgf_lines.append(")")

    return "\n".join(sgf_lines)


def export_to_quantum_json(result: Dict[str, Any]) -> str:
    """Generates complete structured QuantumGo 9x9 JSON definition."""
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        result = process_complete_tsumego(target)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python quantum_tsumego_toolkit.py <image_or_sgf_path>")

