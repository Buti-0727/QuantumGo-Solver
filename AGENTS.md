# AGENTS.md — Instructions for Coding Agents

This document is the operational guideline for any AI agent working on the **QuantumGo Life-and-Death (L&D) Solver**.

---

## 1. Prime Directive

You are implementing an **Exact Life-and-Death Solver** for QuantumGo by adapting the Relevance-Zone Search engine in [`study-LD-RZ-solver/`](./study-LD-RZ-solver/).
- **DO NOT** build a full-game MCTS playing engine.
- **DO NOT** deviate from the rules defined in [`QuantumGo Solver Coding Protocol.md`](./QuantumGo%20Solver%20Coding%20Protocol.md).
- **DO** focus strictly on exact proof trees, dual-board state transitions, capture cascades, and Quantum Relevance Zone ($RZ_Q$) pruning.

---

## 2. Authoritative Document Hierarchy & Core References

When rules, algorithms, or design decisions conflict, resolve strictly in this priority order:

### 🥇 1. [`QuantumGo Solver Coding Protocol.md`](./QuantumGo%20Solver%20Coding%20Protocol.md) *(Highest Priority Source of Truth)*
- **Role**: Configured as the **#1 highest priority authoritative source** for all rules, data structures, and algorithms.
- **Agent Action**: Check this file first for board invariants, dual-board representation, synchronized move rules, recursive capture cascade algorithms, and $RZ_Q$ expansion mathematics.

### 🥈 2. [`quantumgo_solver_capability_specification.md`](./quantumgo_solver_capability_specification.md)
- **Role**: **Authoritative reference for required solver capabilities and I/O specifications**.
- **Agent Action**: Check this file for problem input schemas, expected terminal states (**ALIVE**, **DEAD**, **SEKI**, **KO**), proof tree verification criteria, and performance requirements.

### 🥉 3. [`quantumgo_solver_agent_development_phases.md`](./quantumgo_solver_agent_development_phases.md)
- **Role**: **The mandatory step-by-step roadmap that dictates phase order for the agent**.
- **Agent Action**: Follow the phase sequence strictly (Phase 1 $\rightarrow$ Phase 2 $\rightarrow$ Phase 3 $\rightarrow$ Phase 4 $\rightarrow$ Phase 5 $\rightarrow$ Phase 6). Do not skip ahead or implement search logic before underlying state and cascade mechanics are verified with unit tests.

### 4. [`prd/`](./prd/) files (`PRD-01` through `PRD-05`)
- Supplementary product specifications and requirements breakdown.

### 5. Single-board reference implementation in [`study-LD-RZ-solver/`](./study-LD-RZ-solver/)
- C++ codebase for single-board RZS to adapt and extend.

---

## 3. Core Invariants & Rules Checklist

Before submitting code, ensure all the following invariants hold:

| Area | Rule / Invariant | Authoritative Source |
| :--- | :--- | :--- |
| **Boards** | Exactly two boards ($B_1$ and $B_2$). | [Coding Protocol §0.1](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Moves 1 & 2** | Move 1 is Black (one stone on $B_1$, one on $B_2$). Move 2 is White (one on $B_1$, one on $B_2$). Stored as entangled pairs. | [Coding Protocol §0.1](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Move 3+** | Played at identical coordinate $(x, y)$ on both $B_1$ and $B_2$. Illegal if illegal on either board. | [Coding Protocol §0.1](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Captures** | Capturing a stone removes its entangled partner on the opposite board immediately. | [Coding Protocol §0.2](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Cascades** | Partner removals can reduce neighboring liberties to 0, triggering recursive capture cascades. Must resolve to stable state. | [Coding Protocol §0.2](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Relevance Zone ($RZ_Q$)** | $RZ_Q = RZ_{B1} \cup RZ_{B2} \cup \text{EntangledPartners}(RZ)$. Expands when tactical moves touch boundaries. | [Coding Protocol §0.3](./QuantumGo%20Solver%20Coding%20Protocol.md) |
| **Search Tree** | Exact AND/OR proof tree search; terminal states must definitively evaluate ALIVE, DEAD, SEKI, or KO. | [Capability Spec §2](./quantumgo_solver_capability_specification.md) |

---

## 4. Phased Development Workflow

Follow the phase order defined in [`quantumgo_solver_agent_development_phases.md`](./quantumgo_solver_agent_development_phases.md):

- **Phase 1: Game State & Entanglement Data Structures**
  - Implement dual-board struct/classes (`QuantumBoardState`, `EntanglementTable`).
  - Add state cloning, hashing (Zobrist), and serialization.
- **Phase 2: Move Generation & Capture Cascade Engine**
  - Implement synchronized move validation.
  - Implement recursive cross-board capture resolution.
- **Phase 3: Quantum Relevance Zone ($RZ_Q$)**
  - Track active $RZ_Q$ bitboards / coordinate sets.
  - Implement dynamic expansion and null-move verification.
- **Phase 4: Exact Search Algorithm**
  - Adapt proof-number or alpha-beta AND/OR search with $RZ_Q$ filtering.
  - Produce solution variations and proof trees.
- **Phase 5: Test Suite & Benchmarks**
  - Create synthetic test cases for all capture cascade topologies.
  - Validate against classical Tsumego converted to QuantumGo variants.
- **Phase 6: Integration, Optimization, and Documentation**
  - CLI/API integration, profiling, and final documentation.

---

## 5. Coding & Testing Standards

1. **Language & Toolchain**: Modern C++ (C++17 / C++20) matching [`study-LD-RZ-solver/CMakeLists.txt`](./study-LD-RZ-solver/CMakeLists.txt).
2. **Determinism**: All search, state evaluation, and hashing must be 100% deterministic.
3. **Unit Tests First**: For each mechanic (e.g., cascade capture with 3 chained groups across $B_1 \leftrightarrow B_2$), write a minimal unit test before integrating into search.
4. **Git Hygiene**:
   - Write clear, concise commit messages (`feat: ...`, `fix: ...`, `test: ...`, `docs: ...`).
   - Keep working tree clean.
