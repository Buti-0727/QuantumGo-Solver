# PRD 01: Game State Representation

## 1. Core State Components
The QuantumGo state is a singular joint entity representing:
- **Board 1 (B1):** Standard Go grid tracking intersections and stone colors.
- **Board 2 (B2):** Secondary Go grid, identical in size to B1.
- **Side to Move:** Current player (Black or White).
- **Ko/History:** Relevant state data to enforce ko rules across the joint boards.

## 2. Entanglement Model
- **Topology:** Entanglement is strictly **1-to-1**. A single stone on B1 links to exactly one stone on B2.
- **Tracking:** The state must bidirectionally map `B1[coord] ↔ B2[coord]`.
- **Lifecycle:** The link is created during play and severed immediately when either linked stone is removed from the board.

## 3. L&D Target Representation
- The target is treated as a unified "QuantumGo object".
- It may consist of stones on B1, stones on B2, or a combination of both, including their cross-board dependencies.

## 4. State Hashing
- Game identity relies on more than just physical stone placement. 
- `Hash = B1_State + B2_State + 1:1_Entanglement_Map + Side_To_Move + Ko_State`.
- Identical board configurations with different entanglement pairings MUST generate distinct hash values.
