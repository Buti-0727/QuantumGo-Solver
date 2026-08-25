# QuantumGo Life-and-Death Solver — Capability Specification

## 1. QuantumGo Position Representation

The solver must be able to represent a complete QuantumGo L&D position consisting of:

- Two simultaneous Go boards:
  - Board 1 (B1)
  - Board 2 (B2)
- Stone colour and position on both boards
- Side to move
- Entanglement relationships between stones
- Target group(s) relevant to the L&D problem
- L&D objective:
  - Kill
  - Live
- Ko state / relevant game history

The two boards must be treated as one joint game state rather than as two independent Go positions.

## 2. Quantum Entanglement Management

The solver must maintain explicit entanglement relationships.

It must be able to:

- Create an entangled pair.
- Identify the partner of any entangled stone.
- Determine whether a stone is currently entangled.
- Remove an entanglement relationship when a stone disappears.
- Track entanglement across B1 and B2.
- Preserve entanglement information during search and undo.

For example:

    B1[D4] ↔ B2[C3]

must remain a relationship in the search state.

## 3. QuantumGo Move Generation

### Opening moves

The solver must understand the special first two QuantumGo moves:

- Move 1: Black chooses one position on B1 and one on B2.
- Move 2: White chooses one position on B1 and one on B2.

Both placements must independently satisfy Go legality.

### Common phase

From move 3 onward:

- Generate one coordinate `P`.
- Test `P` on B1.
- Test `P` on B2.
- The move is legal only if it is legal on BOTH boards.

Therefore:

    Legal_Q(P) =
        Legal_B1(P) AND Legal_B2(P)

For an L&D solver, the opening moves normally do not need to be searched from the beginning; the solver can receive an already-established QuantumGo position.

## 4. QuantumGo Move Execution

The solver must correctly execute a QuantumGo move on the joint state.

For a common-phase move:

    P
    ↓
    B1[P]
    B2[P]

The solver must:

- Place the appropriate stones.
- Detect captures independently on each board.
- Apply normal Go capture rules.
- Detect entangled stones among captured stones.
- Propagate captures through entanglement.
- Continue propagation until the position reaches a stable state.

## 5. Cross-Board Capture Propagation

This is a core QuantumGo capability.

If:

    B1[A] ↔ B2[B]

and B1[A] is captured, the solver must automatically remove B2[B].

The solver must then check whether removing B2[B] causes another capture.

This process must continue recursively until no additional consequences exist.

Conceptually:

    Local capture
        ↓
    Entangled partner removed
        ↓
    New local capture?
        ↓
    Entangled partner removed
        ↓
    ...
        ↓
    Stable QuantumGo position

The solver must correctly handle multi-step cross-board capture cascades.

## 6. Legal-Move Verification

The solver must verify:

- Occupied intersections
- Suicide
- Capture
- Ko
- Any other selected Go legality rules
- Simultaneous legality on B1 and B2 during the common phase

A move that is legal on only one board must be rejected.

## 7. QuantumGo State Undo / Rollback

Every search move must be reversible.

The solver must be able to:

    Apply move
        ↓
    Search child state
        ↓
    Undo move
        ↓
    Restore EXACT previous state

Undo must restore:

- B1 stones
- B2 stones
- Captured stones
- Entanglement relationships
- Ko state
- Side to move
- Hash value
- Any L&D-specific state

This is essential for efficient tree search.

## 8. QuantumGo State Hashing

The solver must have a unique/reliable representation of a QuantumGo state for:

- Transposition tables
- Duplicate-state detection
- Search caching

The hash must represent more than the two board positions.

Conceptually:

    QuantumHash =
        B1 state
        + B2 state
        + entanglement structure
        + side to move
        + relevant ko/history information

Two positions with identical stone layouts but different entanglement relationships must be treated as different states.

Example:

    State A:
        B1[D4] ↔ B2[C3]

    State B:
        B1[D4] ↔ B2[F4]

must NOT have the same game-state identity.

## 9. Quantum Target Representation

The solver must represent the L&D target as a QuantumGo object.

