#!/usr/bin/env python3
import sys
from pathlib import Path
import cv2
import numpy as np

img_path = Path(sys.argv[1])
img = cv2.imread(str(img_path))
h, w = img.shape[:2]

lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)

# Print stats
print("L range:", int(l.min()), int(l.max()), "mean:", int(l.mean()))
print("A range:", int(a.min()), int(a.max()), "mean:", int(a.mean()) - 128)
print("B range:", int(b.min()), int(b.max()), "mean:", int(b.mean()) - 128)

# Board mask
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

# Save board ROI
out_roi = img_path.stem + "_roi.png"
cv2.imwrite(str(Path("extracted") / out_roi), roi)

# Try grid detection methods
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# Method 1: Otsu binary
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_binary.png")), binary)

# Method 2: Detect dark grid lines only (brown lines)
# Grid lines are darker than board. Use a threshold in the lower L range.
_, line_bin = cv2.threshold(l[y0:y1, x0:x1], 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_linebin_l.png")), line_bin)

# Detect stone masks from original ROI colors and remove them from binary
roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
rl, ra, rb = cv2.split(roi_lab)
# Black stones: low L, neutral a/b
black_stone = ((rl < 60) & (ra > 120) & (ra < 140) & (rb > 120) & (rb < 140)).astype(np.uint8) * 255
# White stones: high L, neutral a/b
white_stone = ((rl > 200) & (ra > 120) & (ra < 140) & (rb > 120) & (rb < 140)).astype(np.uint8) * 255

# Dilate to cover full stone areas
stone_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
stone_mask = cv2.bitwise_or(
    cv2.dilate(black_stone, stone_kernel, iterations=1),
    cv2.dilate(white_stone, stone_kernel, iterations=1)
)
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_stone_mask.png")), stone_mask)

# Subtract stones from binary
grid_binary = cv2.bitwise_and(binary, cv2.bitwise_not(stone_mask))
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_grid_binary.png")), grid_binary)

# Projections on grid-only binary
proj_y = np.sum(grid_binary, axis=1)
proj_x = np.sum(grid_binary, axis=0)
print("ProjY max:", int(proj_y.max()), "peaks:", len([p for p in proj_y if p > 0.15 * proj_y.max() and p > 50]))
print("ProjX max:", int(proj_x.max()), "peaks:", len([p for p in proj_x if p > 0.15 * proj_x.max() and p > 50]))

# Save projection visualizations
py_img = np.zeros((200, len(proj_y)), dtype=np.uint8)
for i, v in enumerate(proj_y):
    h_px = int(199 * min(v / (proj_y.max() + 1), 1.0))
    if h_px > 0:
        py_img[-h_px:, i] = 255
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_proj_y.png")), py_img)

px_img = np.zeros((len(proj_x), 200), dtype=np.uint8)
for i, v in enumerate(proj_x):
    w_px = int(199 * min(v / (proj_x.max() + 1), 1.0))
    if w_px > 0:
        px_img[i, :w_px] = 255
cv2.imwrite(str(Path("extracted") / (img_path.stem + "_proj_x.png")), px_img)

print("Debug images saved to extracted/")
