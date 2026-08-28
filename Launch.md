# QuantumGo Life-and-Death Solver — Launch Guide

Quick, hands-on instructions for building, launching, and running all components of the project.

---

## ⚡ Quick Start (One-Liner per Component)

| Component | Quick Launch Command | Interface / Port |
| :--- | :--- | :--- |
| **C++ Solver & Tests** | `cmake -B quantum/build -S quantum && cmake --build quantum/build && ./quantum/build/tests/qgo_tests` | CLI Terminal |
| **101 Tsumego Web Studio** | `python3 101/web_server.py` | `http://localhost:8080` |
| **Interactive Quantum GUI** | `python3 -m http.server 3000 --directory quantum/gui` | `http://localhost:3000` |
| **Batch Analysis Pipeline** | `python3 101/run_quantum_tsumego_pipeline.py` | Generates Markdown report |

---

## 1. C++ Exact QuantumGo L&D Solver (`quantum/`)

The core engine: dual-board ($B_1 \times B_2$) representation, recursive cross-board capture cascades, entanglement tracking, and Quantum Relevance-Zone ($RZ_Q$) search.

### 1.1 Prerequisites
- CMake 3.10 or newer
- C++17 compatible compiler (`clang++` or `g++`)

### 1.2 Build

```bash
# 1. Configure and compile in quantum/build
cmake -B quantum/build -S quantum
cmake --build quantum/build
```

### 1.3 Run Solver CLI & Unit Tests

```bash
# Run all 32 unit tests (State, Entanglement, Capture Cascades, RZ_Q, Game Replays)
./quantum/build/tests/qgo_tests

# Run standalone solver executable demo
./quantum/build/qgo_solver
```

---

## 2. 101Weiqi Tsumego Studio & Web Server (`101/`)

Interactive web interface for uploading Go problems, automated SGF/JSON parsing, quantum superposition mapping, difficulty sensitivity analysis, and step-by-step solver replay.

### 2.1 Launch Web Server

```bash
python3 101/web_server.py
```

- Open your browser at: **`http://localhost:8080`**
- Features available:
  - **Sample Picker**: Select from preloaded 101Weiqi test cases.
  - **Visual Board**: 9×9 board with coordinate labels and quantum pair markers.
  - **Tactical Patterns**: Eye-space diagnosis, vital point identification, and difficulty scoring.
  - **Export Options**: Export to 9×9 SGF and Quantum JSON format.

### 2.2 Run Full Batch Tsumego Analysis

```bash
python3 101/run_quantum_tsumego_pipeline.py
```

- Analyzes all extracted SGFs in `101/extracted/sgf/`.
- Generates comprehensive markdown report at `101/extracted/review/quantum_tsumego_full_analysis.md`.

---

## 3. QuantumGo Dual-Board Visualizer (`quantum/gui/`)

Standalone client-side GUI for visualising dual boards $B_1$ and $B_2$, entanglement links, and move replays.

### 3.1 Launch GUI

```bash
python3 -m http.server 3000 --directory quantum/gui
```

- Open your browser at: **`http://localhost:3000`**
- Alternatively, double-click `quantum/gui/index.html` to open directly in any modern web browser.

---

## 4. Reference Single-Board RZ Solver (`study-LD-RZ-solver/`)

Baseline single-board Relevance-Zone solver from the IEEE ToG paper.

```bash
cd study-LD-RZ-solver

# Launch Docker container
./scripts/run-container.sh

# Inside container: configure and compile
./scripts/clean-up.sh
./scripts/setup-cmake.sh release caffe2
make

# Run solver on benchmark candidates
Release/CGI -conf_file cfg/RZS-TT.cfg -mode tsumego_solver
```

---

## 5. Directory Structure Overview

```text
├── Launch.md                      # Hands-on launch guide (this file)
├── quantum/                       # Core C++ QuantumGo L&D Solver
│   ├── src/                       # Engine (Board, Cascades, Entanglement, RZone, Search)
│   ├── tests/                     # Test suite (32 unit test cases)
│   ├── gui/                       # Dual-board web GUI
│   └── main.cpp                   # Solver CLI entrypoint
├── 101/                           # 101Weiqi Tsumego Toolkit & Studio
│   ├── web_server.py              # Localhost studio server (:8080)
│   ├── quantum_tsumego_toolkit.py # Pattern diagnosis & quantum conversion
│   ├── run_quantum_tsumego_pipeline.py # Batch analysis runner
│   └── extracted/                 # Extracted SGF, JSON, and reports
├── study-LD-RZ-solver/            # Single-board reference RZ solver
├── games/ & game_eval/            # Self-play game datasets for solver validation
└── agents/                        # Architectural documentation & coding specifications
```
