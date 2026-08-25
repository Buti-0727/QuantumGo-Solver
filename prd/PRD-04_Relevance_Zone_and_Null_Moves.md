# PRD 04: Relevance Zone and Null Moves

## 1. The Quantum Relevance Zone (RZ_Q)
- RZ_Q dictates the subset of intersections on B1 and B2 that mathematically matter to the survival or death of the L&D target.
- Unlike traditional single-board RZS, RZ_Q can be spatially disjointed, spanning isolated areas across both boards connected purely by entanglement physics.

## 2. Initialization (Entanglement-Aware Seeding)
- Before the search begins, RZ_Q is seeded comprehensively.
- **Initial State:** Includes the physical L&D target stones, their immediate surrounding liberties, **plus** all stones directly connected to the target via entanglement links (and their respective surrounding liberties).

## 3. Dynamic RZ Expansion
- **Physical Expansion:** As the search explores deeper, local tactical interactions (e.g., a group losing liberties) will expand RZ_Q to include neighboring blocks.
- **Quantum Expansion:** If RZ_Q physically expands to include a stone that possesses an entanglement link, the RZ_Q automatically and instantly propagates across that link to include the partner stone on the opposite board.

## 4. Move Filtering and Null Moves
- **Candidate Moves:** The move generator only emits legal coordinates that fall inside the current RZ_Q.
- **Irrelevant Moves:** Any legal move outside RZ_Q is deemed a "null move" (it cannot affect the target's fate). The RZS framework skips these moves to bypass combinatorial explosion, searching only the relevant subspace while maintaining exact-solving mathematical integrity.
