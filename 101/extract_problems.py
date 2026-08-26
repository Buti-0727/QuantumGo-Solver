#!/usr/bin/env python3
"""
Extract Go life-and-death problems from 101weiqi-style screenshots.

Produces:
  - extracted/sgf/      : one .sgf per problem with initial stones and solution
  - extracted/json/     : one .json per problem compatible with study-LD-RZ-solver
  - extracted/review/   : a human-readable markdown review + summary

The script detects the board, the grid inferred from stone centers, classifies
intersections, reads numbers on stones via OCR, and writes SGF/JSON files.
Absolute board offsets are provided manually in OFFSETS (one per screenshot).
"""

import os
import re
import json
import math
import glob
from pathlib import Path
from collections import defaultdict

# pyrefly: ignore [missing-import]
import cv2
import numpy as np
# pyrefly: ignore [missing-import]
import easyocr


ROOT = Path(__file__).parent.resolve()
IMG_DIR = ROOT
OUT_DIR = ROOT / "extracted"
SGF_DIR = OUT_DIR / "sgf"
JSON_DIR = OUT_DIR / "json"
REVIEW_DIR = OUT_DIR / "review"

SGF_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

SGF_LETTERS = "abcdefghjklmnopqrst"


def idx_to_sgf(col: int, row: int) -> str:
    return SGF_LETTERS[col] + SGF_LETTERS[row]


# ---------------------------------------------------------------------------
# Manual absolute offsets for each screenshot.
# Key: image filename stem.
# Value: (top_left_col, top_left_row) in 19x19 zero-based coords.
# The visible top-left intersection is mapped to these absolute coords.
# ---------------------------------------------------------------------------

OFFSETS = {
    "Weixin Image_20260826133010_222_8": (0, 0),
    "Weixin Image_20260826133445_223_8": (0, 0),
    "Weixin Image_20260826133454_224_8": (0, 0),
    "Weixin Image_20260826133548_225_8": (0, 0),
    "Weixin Image_20260826133559_226_8": (0, 0),
    "Weixin Image_20260826133622_227_8": (0, 0),
    "Weixin Image_20260826133631_228_8": (0, 0),
    "Weixin Image_20260826133743_229_8": (0, 0),
    "Weixin Image_20260826133749_230_8": (0, 0),
    "Weixin Image_20260826133812_231_8": (0, 0),
    "Weixin Image_20260826133837_232_8": (0, 0),
    "Weixin Image_20260826134914_233_8": (0, 0),
    "Weixin Image_20260826134924_234_8": (0, 0),
    "Weixin Image_20260826134934_235_8": (0, 0),
    "Weixin Image_20260826134948_236_8": (0, 0),
    "Weixin Image_20260826134958_237_8": (0, 0),
    "Weixin Image_20260826135008_238_8": (0, 0),
    "Weixin Image_20260826135021_239_8": (0, 0),
    "Weixin Image_20260826135029_240_8": (0, 0),
    "Weixin Image_20260826135059_241_8": (0, 0),
    "Weixin Image_20260826135116_243_8": (0, 0),
    "Weixin Image_20260826135127_244_8": (0, 0),
    "Weixin Image_20260826135135_245_8": (0, 0),
    "Weixin Image_20260826135142_246_8": (0, 0),
    "Weixin Image_20260826135156_247_8": (0, 0),
    "Weixin Image_20260826135211_248_8": (0, 0),
    "Weixin Image_20260826135225_249_8": (0, 0),
}


# ---------------------------------------------------------------------------
# Board region detection
# ---------------------------------------------------------------------------

