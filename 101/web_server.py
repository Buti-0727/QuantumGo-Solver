#!/usr/bin/env python3
"""
Localhost Web Server for QuantumGo Life-and-Death Problem Converter (Strict 9x9 Board).
Provides:
  1. Instant upload & built-in sample picker from 101/image & 101/extracted/sgf.
  2. Clear English Go notation (standard A-J, 1-9 coordinates).
  3. Precise visual detection & highlighting of Black & White Quantum pieces on the 9x9 board.
  4. Direct export to folder (101/extracted/json/ & 101/extracted/sgf/) + Browser Downloads.
  5. Step-by-step solver replay with capture animations.
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
from quantum_tsumego_toolkit import (
    process_complete_tsumego,
    export_to_9x9_sgf,
    export_to_quantum_json,
    COORD_9X9_LETTERS,
)

PORT = 8080

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QuantumGo 9x9 Tsumego Studio</title>
  <style>
    :root {
      --bg: #0b1120;
      --card-bg: #1e293b;
      --card-border: rgba(255, 255, 255, 0.08);
      --accent: #38bdf8;
      --accent-purple: #c084fc;
      --accent-amber: #f59e0b;
      --accent-green: #34d399;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --board-bg: #dca357;
      --line-color: #4a2810;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; padding: 20px; }
    .container { max-width: 1280px; margin: 0 auto; }
    
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
    header h1 { font-size: 1.8rem; background: linear-gradient(135deg, #38bdf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    header p { color: var(--text-muted); font-size: 0.9rem; }
    
    .grid { display: grid; grid-template-columns: 480px 1fr; gap: 20px; }
    @media (max-width: 980px) { .grid { grid-template-columns: 1fr; } }
    
    .card { background: var(--card-bg); border-radius: 12px; padding: 18px; border: 1px solid var(--card-border); box-shadow: 0 4px 20px rgba(0,0,0,0.35); }
    .card h2 { font-size: 1.05rem; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; color: var(--accent); }
    
    /* Dropzone & Picker */
    .dropzone { border: 2px dashed rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 16px; text-align: center; cursor: pointer; transition: all 0.2s; background: rgba(15, 23, 42, 0.5); margin-bottom: 12px; }
    .dropzone:hover { border-color: var(--accent); background: rgba(56, 189, 248, 0.08); }
    .dropzone input { display: none; }
    
    .sample-bar { display: flex; gap: 8px; align-items: center; }
    select { flex: 1; background: #0f172a; color: var(--text); border: 1px solid rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; outline: none; }
    select:focus { border-color: var(--accent); }

    /* Canvas Board */
    .board-wrapper { display: flex; justify-content: center; margin: 10px 0; }
    #boardCanvas { width: 440px; height: 440px; background: var(--board-bg); border-radius: 8px; box-shadow: 0 8px 28px rgba(0,0,0,0.6); }

    /* Quantum Legend / Controls */
    .legend-row { display: flex; justify-content: space-around; background: #0f172a; padding: 8px; border-radius: 8px; margin-bottom: 10px; font-size: 0.82rem; }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    .dot-bq { background: #c084fc; box-shadow: 0 0 8px #c084fc; }
    .dot-wq { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
    .dot-sol { background: #38bdf8; box-shadow: 0 0 8px #38bdf8; }

    /* Buttons */
    .controls { display: flex; gap: 8px; justify-content: center; margin-top: 10px; flex-wrap: wrap; }
    .btn { background: #334155; color: white; border: none; padding: 7px 14px; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 0.85rem; transition: background 0.15s; }
    .btn:hover { background: #475569; }
    .btn-primary { background: #0284c7; }
    .btn-primary:hover { background: #0369a1; }
    .btn-export { background: #059669; }
    .btn-export:hover { background: #047857; }
    .btn-purple { background: #7e22ce; }
    .btn-purple:hover { background: #6b21a8; }
    
    /* Metrics & Quantum Piece Cards */
    .metric-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 0.88rem; }
    .metric-row:last-child { border-bottom: none; }
    .metric-val { font-weight: 600; color: var(--accent); }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }
    .badge-blue { background: rgba(56,189,248,0.2); color: #38bdf8; }
    .badge-purple { background: rgba(168,85,247,0.25); color: #c084fc; border: 1px solid rgba(168,85,247,0.4); }
    .badge-amber { background: rgba(245,158,11,0.25); color: #f59e0b; border: 1px solid rgba(245,158,11,0.4); }

    .q-piece-box { background: #0f172a; border-radius: 8px; padding: 10px 12px; margin: 8px 0; border-left: 3px solid var(--accent); cursor: pointer; transition: all 0.2s; }
    .q-piece-box:hover { background: #172554; border-color: #38bdf8; }
    .q-piece-box.purple-border { border-left-color: #c084fc; }
    .q-piece-box.amber-border { border-left-color: #f59e0b; }

    /* Export Box */
    .export-bar { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
    
    /* Tabs & Code viewer */
    .tab-bar { display: flex; gap: 4px; margin-bottom: 8px; }
    .tab-btn { background: #0f172a; color: var(--text-muted); border: 1px solid var(--card-border); padding: 6px 12px; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 0.8rem; }
    .tab-btn.active { background: #0b132b; color: var(--accent); border-bottom-color: transparent; }
    pre { background: #0b132b; padding: 12px; border-radius: 0 8px 8px 8px; overflow-x: auto; font-size: 0.82rem; color: #a5f3fc; line-height: 1.4; max-height: 240px; border: 1px solid var(--card-border); }
    
    .loading { display: none; text-align: center; color: var(--accent); margin: 8px 0; font-weight: 600; font-size: 0.9rem; }
    .toast { display: none; position: fixed; bottom: 24px; right: 24px; background: #059669; color: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); font-weight: 500; font-size: 0.9rem; z-index: 100; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>QuantumGo 9&times;9 Tsumego Studio</h1>
        <p>101weiqi Converter &bull; 9&times;9 Sub-board Normalization &bull; Quantum Superposition &bull; 101 Folder Exporter</p>
      </div>
      <div>
        <button class="btn btn-export" onclick="exportToFolder()">💾 Save to 101 Folder</button>
        <button class="btn" onclick="downloadJSON()">📥 JSON</button>
        <button class="btn" onclick="downloadSGF()">📥 SGF</button>
      </div>
    </header>

    <div class="grid">
      <!-- Left Column: Source Selection & 9x9 Board -->
      <div>
        <div class="card">
          <h2>1. Select or Upload Problem</h2>
          <div class="dropzone" onclick="document.getElementById('fileInput').click()">
            <p><strong>Click or Drag &amp; Drop</strong> 101weiqi Screenshot (PNG/JPG/SGF)</p>
            <span style="font-size: 0.78rem; color: var(--text-muted);">Auto-normalizes bounding box to standard 9&times;9 Go coordinates</span>
            <input type="file" id="fileInput" accept="image/png, image/jpeg, .sgf" onchange="handleFileUpload(this.files[0])">
          </div>
          
          <div class="sample-bar">
            <select id="sampleSelect" onchange="loadSample(this.value)">
              <option value="">-- Or Pick From 101 Dataset Samples --</option>
            </select>
            <button class="btn btn-primary" onclick="loadSelectedSample()">Load</button>
          </div>
          <div class="loading" id="loading">Processing &amp; computing quantum states...</div>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h2>
            <span>2. Standard 9&times;9 Go Board</span>
            <span id="stepDisplay" style="font-size: 0.82rem; color: var(--text-muted);">Initial State</span>
          </h2>
          
          <div class="legend-row">
            <div class="legend-item"><span class="legend-dot dot-bq"></span> Black Q-Piece</div>
            <div class="legend-item"><span class="legend-dot dot-wq"></span> White Q-Piece</div>
            <div class="legend-item"><span class="legend-dot dot-sol"></span> Solution Move</div>
          </div>

          <div class="board-wrapper">
            <canvas id="boardCanvas" width="440" height="440"></canvas>
          </div>

          <div class="controls">
            <button class="btn" onclick="toggleQuantumMode()" id="qModeBtn">🔮 Quantum: ON</button>
            <button class="btn" onclick="prevStep()">&larr; Prev</button>
            <button class="btn" onclick="resetSteps()">⏮ Reset</button>
            <button class="btn" onclick="nextStep()">Next &rarr;</button>
            <button class="btn btn-primary" onclick="autoPlay()" id="playBtn">&#9654; Auto Play</button>
          </div>
        </div>
      </div>

      <!-- Right Column: Quantum & Tactical Analysis -->
      <div>
        <!-- Step 3 Card -->
        <div class="card">
          <h2>3. Tsumego Motif &amp; Quantum Superposition</h2>
          
          <div class="metric-row">
            <span>Pattern Motif</span>
            <span class="badge badge-blue" id="patternName">Awaiting problem...</span>
          </div>
          <div class="metric-row">
            <span>Region</span>
            <span class="metric-val" id="patternRegion">-</span>
          </div>
          <div class="metric-row">
            <span>First Vital Move (9&times;9)</span>
            <span class="metric-val" id="vitalPoints" style="color: #34d399;">-</span>
          </div>
          
          <!-- Exact Black Quantum Piece -->
          <div class="q-piece-box purple-border" onclick="highlightPiece('B')">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color: #c084fc;">🟣 Black Quantum Piece (BQ)</strong>
              <span class="badge badge-purple" id="bqState">-</span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;" id="bqDesc">Primary stone superposed into alternate coordinate</p>
          </div>

          <!-- Exact White Quantum Piece -->
          <div class="q-piece-box amber-border" onclick="highlightPiece('W')">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color: #f59e0b;">🟠 White Quantum Piece (WQ)</strong>
              <span class="badge badge-amber" id="wqState">-</span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;" id="wqDesc">Primary stone superposed into alternate coordinate</p>
          </div>
        </div>

        <!-- Step 4 Card -->
        <div class="card" style="margin-top: 16px;">
          <h2>4. Maximum Quantum Difficulty Sensitivity</h2>
          
          <div class="metric-row">
            <span>Most Sensitive Black Stone</span>
            <span class="metric-val" id="diffBlack">-</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;" id="diffBlackRat">-</div>
          
          <div class="metric-row">
            <span>Most Sensitive White Stone</span>
            <span class="metric-val" id="diffWhite">-</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;" id="diffWhiteRat">-</div>
          
          <div class="metric-row">
            <span>Highest Branching Solution Move</span>
            <span class="metric-val" id="diffMove">-</span>
          </div>
          <div class="metric-row">
            <span>Quantum Complexity Index</span>
            <span class="metric-val" id="quantumIndex">-</span>
          </div>
        </div>

        <!-- Step 5 / Export Viewer -->
        <div class="card" style="margin-top: 16px;">
          <h2>5. Export Specifications (9&times;9)</h2>
          
          <div class="tab-bar">
            <button class="tab-btn active" id="tabJson" onclick="switchTab('json')">Quantum JSON</button>
            <button class="tab-btn" id="tabSgf" onclick="switchTab('sgf')">9&times;9 SGF</button>
          </div>
          
          <pre id="codeOutput">// Select or upload a problem to view export specification</pre>
          
          <div class="export-bar">
            <button class="btn btn-export" onclick="exportToFolder()">💾 Save to 101/extracted/</button>
            <button class="btn" onclick="downloadJSON()">📥 Download .json</button>
            <button class="btn" onclick="downloadSGF()">📥 Download .sgf</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">File exported successfully!</div>

  <script>
    let currentResult = null;
    let currentStepIndex = 0;
    let showQuantumOverlay = true;
    let isPlaying = false;
    let playInterval = null;
    let activeTab = 'json';
    let currentFileName = 'quantum_problem';

    const COORD_CHARS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']; // 9x9 skipping I
    const STAR_POINTS = [[2, 2], [6, 2], [4, 4], [2, 6], [6, 6]];

    // Load available sample files on startup
    window.onload = function() {
      fetchSamples();
      drawBoard9x9();
    };

    function fetchSamples() {
      fetch('/api/list_samples')
        .then(r => r.json())
        .then(data => {
          const sel = document.getElementById('sampleSelect');
          sel.innerHTML = '<option value="">-- Pick from 101 Dataset Samples --</option>';
          if (data.samples) {
            data.samples.forEach(s => {
              const opt = document.createElement('option');
              opt.value = s.path;
              opt.innerText = `${s.type}: ${s.name}`;
              sel.appendChild(opt);
            });
          }
        })
        .catch(err => console.error("Error loading sample list:", err));
    }

    function loadSelectedSample() {
      const sel = document.getElementById('sampleSelect');
      if (sel.value) loadSample(sel.value);
    }

    function loadSample(path) {
      if (!path) return;
      document.getElementById('loading').style.display = 'block';
      fetch('/api/load_sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
      })
      .then(r => r.json())
      .then(res => {
        document.getElementById('loading').style.display = 'none';
        currentResult = res;
        currentStepIndex = 0;
        currentFileName = path.split('/').pop().replace(/\\.[^/.]+$/, "");
        renderUI(res);
      })
      .catch(err => {
        document.getElementById('loading').style.display = 'none';
        alert("Error loading sample: " + err);
      });
    }

    function handleFileUpload(file) {
      if (!file) return;
      document.getElementById('loading').style.display = 'block';
      currentFileName = file.name.replace(/\\.[^/.]+$/, "");
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

      // Pattern & Vital Points
      document.getElementById('patternName').innerText = pat.pattern_name || "Standard";
      document.getElementById('patternRegion').innerText = pat.region || "Corner";
      document.getElementById('vitalPoints').innerText = pat.first_move || "-";

      // Black Quantum Piece
      if (qver.black_quantum_piece) {
        const bq = qver.black_quantum_piece;
        document.getElementById('bqState').innerText = bq.state_ket;
        document.getElementById('bqDesc').innerText = `Stone at ${bq.primary_coord_9x9} superposed with ${bq.secondary_coord_9x9} (${bq.probability_split})`;
      } else {
        document.getElementById('bqState').innerText = "-";
        document.getElementById('bqDesc').innerText = "None detected";
      }

      // White Quantum Piece
      if (qver.white_quantum_piece) {
        const wq = qver.white_quantum_piece;
        document.getElementById('wqState').innerText = wq.state_ket;
        document.getElementById('wqDesc').innerText = `Stone at ${wq.primary_coord_9x9} superposed with ${wq.secondary_coord_9x9} (${wq.probability_split})`;
      } else {
        document.getElementById('wqState').innerText = "-";
        document.getElementById('wqDesc').innerText = "None detected";
      }

      // Difficulty stones
      if (diff.most_difficult_black_stone) {
        const d = diff.most_difficult_black_stone;
        document.getElementById('diffBlack').innerText = `${d.coord_9x9} (Sensitivity: ${d.difficulty_score})`;
        document.getElementById('diffBlackRat').innerText = d.rationale;
      }
      if (diff.most_difficult_white_stone) {
        const d = diff.most_difficult_white_stone;
        document.getElementById('diffWhite').innerText = `${d.coord_9x9} (Sensitivity: ${d.difficulty_score})`;
        document.getElementById('diffWhiteRat').innerText = d.rationale;
      }
      if (diff.most_difficult_solution_move) {
        const m = diff.most_difficult_solution_move;
        document.getElementById('diffMove').innerText = `Step ${m.move_index} (${m.color_name} at ${m.coord_9x9})`;
      }
      document.getElementById('quantumIndex').innerText = diff.quantum_complexity_index || "-";

      updateCodeView();
      drawBoard9x9();
    }

    function drawBoard9x9() {
      const canvas = document.getElementById('boardCanvas');
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      // Wood background
      ctx.fillStyle = '#dca357';
      ctx.fillRect(0, 0, w, h);

      const pad = 38;
      const cellSize = (w - pad * 2) / 8;

      // Grid lines
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

      // Star Points
      ctx.fillStyle = '#4a2810';
      STAR_POINTS.forEach(([sx, sy]) => {
        ctx.beginPath();
        ctx.arc(pad + sx * cellSize, pad + sy * cellSize, 3.8, 0, Math.PI * 2);
        ctx.fill();
      });

      // Coordinate Labels
      ctx.fillStyle = '#5c3817';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      for (let i = 0; i < 9; i++) {
        const p = pad + i * cellSize;
        ctx.fillText(COORD_CHARS[i], p, pad - 18);
        ctx.fillText(COORD_CHARS[i], p, h - pad + 18);
        ctx.fillText(i + 1, pad - 18, p);
        ctx.fillText(i + 1, w - pad + 18, p);
      }

      if (!currentResult) return;

      const pdata = currentResult.problem_data;
      const moves = pdata.solution_moves || [];
      const qver = currentResult.quantum_version || {};

      // Calculate active stones up to step
      let blackStones = new Set(pdata.initial_black.map(p => `${p[0]},${p[1]}`));
      let whiteStones = new Set(pdata.initial_white.map(p => `${p[0]},${p[1]}`));

      for (let i = 0; i < currentStepIndex && i < moves.length; i++) {
        const [color, [c, r]] = moves[i];
        if (color === 'B') blackStones.add(`${c},${r}`);
        else whiteStones.add(`${c},${r}`);
      }

      // Draw Quantum Entanglement Links (Dashed Lines)
      if (showQuantumOverlay) {
        if (qver.black_quantum_piece) {
          const bq = qver.black_quantum_piece;
          const [px, py] = bq.primary_xy;
          const [sx, sy] = bq.secondary_xy;
          drawEntanglementLine(ctx, pad + px*cellSize, pad + py*cellSize, pad + sx*cellSize, pad + sy*cellSize, '#c084fc');
          drawGhostStone(ctx, pad + sx*cellSize, pad + sy*cellSize, cellSize * 0.42, '#c084fc', '|B2⟩');
        }
        if (qver.white_quantum_piece) {
          const wq = qver.white_quantum_piece;
          const [wpx, wpy] = wq.primary_xy;
          const [wsx, wsy] = wq.secondary_xy;
          drawEntanglementLine(ctx, pad + wpx*cellSize, pad + wpy*cellSize, pad + wsx*cellSize, pad + wsy*cellSize, '#f59e0b');
          drawGhostStone(ctx, pad + wsx*cellSize, pad + wsy*cellSize, cellSize * 0.42, '#f59e0b', '|W2⟩');
        }
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

      // Draw Quantum Glowing Halos on Exact Quantum Stones
      if (showQuantumOverlay) {
        if (qver.black_quantum_piece) {
          const [bx, by] = qver.black_quantum_piece.primary_xy;
          drawQuantumAura(ctx, pad + bx*cellSize, pad + by*cellSize, cellSize * 0.48, '#c084fc', 'BQ');
        }
        if (qver.white_quantum_piece) {
          const [wx, wy] = qver.white_quantum_piece.primary_xy;
          drawQuantumAura(ctx, pad + wx*cellSize, pad + wy*cellSize, cellSize * 0.48, '#f59e0b', 'WQ');
        }
      }

      // Draw Solution Step Indicators
      if (currentStepIndex > 0 && currentStepIndex <= moves.length) {
        const [color, [lc, lr]] = moves[currentStepIndex - 1];
        drawGlowCircle(ctx, pad + lc * cellSize, pad + lr * cellSize, cellSize * 0.46, '#38bdf8');
        ctx.fillStyle = color === 'B' ? '#ffffff' : '#111827';
        ctx.font = 'bold 15px sans-serif';
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

    function drawQuantumAura(ctx, px, py, r, color, tag) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 3.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 14;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.stroke();

      // Mini badge tag
      ctx.shadowBlur = 0;
      ctx.fillStyle = color;
      ctx.font = 'bold 10px sans-serif';
      ctx.fillText(tag, px, py - r - 3);
      ctx.restore();
    }

    function drawGhostStone(ctx, px, py, r, color, label) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.fillStyle = color + '22';
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.setLineDash([]);
      ctx.fillStyle = color;
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText(label, px, py);
      ctx.restore();
    }

    function drawEntanglementLine(ctx, x1, y1, x2, y2, color) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([3, 5]);
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.restore();
    }

    function drawGlowCircle(ctx, px, py, r, color) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 3.5;
      ctx.shadowColor = color;
      ctx.shadowBlur = 14;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    function toggleQuantumMode() {
      showQuantumOverlay = !showQuantumOverlay;
      document.getElementById('qModeBtn').innerText = showQuantumOverlay ? "🔮 Quantum: ON" : "⚪ Classical: ON";
      drawBoard9x9();
    }

    function highlightPiece(color) {
      showQuantumOverlay = true;
      document.getElementById('qModeBtn').innerText = "🔮 Quantum: ON";
      drawBoard9x9();
      showToast(`Focused on ${color === 'B' ? 'Black' : 'White'} Quantum Piece on 9x9 Board`);
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

    function resetSteps() {
      currentStepIndex = 0;
      if (isPlaying) stopAutoPlay();
      drawBoard9x9();
    }

    function autoPlay() {
      if (isPlaying) {
        stopAutoPlay();
      } else {
        if (!currentResult) return;
        isPlaying = true;
        document.getElementById('playBtn').innerText = "⏸ Pause";
        playInterval = setInterval(() => {
          const maxSteps = currentResult.problem_data.solution_moves.length;
          if (currentStepIndex < maxSteps) {
            currentStepIndex++;
            drawBoard9x9();
          } else {
            stopAutoPlay();
          }
        }, 1000);
      }
    }

    function stopAutoPlay() {
      isPlaying = false;
      clearInterval(playInterval);
      document.getElementById('playBtn').innerText = "▶ Auto Play";
    }

    function switchTab(tab) {
      activeTab = tab;
      document.getElementById('tabJson').classList.toggle('active', tab === 'json');
      document.getElementById('tabSgf').classList.toggle('active', tab === 'sgf');
      updateCodeView();
    }

    function updateCodeView() {
      if (!currentResult) return;
      const pre = document.getElementById('codeOutput');
      if (activeTab === 'json') {
        pre.innerText = JSON.stringify(currentResult, null, 2);
      } else {
        fetch('/api/get_sgf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(currentResult)
        })
        .then(r => r.text())
        .then(sgf => pre.innerText = sgf)
        .catch(() => pre.innerText = "// SGF generation ready");
      }
    }

    function exportToFolder() {
      if (!currentResult) {
        alert("Please load or upload a problem first.");
        return;
      }
      fetch('/api/export_to_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: currentFileName, data: currentResult })
      })
      .then(r => r.json())
      .then(res => {
        if (res.success) {
          showToast(`Saved to 101/extracted: ${res.json_file} & ${res.sgf_file}`);
        } else {
          alert("Export failed: " + res.error);
        }
      })
      .catch(err => alert("Error exporting: " + err));
    }

    function downloadJSON() {
      if (!currentResult) return;
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentResult, null, 2));
      const a = document.createElement('a');
      a.setAttribute("href", dataStr);
      a.setAttribute("download", `${currentFileName}_9x9_quantum.json`);
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast(`Downloaded ${currentFileName}_9x9_quantum.json`);
    }

    function downloadSGF() {
      if (!currentResult) return;
      fetch('/api/get_sgf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentResult)
      })
      .then(r => r.text())
      .then(sgf => {
        const dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(sgf);
        const a = document.createElement('a');
        a.setAttribute("href", dataStr);
        a.setAttribute("download", `${currentFileName}_9x9.sgf`);
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast(`Downloaded ${currentFileName}_9x9.sgf`);
      });
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.style.display = 'block';
      setTimeout(() => { t.style.display = 'none'; }, 4000);
    }
  </script>
</body>
</html>
"""


class QuantumServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/list_samples":
            samples = []
            img_dir = ROOT / "image"
            if img_dir.exists():
                for p in sorted(img_dir.glob("*.png")):
                    samples.append({"name": p.name, "path": str(p), "type": "Image"})
            sgf_dir = ROOT / "extracted" / "sgf"
            if sgf_dir.exists():
                for p in sorted(sgf_dir.glob("*.sgf"))[:15]:
                    samples.append({"name": p.name, "path": str(p), "type": "SGF"})
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"samples": samples}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8")) if body else {}

        if self.path == "/api/analyze":
            filename = payload.get("filename", "upload.png")
            data_url = payload.get("data", "")
            if "," in data_url:
                data_url = data_url.split(",", 1)[1]
            raw_bytes = base64.b64decode(data_url)

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

        elif self.path == "/api/load_sample":
            target_path = payload.get("path", "")
            if os.path.exists(target_path):
                result = process_complete_tsumego(target_path)
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        elif self.path == "/api/get_sgf":
            sgf_text = export_to_9x9_sgf(payload)
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(sgf_text.encode("utf-8"))

        elif self.path == "/api/export_to_folder":
            filename_base = payload.get("filename", "problem")
            # sanitize filename
            clean_name = Path(filename_base).stem
            data = payload.get("data", {})

            json_out_dir = ROOT / "extracted" / "json"
            sgf_out_dir = ROOT / "extracted" / "sgf"
            json_out_dir.mkdir(parents=True, exist_ok=True)
            sgf_out_dir.mkdir(parents=True, exist_ok=True)

            json_file = json_out_dir / f"{clean_name}_9x9.json"
            sgf_file = sgf_out_dir / f"{clean_name}_9x9.sgf"

            json_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            sgf_file.write_text(export_to_9x9_sgf(data, title=clean_name), encoding="utf-8")

            resp = {
                "success": True,
                "json_file": str(json_file.relative_to(ROOT)),
                "sgf_file": str(sgf_file.relative_to(ROOT)),
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode("utf-8"))

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
