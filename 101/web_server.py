#!/usr/bin/env python3
"""
Localhost Web Server for QuantumGo Life-and-Death Problem Converter (Strict 9x9 Board).
Allows uploading any 101weiqi PNG screenshot and renders:
  A. Extracted Go board & solution steps normalized to 9x9
  B. Tsumego pattern classification
  C. QuantumGo converted representation (9x9 coordinates)
  D. Quantum difficulty sensitivity heatmap
  E. Interactive step-by-step solver replay on a 9x9 Go board
"""

import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import the core engine
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))
from quantum_tsumego_toolkit import process_complete_tsumego, COORD_9X9_LETTERS

PORT = 8080

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QuantumGo Tsumego Studio (9x9 Board)</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --accent: #38bdf8;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --board-bg: #dca357;
      --line-color: #4a2810;
      --star-color: #4a2810;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; padding: 24px; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 24px; }
    header h1 { font-size: 2rem; background: linear-gradient(135deg, #38bdf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    header p { color: var(--text-muted); margin-top: 4px; font-size: 0.95rem; }
    
    .grid { display: grid; grid-template-columns: 460px 1fr; gap: 24px; }
    @media (max-width: 950px) { .grid { grid-template-columns: 1fr; } }
    
    .card { background: var(--card-bg); border-radius: 12px; padding: 18px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .card h2 { font-size: 1.1rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; color: var(--accent); }
    
    /* Upload Dropzone */
    .dropzone { border: 2px dashed rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: rgba(15, 23, 42, 0.5); }
    .dropzone:hover { border-color: var(--accent); background: rgba(56, 189, 248, 0.08); }
    .dropzone input { display: none; }

    /* 9x9 Board Canvas */
    .board-wrapper { display: flex; justify-content: center; margin-top: 10px; }
    #boardCanvas { width: 400px; height: 400px; background: var(--board-bg); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); }

    /* Badges & Metrics */
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: rgba(56,189,248,0.2); color: var(--accent); }
    .badge-purple { background: rgba(168,85,247,0.2); color: #c084fc; }
    .metric-row { display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 0.88rem; }
    .metric-row:last-child { border-bottom: none; }
    .metric-val { font-weight: 600; color: #38bdf8; }

    /* Step replay buttons */
    .controls { display: flex; gap: 8px; justify-content: center; margin-top: 12px; }
    .btn-small { background: #334155; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: 500; }
    .btn-small:hover { background: #475569; }

    pre { background: #0b132b; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 0.82rem; color: #a5f3fc; line-height: 1.4; max-height: 220px; }
    .loading { display: none; text-align: center; color: var(--accent); margin: 10px 0; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>QuantumGo 9&times;9 Tsumego Studio</h1>
      <p>Upload 101weiqi Screenshot &rarr; Auto 9&times;9 Normalization &rarr; Quantum Superposition &rarr; Difficulty Heatmap &rarr; Solver Replay</p>
    </header>

    <div class="grid">
      <!-- Left Column: Upload & 9x9 Board -->
      <div>
        <div class="card">
          <h2>1. Upload 101weiqi Problem</h2>
          <div class="dropzone" onclick="document.getElementById('fileInput').click()">
            <p><strong>Click or Drag &amp; Drop</strong> 101weiqi Image (PNG/JPG/SGF)</p>
            <span style="font-size: 0.8rem; color: var(--text-muted);">Auto-crops &amp; normalizes to standard 9&times;9 board coordinates</span>
            <input type="file" id="fileInput" accept="image/png, image/jpeg, .sgf" onchange="handleFileUpload(this.files[0])">
          </div>
          <div class="loading" id="loading">Processing &amp; mapping to 9&times;9 QuantumGo...</div>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h2>2. Standard 9&times;9 Go Board (A–J, 1–9)</h2>
          <div class="board-wrapper">
            <canvas id="boardCanvas" width="400" height="400"></canvas>
          </div>
          <div class="controls">
            <button class="btn-small" onclick="prevStep()">&larr; Prev Step</button>
            <span id="stepDisplay" style="align-self: center; font-size: 0.88rem; font-weight: 600;">Initial Position</span>
            <button class="btn-small" onclick="nextStep()">Next Step &rarr;</button>
          </div>
        </div>
      </div>

      <!-- Right Column: Quantum & Tactical Analysis -->
      <div>
        <div class="card">
          <h2>3. Tsumego Motif &amp; Quantum Transformation</h2>
          <div class="metric-row">
            <span>Pattern Motif (B)</span>
            <span class="badge" id="patternName">Awaiting upload...</span>
          </div>
          <div class="metric-row">
            <span>Board Grid</span>
            <span class="metric-val">9&times;9 Standard Sub-board</span>
          </div>
          <div class="metric-row">
            <span>First Vital Move (急所)</span>
            <span class="metric-val" id="vitalPoints">-</span>
          </div>
          <div class="metric-row">
            <span>Quantum Move Superposition (C)</span>
            <span class="badge badge-purple" id="quantumPair">-</span>
          </div>
          <div class="metric-row">
            <span>Quantum Complexity Score</span>
            <span class="metric-val" id="quantumIndex">-</span>
          </div>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h2>4. Maximum Quantum Difficulty Stones (D)</h2>
          <div class="metric-row">
            <span>Most Difficult Black Stone</span>
            <span class="metric-val" id="diffBlack">-</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;" id="diffBlackRat">-</div>
          <div class="metric-row">
            <span>Most Difficult White Stone</span>
            <span class="metric-val" id="diffWhite">-</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;" id="diffWhiteRat">-</div>
          <div class="metric-row">
            <span>Highest Branching Move</span>
            <span class="metric-val" id="diffMove">-</span>
          </div>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h2>5. QuantumGo 9&times;9 JSON Definition</h2>
          <pre id="jsonOutput">// Upload an image to view 9x9 QuantumGo JSON specification</pre>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentResult = null;
    let currentStepIndex = 0;
    const COORD_CHARS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']; // 9x9 skipping I

    // Star points on 9x9: C3 (2,2), G3 (6,2), E5 (4,4), C7 (2,6), G7 (6,6)
    const STAR_POINTS = [[2, 2], [6, 2], [4, 4], [2, 6], [6, 6]];

    function handleFileUpload(file) {
      if (!file) return;
      document.getElementById('loading').style.display = 'block';
      const reader = new FileReader();
      reader.onload = function(e) {
        fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: file.name, data: e.target.result })
        })
        .then(r => r.json())
        .then(res => {
          document.getElementById('loading').style.display = 'none';
          currentResult = res;
          currentStepIndex = 0;
          renderUI(res);
        })
        .catch(err => {
          document.getElementById('loading').style.display = 'none';
          alert("Error processing: " + err);
        });
      };
      reader.readAsDataURL(file);
    }

    function renderUI(res) {
      const pat = res.pattern_analysis;
      const qver = res.quantum_version;
      const diff = res.difficulty_analysis;

      document.getElementById('patternName').innerText = pat.pattern_name;
      document.getElementById('vitalPoints').innerText = pat.first_move;

      if (qver.quantum_moves && qver.quantum_moves.length > 0) {
        const qm = qver.quantum_moves[0];
        document.getElementById('quantumPair').innerText = `|${qm.coord_a}> + |${qm.coord_b}>`;
      }
      document.getElementById('quantumIndex').innerText = diff.quantum_complexity_index;

      if (diff.most_difficult_black_stone) {
        document.getElementById('diffBlack').innerText = `${diff.most_difficult_black_stone.coord} (Score: ${diff.most_difficult_black_stone.difficulty_score})`;
        document.getElementById('diffBlackRat').innerText = diff.most_difficult_black_stone.rationale;
      }
      if (diff.most_difficult_white_stone) {
        document.getElementById('diffWhite').innerText = `${diff.most_difficult_white_stone.coord} (Score: ${diff.most_difficult_white_stone.difficulty_score})`;
        document.getElementById('diffWhiteRat').innerText = diff.most_difficult_white_stone.rationale;
      }
      if (diff.most_difficult_solution_move) {
        document.getElementById('diffMove').innerText = `Move ${diff.most_difficult_solution_move.move_index} (${diff.most_difficult_solution_move.coord})`;
      }

      document.getElementById('jsonOutput').innerText = JSON.stringify(qver, null, 2);
      drawBoard9x9();
    }

    function drawBoard9x9() {
      const canvas = document.getElementById('boardCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      // Draw wood background
      ctx.fillStyle = '#dca357';
      ctx.fillRect(0, 0, w, h);

      const pad = 34;
      const cellSize = (w - pad * 2) / 8;

      // Draw 9x9 grid lines
      ctx.strokeStyle = '#4a2810';
      ctx.lineWidth = 1.6;
      for (let i = 0; i < 9; i++) {
        const pos = pad + i * cellSize;
        // Vertical
        ctx.beginPath();
        ctx.moveTo(pos, pad);
        ctx.lineTo(pos, pad + 8 * cellSize);
        ctx.stroke();

        // Horizontal
        ctx.beginPath();
        ctx.moveTo(pad, pos);
        ctx.lineTo(pad + 8 * cellSize, pos);
        ctx.stroke();
      }

      // Draw Star Points (Hoshi)
      ctx.fillStyle = '#4a2810';
      STAR_POINTS.forEach(([sx, sy]) => {
        ctx.beginPath();
        ctx.arc(pad + sx * cellSize, pad + sy * cellSize, 3.5, 0, Math.PI * 2);
        ctx.fill();
      });

      // Draw Coordinate Labels (A..J on top/bottom, 1..9 on left/right)
      ctx.fillStyle = '#5c3817';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      for (let i = 0; i < 9; i++) {
        const p = pad + i * cellSize;
        // Column letters (top & bottom)
        ctx.fillText(COORD_CHARS[i], p, pad - 16);
        ctx.fillText(COORD_CHARS[i], p, h - pad + 16);
        // Row numbers (left & right)
        ctx.fillText(i + 1, pad - 16, p);
        ctx.fillText(i + 1, w - pad + 16, p);
      }

      if (!currentResult) return;

      const pdata = currentResult.problem_data;
      const moves = pdata.solution_moves || [];

      // Collect active stones up to currentStepIndex
      let blackStones = new Set(pdata.initial_black.map(p => `${p[0]},${p[1]}`));
      let whiteStones = new Set(pdata.initial_white.map(p => `${p[0]},${p[1]}`));

      for (let i = 0; i < currentStepIndex && i < moves.length; i++) {
        const [color, [c, r]] = moves[i];
        if (color === 'B') blackStones.add(`${c},${r}`);
        else whiteStones.add(`${c},${r}`);
      }

      // Draw Black Stones
      blackStones.forEach(k => {
        const [x, y] = k.split(',').map(Number);
        if (x >= 0 && x < 9 && y >= 0 && y < 9) {
          drawStone(ctx, pad + x * cellSize, pad + y * cellSize, cellSize * 0.44, '#111827', '#4b5563');
        }
      });

      // Draw White Stones
      whiteStones.forEach(k => {
        const [x, y] = k.split(',').map(Number);
        if (x >= 0 && x < 9 && y >= 0 && y < 9) {
          drawStone(ctx, pad + x * cellSize, pad + y * cellSize, cellSize * 0.44, '#f8fafc', '#cbd5e1');
        }
      });

      // Draw Quantum Move Superposition Glow Highlights
      if (currentResult.quantum_version.quantum_moves && currentResult.quantum_version.quantum_moves.length > 0) {
        const qm = currentResult.quantum_version.quantum_moves[0];
        const [c1, r1] = moves.length > 0 ? moves[0][1] : [0, 0];
        // Draw glow on primary and secondary superposition
        drawGlowCircle(ctx, pad + c1 * cellSize, pad + r1 * cellSize, cellSize * 0.48, '#00f2fe');
      }

      // Draw numbered step labels if replaying
      if (currentStepIndex > 0 && currentStepIndex <= moves.length) {
        const [color, [lc, lr]] = moves[currentStepIndex - 1];
        ctx.fillStyle = color === 'B' ? '#f8fafc' : '#111827';
        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(currentStepIndex, pad + lc * cellSize, pad + lr * cellSize);
      }

      document.getElementById('stepDisplay').innerText = currentStepIndex === 0 ? "Initial State" : `Step ${currentStepIndex} of ${moves.length}`;
    }

    function drawStone(ctx, px, py, r, gradStart, gradEnd) {
      const grad = ctx.createRadialGradient(px - r*0.3, py - r*0.3, r*0.1, px, py, r);
      grad.addColorStop(0, gradEnd);
      grad.addColorStop(1, gradStart);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }

    function drawGlowCircle(ctx, px, py, r, color) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 3.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    function nextStep() {
      if (!currentResult) return;
      const maxSteps = currentResult.problem_data.solution_moves.length;
      if (currentStepIndex < maxSteps) {
        currentStepIndex++;
        drawBoard9x9();
      }
    }

    function prevStep() {
      if (!currentResult) return;
      if (currentStepIndex > 0) {
        currentStepIndex--;
        drawBoard9x9();
      }
    }

    // Initialize board on load
    window.onload = function() {
      drawBoard9x9();
    };
  </script>
</body>
</html>
"""


class QuantumServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            filename = payload.get("filename", "upload.png")
            data_url = payload.get("data", "")

            # Decode base64 data
            if "," in data_url:
                data_url = data_url.split(",", 1)[1]
            raw_bytes = base64.b64decode(data_url)

            # Write to temp file
            suffix = Path(filename).suffix or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(raw_bytes)
                tmp_path = tmp.name

            try:
                result = process_complete_tsumego(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, QuantumServerHandler)
    print(f"QuantumGo 9x9 Tsumego Studio running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