def detect_board_region(image_bgr: np.ndarray):
    """Return the bounding box (x0, y0, x1, y1) of the wooden board."""
    h, w = image_bgr.shape[:2]
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    mask = (
        (l > 80) & (l < 200) &
        (a > 120) & (a < 145) &
        (b > 140) & (b < 185)
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    if cv2.contourArea(cnt) < 0.05 * h * w:
        return None

    x, y, bw, bh = cv2.boundingRect(cnt)
    margin = int(min(bw, bh) * 0.03)
    x0, y0 = max(0, x + margin), max(0, y + margin)
    x1, y1 = min(w, x + bw - margin), min(h, y + bh - margin)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------------
# Stone detection
# ---------------------------------------------------------------------------

def detect_stones(image_bgr: np.ndarray, bbox: tuple):
    """
    Detect black/white stones inside the board bbox.
    Returns a list of dicts: {cx, cy, color, area}.
    """
    x0, y0, x1, y1 = bbox
    roi = image_bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return []

    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    chroma = np.sqrt((a.astype(float) - 128) ** 2 + (b.astype(float) - 128) ** 2)

    # Black stones: dark and low chroma
    black_mask = ((l < 95) & (chroma < 22)).astype(np.uint8) * 255
    # White stones: bright and low chroma
    white_mask = ((l > 190) & (chroma < 22)).astype(np.uint8) * 255

    stone_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, stone_kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, stone_kernel)

    stones = []
    for color, mask in [("black", black_mask), ("white", white_mask)]:
        num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, num):
            area = stats[i, cv2.CC_STAT_AREA]
            cx, cy = centroids[i]
            # Filter out tiny noise and huge accidental regions
            if 80 < area < 0.15 * roi.shape[0] * roi.shape[1]:
                stones.append({
                    "cx": float(cx),
                    "cy": float(cy),
                    "color": color,
                    "area": int(area),
                })
    return stones


# ---------------------------------------------------------------------------
# Grid inference from stone centers
# ---------------------------------------------------------------------------

def cluster_values(values, min_gap=12):
    if not values:
        return []
    values = sorted(values)
    clusters = [[values[0]]]
    for v in values[1:]:
        if v - clusters[-1][-1] < min_gap:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [float(np.mean(c)) for c in clusters]


def fill_grid_lines(lines, length):
    """Given detected line positions, fill missing lines by equal spacing."""
    if len(lines) < 2:
        return lines
    diffs = np.diff(lines)
    spacing = float(np.median(diffs))
    if spacing <= 0:
        return lines

    filled = [lines[0]]
    for i in range(1, len(lines)):
        gap = lines[i] - lines[i - 1]
        steps = max(1, int(round(gap / spacing)))
        for j in range(1, steps):
            filled.append(lines[i - 1] + j * gap / steps)
        filled.append(lines[i])
    return filled


def infer_grid(stones, roi_shape):
    """
    Infer vertical and horizontal grid line positions from stone centers.
    Returns (v_lines, h_lines) as lists of pixel coords relative to ROI.
    """
    if not stones:
        return [], []

    cxs = [s["cx"] for s in stones]
    cys = [s["cy"] for s in stones]

    v_lines = cluster_values(cxs)
    h_lines = cluster_values(cys)

    v_lines = fill_grid_lines(v_lines, roi_shape[1])
    h_lines = fill_grid_lines(h_lines, roi_shape[0])

    return v_lines, h_lines


# ---------------------------------------------------------------------------
# Intersection classification
# ---------------------------------------------------------------------------