Unlike normal Go, the target may involve:

- A group on B1
- A group on B2
- Entangled stones
- Cross-board tactical dependencies

The solver must therefore be able to determine which stones are relevant to the target's survival or capture.

## 10. Quantum Life-and-Death Evaluation

The solver must answer:

### Kill problem

    Can the attacker force the target to die?

### Life problem

    Can the defender force the target to survive?

The evaluation must consider the complete joint state.

It must NOT simply run:

    L&D(B1)
    +
    L&D(B2)

independently.

A tactical event on B1 may change the outcome on B2 through entanglement.

## 11. Quantum Unconditional Life / Terminal-State Detection

The solver must determine when an L&D result has become established.

It should support QuantumGo equivalents of terminal L&D conditions such as:

- Target is unconditionally alive.
- Target is unconditionally dead.
- Attacker has established a forced kill.
- Defender has established a forced life result.

The exact definition of QuantumGo unconditional life/death should be explicitly defined for the project rather than inherited blindly from normal Go.

## 12. Quantum Relevance Zone (RZ)

The solver must adapt the Relevance-Zone Search principle from normal Go.

Instead of:

    RZ = relevant positions on one board

The QuantumGo solver should maintain:

    RZ_Q =
        relevant positions on B1
        +
        relevant positions on B2
        +
        entanglement-related positions

The RZ must be able to expand dynamically during search.

## 13. Cross-Board Relevance Propagation

A position can become relevant because of either:

### Local Go interaction

    B1[A] → B1[B]

or:

### Entanglement interaction

    B1[A] ↔ B2[C]

Therefore:

    RZ(B1)
        ↓
    entangled partner
        ↓
    RZ(B2)

The solver must automatically propagate relevance across entanglement links.

This is one of the most important new capabilities compared with the original RZS solver.

## 14. Relevant-Move Generation

The solver should NOT necessarily search every legal board coordinate.

Instead, it should:

1. Identify the current Quantum RZ.
2. Generate moves within the RZ.
3. Search relevant moves normally.
4. Treat demonstrably irrelevant moves according to the RZS/null-move framework.
5. Expand the RZ when tactical analysis shows that additional positions matter.

This preserves the fundamental efficiency principle of `study-LD-RZ`.

## 15. Quantum Null-Move Handling

The solver should be able to identify moves that cannot affect the current L&D objective.

Such moves may be treated as null/irrelevant moves when justified by the RZS framework.

However, a move must NOT be considered irrelevant merely because it is far away on one board.

It may become relevant through:

    B1 position
        ↓
    entanglement
        ↓
    B2 position
        ↓
    target interaction

Therefore QuantumGo requires a stronger relevance test than normal Go.

## 16. Search Tree

The solver must construct a search tree in which each node represents:

    QuantumGo Position
        +
    L&D Objective
        +
    Quantum RZ information

Each edge represents a legal QuantumGo move.

The search must support:

- Alternating players
- Forced variations
- Capture sequences
- Cross-board consequences
- Transpositions
- Terminal L&D states

## 17. Exact L&D Solving

The final solver should provide an exact result rather than merely a heuristic evaluation.

For example:

    Target: BLACK group on B1
    Objective: KILL
    Result: WHITE CAN FORCE KILL

or:

    Target: BLACK quantum group
    Objective: LIVE
    Result: BLACK CAN FORCE LIFE

The solver should also provide the corresponding winning variation.

## 18. Principal Variation / Solution Tree

The solver should be able to output:

- Winning move
- Opponent's best response
- Winning continuation
- Terminal result

Example:

    1. Q[D4]
       ├── 1...C5
       │     └── 2. Q[E4] → Kill
       │
       └── 1...E5
             └── 2. Q[C4] → Kill

## 19. RZ / Search Statistics

For research purposes, the solver should record:

- Number of searched nodes
- Number of generated moves
- Number of relevant moves
- Number of null moves
- Maximum search depth
- RZ size on B1
- RZ size on B2
- Number of entanglement propagations
- Number of cross-board captures
- Number of transposition-table hits
- Total solving time

