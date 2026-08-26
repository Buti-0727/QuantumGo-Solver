#!/usr/bin/env python3
"""Debug stone detection and grid inference from stone centers."""
import sys
from pathlib import Path
import cv2
import numpy as np

img_path = Path(sys.argv[1])
out_dir = img_path.parent / "extracted"
out_dir.mkdir(parents=True, exist_ok=True)
img = cv2.imread(str(img_path))
h, w = img.shape[:2]

# Board mask
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
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
cnt = max(contours, key=cv2.contourArea)
x, y, bw, bh = cv2.boundingRect(cnt)
margin = int(min(bw, bh) * 0.03)
x0, y0 = max(0, x + margin), max(0, y + margin)
x1, y1 = min(w, x + bw - margin), min(h, y + bh - margin)
roi = img[y0:y1, x0:x1]
roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
rl, ra, rb = cv2.split(roi_lab)
chroma = np.sqrt((ra.astype(float) - 128) ** 2 + (rb.astype(float) - 128) ** 2)

# Detect stones
black = ((rl < 90) & (chroma < 20)).astype(np.uint8) * 255
white = ((rl > 190) & (chroma < 20)).astype(np.uint8) * 255

# Clean up
stone_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
black = cv2.morphologyEx(black, cv2.MORPH_CLOSE, stone_kernel)
white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, stone_kernel)

# Visualize stone masks
stone_vis = np.zeros_like(roi)
stone_vis[:, :, 2] = black
stone_vis[:, :, 0] = white
cv2.imwrite(str(out_dir / (img_path.stem + "_stones.png")), stone_vis)

# Find connected components and centroids
all_stones = []
for color_name, mask_img in [("black", black), ("white", white)]:
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_img, connectivity=8)
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        cx, cy = centroids[i]
        if area > 50:
            all_stones.append((cx, cy, area, color_name))

print(f"Detected {len(all_stones)} stones")

# Cluster centers to find grid lines
cxs = sorted([s[0] for s in all_stones])
cys = sorted([s[1] for s in all_stones])

def cluster_values(values, min_gap=10):
    if not values:
        return []
    clusters = [[values[0]]]
    for v in values[1:]:
        if v - clusters[-1][-1] < min_gap:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [np.mean(c) for c in clusters]

v_lines = cluster_values(cxs)
h_lines = cluster_values(cys)
print(f"Initial clusters: H={len(h_lines)}, V={len(v_lines)}")

# Estimate spacing and fill missing lines
def fill_lines(lines, length):
    if len(lines) < 2:
        return lines
    diffs = np.diff(lines)
    spacing = np.median(diffs)
    # Fill from first to last
    filled = [lines[0]]
    for i in range(1, len(lines)):
        gap = lines[i] - lines[i - 1]
        steps = int(round(gap / spacing))
        if steps <= 0:
            steps = 1
        for j in range(1, steps):
            filled.append(lines[i - 1] + j * gap / steps)
        filled.append(lines[i])
    return filled

v_lines = fill_lines(v_lines, roi.shape[1])
h_lines = fill_lines(h_lines, roi.shape[0])
print(f"Filled lines: H={len(h_lines)}, V={len(v_lines)}")

# Draw grid and stone centers on ROI
vis = roi.copy()
for y in h_lines:
    cv2.line(vis, (0, int(y)), (vis.shape[1], int(y)), (0, 255, 0), 1)
for x in v_lines:
    cv2.line(vis, (int(x), 0), (int(x), vis.shape[0]), (0, 255, 0), 1)
for cx, cy, area, color in all_stones:
    cv2.circle(vis, (int(cx), int(cy)), 5, (0, 0, 255), -1)
cv2.imwrite(str(out_dir / (img_path.stem + "_grid.png")), vis)

print("Saved stones.png and grid.png")