def classify_intersection(roi_bgr: np.ndarray, x: int, y: int, spacing: float):
    """Classify the intersection at (x, y) in ROI coords."""
    r = int(spacing * 0.38)
    h, w = roi_bgr.shape[:2]
    x0, x1 = max(0, x - r), min(w, x + r)
    y0, y1 = max(0, y - r), min(h, y + r)
    crop = roi_bgr[y0:y1, x0:x1]
    if crop.size == 0:
        return "empty"

    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    mask = np.zeros_like(l)
    cv2.circle(mask, (crop.shape[1] // 2, crop.shape[0] // 2), r, 255, -1)

    mean_l = cv2.mean(l, mask=mask)[0]
    mean_a = cv2.mean(a, mask=mask)[0]
    mean_b = cv2.mean(b, mask=mask)[0]
    chroma = math.sqrt((mean_a - 128) ** 2 + (mean_b - 128) ** 2)

    if mean_l < 100 and chroma < 18:
        return "black"
    if mean_l > 175 and chroma < 18:
        return "white"
    return "empty"


# ---------------------------------------------------------------------------
# Number OCR
# ---------------------------------------------------------------------------

def detect_number(roi_bgr: np.ndarray, x: int, y: int, spacing: float,
                  stone_color: str, reader: easyocr.Reader):
    r = int(spacing * 0.42)
    h, w = roi_bgr.shape[:2]
    x0, x1 = max(0, x - r), min(w, x + r)
    y0, y1 = max(0, y - r), min(h, y + r)
    crop = roi_bgr[y0:y1, x0:x1]
    if crop.size == 0:
        return None

    # Quick number-presence check by contrast with the stone color
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    if stone_color == "black":
        # Number is light gray/white
        if np.max(gray) < 120:
            return None
    else:
        # Number is dark gray/black
        if np.min(gray) > 130:
            return None

    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    scale = max(2.0, 64.0 / min(rgb.shape[:2]))
    if scale > 1.0:
        rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    results = reader.readtext(rgb, detail=0, allowlist="0123456789")
    if not results:
        return None

    txt = "".join(results).strip()
    txt = re.sub(r"[^0-9]", "", txt)
    if txt:
        try:
            return int(txt)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_problem(image_path: Path, reader: easyocr.Reader):
    img = cv2.imread(str(image_path))
    if img is None:
        raise RuntimeError(f"Could not load {image_path}")

    bbox = detect_board_region(img)
    if bbox is None:
        raise RuntimeError(f"Could not detect board region in {image_path}")

    x0, y0, x1, y1 = bbox
    roi = img[y0:y1, x0:x1]

    stones = detect_stones(img, bbox)
    if len(stones) < 4:
        raise RuntimeError(f"Too few stones detected in {image_path}")

    v_lines, h_lines = infer_grid(stones, roi.shape[:2])
    if len(v_lines) < 5 or len(h_lines) < 5:
        raise RuntimeError(f"Could not infer grid in {image_path}")

    # Estimate spacing
    spacing = (v_lines[1] - v_lines[0] + h_lines[1] - h_lines[0]) / 2.0

    # Build local grid and classify intersections
    grid = []
    for ri, hy in enumerate(h_lines):
        row = []
        for ci, vx in enumerate(v_lines):
            color = classify_intersection(roi, int(vx), int(hy), spacing)
            number = None
            if color != "empty":
                number = detect_number(roi, int(vx), int(hy), spacing, color, reader)
            row.append({"color": color, "number": number})
        grid.append(row)

    # Determine absolute coordinates
    stem = image_path.stem
    abs_col0, abs_row0 = OFFSETS.get(stem, (0, 0))

    abs_stones = {}
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            if cell["color"] != "empty":
                abs_stones[(abs_col0 + ci, abs_row0 + ri)] = {
                    "color": cell["color"],
                    "number": cell["number"],
                }

    return {
        "image": str(image_path.name),
        "bbox": bbox,
        "grid_size": (len(v_lines), len(h_lines)),
        "spacing": spacing,
        "stones": abs_stones,
    }


def main():
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    images = sorted(IMG_DIR.glob("Weixin Image_*.png"))
    print(f"Found {len(images)} images")

    all_problems = []
    for img_path in images:
        print(f"Processing {img_path.name} ...")
        try:
            prob = extract_problem(img_path, reader)
            all_problems.append(prob)
            print(f"  -> grid {prob['grid_size']}, {sum(1 for s in prob['stones'].values() if s['color'] != 'empty')} stones")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Save raw extraction with string keys
    raw = []
    for p in all_problems:
        raw.append({
            "image": p["image"],
            "bbox": p["bbox"],
            "grid_size": p["grid_size"],
            "spacing": p["spacing"],
            "stones": {f"{c},{r}": v for (c, r), v in p["stones"].items()},
        })
    out_json = OUT_DIR / "raw_extraction.json"
    with open(out_json, "w") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)
    print(f"Saved raw extraction to {out_json}")


if __name__ == "__main__":
    main()
