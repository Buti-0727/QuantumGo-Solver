# QuantumGo Life-and-Death (L&D) Solver

An exact Life-and-Death solver for **QuantumGo**, extending the **Relevance-Zone Search (RZS)** framework from [`study-LD-RZ-solver`](./study-LD-RZ-solver/) to two-board quantum entangled Go.

---

## 📚 Core Authoritative Documentation

All AI agents and developers working on this codebase must adhere strictly to these three primary documents:

### 1. [**`QuantumGo Solver Coding Protocol.md`**](./QuantumGo%20Solver%20Coding%20Protocol.md)
> **Role: #1 Highest Priority Authoritative Source**
- **Purpose**: Definitive source of truth for all game rules, data structures, algorithms, and architectural constraints.
- **Key Details**:
  - Exact dual-board state representation ($B_1$ and $B_2$).
  - Quantum opening moves (Move 1 Black, Move 2 White, creating entangled stone pairs).
  - Synchronized move execution from Move 3 onward (identical coordinates, illegal if illegal on either board).
  - Cross-board entanglement capture cascades with recursive resolution to stable equilibrium.
  - Quantum Relevance Zone ($RZ_Q = RZ_{B1} \cup RZ_{B2} \cup \text{EntangledPartners}(RZ)$) and null-move pruning mechanics.

### 2. [**`quantumgo_solver_capability_specification.md`**](./quantumgo_solver_capability_specification.md)
> **Role: Authoritative Reference for Capabilities & I/O Specifications**
- **Purpose**: Defines what the solver must accomplish, acceptable I/O formats, and exact evaluation metrics.
- **Key Details**:
  - Core solver functional requirements and exact proof tree outputs.
  - Problem input formats (JSON/SGF extensions for two-board QuantumGo).
  - Terminal state evaluation standards (**ALIVE**, **DEAD**, **SEKI**, **KO**).
  - Performance budgets, proof tree verification, and solution variation reporting.

### 3. [**`quantumgo_solver_agent_development_phases.md`**](./quantumgo_solver_agent_development_phases.md)
> **Role: Mandatory Step-by-Step Roadmap & Phase Order**
- **Purpose**: Dictates the exact chronological phases and gating criteria for development.
- **Key Details**:
  - **Phase 1**: Dual-Board State & Entanglement Data Structures (`QuantumBoardState`, `EntanglementTable`, Zobrist hashing).
  - **Phase 2**: Move Generation & Capture Cascade Engine (synchronized legality, recursive cascade loop).
  - **Phase 3**: Quantum Relevance Zone ($RZ_Q$) & Move Pruning (dynamic expansion across entanglement links).
  - **Phase 4**: Exact Search & Proof Tree Construction (AND/OR tree search with $RZ_Q$).
  - **Phase 5**: Benchmark Suite & Regression Testing (QuantumGo Tsumego testbed).
  - **Phase 6**: Integration, Optimization, and Documentation.

---

## 📖 Recommended Reading Order for Agents

1. [**`AGENTS.md`**](./AGENTS.md) — Operational instructions, agent rules, and invariants.
2. [**`QuantumGo Solver Coding Protocol.md`**](./QuantumGo%20Solver%20Coding%20Protocol.md) — Authoritative implementation protocol.
3. [**`quantumgo_solver_capability_specification.md`**](./quantumgo_solver_capability_specification.md) — Capability & I/O specifications.
4. [**`quantumgo_solver_agent_development_phases.md`**](./quantumgo_solver_agent_development_phases.md) — Phased roadmap.
5. [**`prd/OVERVIEW.md`**](./prd/OVERVIEW.md) & [**`prd/`**](./prd/) — Modular PRD breakdowns.
6. [**`paper/`**](./paper/) — Reference literature on Relevance-Zone Search and Quantum Go.

---

## 🎯 Project Scope & Invariants

- **Objective**: Exact Life-and-Death (L&D) proof tree search. **Not** a full-game MCTS playing bot.
- **Boards**: Exactly two synchronized boards ($B_1$ and $B_2$).
- **Opening Moves (Moves 1 & 2)**:
  - Move 1 (Black) & Move 2 (White): One stone placed on $B_1$ and one on $B_2$, forming an entangled pair.
- **Synchronized Moves (Move 3+)**:
  - Played at the exact same coordinate $(x, y)$ on both $B_1$ and $B_2$.
  - Must be legal on *both* boards simultaneously.
- **Entanglement & Cascades**:
  - Capturing an entangled stone on one board instantly removes its partner on the opposite board.
  - Partner removals can trigger recursive cross-board capture cascades.
- **Quantum Relevance Zone ($RZ_Q$)**:
  - Propagates relevance across $B_1 \leftrightarrow B_2$ via entanglement links.

---

## 🏗️ Repository Layout

```text
.
├── AGENTS.md                                    # Instructions and protocol for AI coding agents
├── README.md                                    # Project overview and documentation index
├── QuantumGo Solver Coding Protocol.md          # #1 Authoritative implementation protocol
├── quantumgo_solver_capability_specification.md # Authoritative capability & I/O specification
├── quantumgo_solver_agent_development_phases.md # Mandatory phased development roadmap
├── prd/                                         # PRD modular specification files
│   ├── OVERVIEW.md
│   ├── PRD-01_Game_State_Representation.md
│   ├── PRD-02_Move_Generation_and_Legality.md
│   ├── PRD-03_Entanglement_and_Capture_Mechanics.md
│   ├── PRD-04_Relevance_Zone_and_Null_Moves.md
│   └── PRD-05_L&D_Objective_and_Evaluation.md
├── study-LD-RZ-solver/                          # Base single-board RZS engine (CGI / MCTPS / etc.)
└── paper/                                       # Reference research papers
```
