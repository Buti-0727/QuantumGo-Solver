# PRD 05: Life-and-Death Objective and Evaluation

## 1. Solver Objectives
- The engine operates as an exact solver targeting one of two outcomes for a specific QuantumGo target:
  - **Kill:** Can the attacking side force the target's destruction?
  - **Live:** Can the defending side force the target's survival?
- Heuristic approximations are not acceptable; the solver must deliver a mathematical proof via its search tree.

## 2. Terminal State Detection (Unconditional Life)
- To prune the search tree efficiently, the solver recognizes "Unconditional Life" through a combination of standard static pattern recognition and strict entanglement verification.
- **Criteria:** A target group is unconditionally alive if and only if:
  1. It possesses at least two irremovable eyes on its local board.
  2. **None** of the stones structurally necessary to maintain those eyes are entangled with vulnerable stones on the opposite board.

## 3. Solution Output and Validation
- Upon solving, the engine must return:
  - The exact L&D result (e.g., `WHITE CAN FORCE KILL`).
  - The Principal Variation (PV) demonstrating the winning sequence of synchronized moves.
  - A trace of critical quantum mechanics (e.g., explicitly noting when a cross-board capture removed a vital defender stone).
- **Research Metrics:** To compare Quantum RZS against standard RZS, the output must report search depth, node count, maximum RZ size per board, and the frequency of cross-board capture propagations.