These statistics will allow comparison between:

    Normal RZS
    vs.
    Quantum RZS

## 20. Problem Input / Output

The solver should have a machine-readable L&D problem format containing at least:

- Board size
- B1 position
- B2 position
- Entanglement pairs
- Player to move
- Target stones/groups
- Objective
- Ko rule
- Optional search parameters

Example:

    {
        "board_size": 9,
        "board1": "...",
        "board2": "...",
        "entanglement": [
            ["D4", "C3"]
        ],
        "to_move": "W",
        "target": "B1:D4",
        "objective": "kill"
    }

## 21. Human-Readable Solution

The solver should be able to explain a solution in a form understandable to a Go researcher:

    Problem:
        White to kill the QuantumGo target.

    Result:
        WHITE WINS

    Winning variation:
        1. D5
        1... C4
        2. E5

    Critical mechanism:
        The capture on B1 removes the entangled stone
        on B2, causing the second group to lose its
        final liberty.

This is particularly useful for validating the research results.

## 22. Compatibility With the Existing RZS Solver

The QuantumGo implementation should reuse as much of the original `study-LD-RZ` framework as possible.

The desired architecture is:

    Existing RZS
          │
          ├── Search framework
          ├── Candidate generation
          ├── RZ mechanism
          ├── Transposition tables
          ├── L&D search logic
          └── Solution generation
                    │
                    ▼
             QuantumGo adapter
                    │
          ┌─────────┴─────────┐
          │                   │
       Board 1             Board 2
          │                   │
          └─────────┬─────────┘
                    │
             Entanglement layer

The goal should be to MODIFY the game-specific components rather than rewrite the entire RZS solver.

## 23. Validation / Test Suite

The solver should include dedicated QuantumGo tests for:

### Basic tests

- Two-board representation
- Opening quantum moves
- Shared moves
- Occupancy
- Suicide
- Ko

### Entanglement tests

- Single cross-board capture
- Multiple entangled captures
- Capture cascade
- Partner already captured
- Multiple entangled pairs

### RZS tests

- Initial RZ construction
- Cross-board RZ propagation
- RZ expansion
- Irrelevant move detection
- Quantum null moves

### L&D tests

- Forced kill
- Forced life
- Seki-like situations
- Cross-board life/death dependency
- Positions where solving B1 and B2 independently gives the WRONG result

The last category is especially important: it demonstrates why a QuantumGo solver is necessary.

## 24. Research Comparison

The completed system should allow experiments comparing:

| Capability | Normal RZS | Quantum RZS |
|---|---:|---:|
| Single-board L&D | ✓ | ✓ |
| Two-board state | — | ✓ |
| Entanglement | — | ✓ |
| Cross-board capture | — | ✓ |
| Cross-board RZ | — | ✓ |
| Quantum null moves | — | ✓ |
| Exact L&D solving | ✓ | ✓ |
| Solution tree | ✓ | ✓ |
| Search statistics | ✓ | ✓ |

The primary research question should be:

> **Can the Relevance-Zone Search framework be extended to efficiently solve exact life-and-death problems in QuantumGo?**

## Minimum Viable Solver

The first working version does NOT need every capability above.

The minimum scientifically meaningful version should have:

1. Two-board state
2. Entanglement map
3. Correct QuantumGo move generation
4. Cross-board capture propagation
5. Quantum state hashing
6. Quantum target representation
7. Quantum L&D terminal evaluation
8. Quantum Relevance Zone
9. Cross-board RZ propagation
10. RZS search
11. Exact kill/live result
12. Winning variation
13. Search statistics

Everything else can be added afterward.

## Core Concept

The central design principle should be:

    Normal RZS
        ↓
    Single-board relevance
        ↓
    Quantum RZS
        ↓
    Two-board + entanglement relevance

The goal is NOT to build:

    "A QuantumGo engine that happens to solve L&D."

The goal is to build:

    "An RZS-based exact life-and-death solver
     whose game state is QuantumGo."

That distinction should guide the entire implementation.
