# PRD 02: Move Generation and Legality

## 1. Move Phases
- **Opening Phase (Moves 1 & 2):** 
  - Move 1: Black plays one position on B1 and one independent position on B2.
  - Move 2: White plays one position on B1 and one independent position on B2.
  - Legality is checked independently per board for these first two moves.
- **Common Phase (Moves 3+):**
  - The player selects a single coordinate `P`.
  - The move is executed at `P` on *both* B1 and B2 simultaneously.

## 2. Legality Constraints
- **Synchronized Legality:** In the common phase, a move is only valid if it is legal on both boards: `Legal_Q(P) = Legal_B1(P) AND Legal_B2(P)`.
- **Validation Rules:** If `P` violates Go rules (occupancy, suicide, ko) on *either* board, the joint move is rejected entirely.
- **No Passing:** Pass moves are NOT permitted in these L&D solving scenarios. Every action must be an explicit coordinate placement.

## 3. Reversibility (Undo)
- Every generated move must be perfectly reversible to support efficient search tree traversal.
- `Undo` operations must exactly restore B1/B2 stone layouts, reinstate captured/removed stones, reconstruct the 1-to-1 entanglement pairs, and revert ko/turn states.
