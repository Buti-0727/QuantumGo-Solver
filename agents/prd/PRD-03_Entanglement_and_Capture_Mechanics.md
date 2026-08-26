# PRD 03: Entanglement and Capture Mechanics

## 1. Direct Capture Execution
- A standard Go capture (group liberties reach 0) applies independently to B1 and B2 upon placing a stone.
- **Simultaneous Resolution:** If a common-phase move directly captures stones on *both* boards, all of these direct captures are resolved and removed simultaneously before any cross-board effects are processed.

## 2. Entanglement Cascade (The Unified Queue)
- **Trigger:** When a stone is captured and removed from the board, its entangled partner on the opposite board must also be removed.
- **Unified Queue:** Partner removals triggered by simultaneous direct captures are placed into a unified processing queue.
- **Recursive Cascade:**
  1. Remove the entangled partner stone(s) mandated by the queue.
  2. Check if this removal causes any adjacent enemy groups on that board to drop to 0 liberties.
  3. If new captures occur, process them and add *their* entangled partners to the unified queue.
  4. Repeat until the queue is empty and the joint state reaches stability.

## 3. Edge Cases in Cascades
- **Pre-captured Partners:** If the cascade queue mandates removing a partner stone that was *already* captured or removed earlier in the exact same cascade sequence, the action is safely ignored.
- **State Integrity:** Entanglement links are permanently severed once resolved during a cascade; they must not re-trigger.
