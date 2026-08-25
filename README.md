# QuantumGo Life-and-Death (L&D) Solver

An exact Life-and-Death solver for **QuantumGo**, extending the **Relevance-Zone Search (RZS)** framework from [`study-LD-RZ-solver`](./study-LD-RZ-solver/) to two-board quantum entangled Go.

---

## 📖 Key Specifications & Reading Order for Agents

Before writing code or modifying engine components, read the specifications in this order:

1. [**`QuantumGo Solver Coding Protocol.md`**](./QuantumGo%20Solver%20Coding%20Protocol.md) *(Authoritative)*: Complete game rules, search algorithm modifications, architecture, and coding constraints.
2. [**`prd/OVERVIEW.md`**](./prd/OVERVIEW.md) & [**`prd/`**](./prd/): Product requirements for state representation, move generation, capture cascades, and relevance zones.
3. [**`quantumgo_solver_capability_specification.md`**](./quantumgo_solver_capability_specification.md): Core functional requirements and solver capabilities.
4. [**`quantumgo_solver_agent_development_phases.md`**](./quantumgo_solver_agent_development_phases.md): Phased roadmap (Phases 1 through 6).
5. [**`paper/`**](./paper/): Academic background on Relevance-Zone Search and Quantum Go.

---

## 🎯 Project Scope & Rules

- **Goal**: Exact Life-and-Death (L&D) solving (proof trees for ALIVE / DEAD / SEKI / KO). **Not** a general-purpose full-game playing engine.
- **Boards**: Exactly two synchronized boards: **Board 1 (B1)** and **Board 2 (B2)**.
- **Opening Moves (Moves 1 & 2)**:
  - Move 1 (Black) & Move 2 (White): One stone on B1 and one stone on B2, forming an entangled pair.
- **Standard Moves (Move 3+)**:
  - Synchronized: Played at the exact same coordinate on both B1 and B2.
  - Legality: Must be legal on *both* boards simultaneously.
- **Entanglement & Cascades**:
  - Capturing an entangled stone on one board instantly removes its partner on the other board.
  - Partner removal can reduce liberties of adjacent groups, triggering recursive cross-board capture cascades.
- **Quantum Relevance Zone ($RZ_Q$)**:
  - Extends RZ across B1 and B2 via entanglement links to prune irrelevant search spaces.

---

## 🏗️ Repository Layout

```text
.
├── AGENTS.md                                    # Instructions and protocol for AI coding agents
├── QuantumGo Solver Coding Protocol.md          # Authoritative implementation protocol
├── quantumgo_solver_capability_specification.md # Detailed capability specification
├── quantumgo_solver_agent_development_phases.md # Phased development plan
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

---

## 🛠️ Implementation Phases

1. **Phase 1: Dual-Board State & Entanglement Data Structures** (B1/B2 representation, pair tracking).
2. **Phase 2: Move Generation & Capture Cascade Engine** (Simultaneous moves, recursive cross-board capture resolution).
3. **Phase 3: Quantum Relevance Zone ($RZ_Q$) & Move Pruning** (Dynamic zone expansion across entanglement links).
4. **Phase 4: Exact Search & Proof Tree Construction** (AND/OR tree search with $RZ_Q$).
5. **Phase 5: Benchmark Suite & Regression Testing** (Tsumego problem suite for QuantumGo).
6. **Phase 6: Integration, Optimization, and Documentation**.

See [**`AGENTS.md`**](./AGENTS.md) for agent-specific workflows and execution standards.
