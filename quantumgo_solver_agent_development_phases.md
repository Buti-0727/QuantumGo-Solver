# QuantumGo Life-and-Death Solver — Agent Development Phases

## Global Instructions for Every Agent

Before modifying any code, understand these two principles:

### Principle 1 — QuantumGo Rules Are Authoritative

The implementation must follow the project's QuantumGo rules exactly:

- There are two boards: B1 and B2.
- Only moves 1 and 2 are quantum opening moves.
- Move 1 is Black's quantum move.
- Move 2 is White's quantum move.
- Each opening move places the player's stones at two independently selected coordinates, one on each board.
- Those two stones form an entangled pair.
- From move 3 onward, a move consists of one coordinate.
- That coordinate is played simultaneously on B1 and B2.
- A common-phase move is legal only if that coordinate is legal on BOTH boards.
- Normal Go captures occur locally.
- When a stone belonging to an entangled pair is captured, its partner is automatically removed from the other board.
- Cross-board capture propagation continues until the position is stable.
- There is no collapse, measurement, or selection of one board.
- Both boards remain part of the game permanently.
- Any existing repository documentation whose opening convention conflicts with these rules must NOT override these QuantumGo rules.

### Principle 2 — This Is a Life-and-Death Solver

This project is NOT a general-purpose QuantumGo engine.

The solver's job is to determine whether a specified target can:

- live, or
- be killed

under optimal play.

The implementation must therefore be organized around:

- an L&D problem,
- a target,
- attacker/defender objectives,
- exact search,
- terminal life/death conditions,
- relevance-zone search.

Do NOT turn the project into a full-game scoring engine.

Do NOT make final territory scoring the central objective.

Do NOT search the complete QuantumGo game from move 1 unless specifically required for a test case.

The normal workflow should be:

    QuantumGo L&D Problem
            ↓
    Initial Quantum Position
            ↓
    Target + Objective
            ↓
    Quantum Relevance Zone
            ↓
    Relevant search
            ↓
    Exact life/death result

# Phase 0 — Understand the Existing RZS Solver

## Objective

Understand the architecture of `study-LD-RZ` before writing QuantumGo code.

## Agent Tasks

The agent must inspect and document:

- Board representation
- Group and liberty representation
- Move generation
- Capture handling
- Ko handling
- Board state copying/undo
- Search node representation
- Candidate generation
- Relevance-zone generation
- Relevance-zone expansion
- Null-move handling
- Terminal L&D evaluation
- UCA-related logic
- Transposition table
- Pattern table
- MCTS/search components
- Problem input
- Solution-tree generation

## Required Output

Produce an internal architecture map showing:

    Existing L&D problem
        ↓
    Board state
        ↓
    Candidate generation
        ↓
    RZ
        ↓
    Search
        ↓
    L&D result

The agent must identify which parts are:

- QuantumGo-specific
- ordinary Go-specific
- RZS-specific
- reusable without modification

## Critical Restriction

Do NOT begin implementation before understanding how the existing solver decides:

> "This target is alive/dead."

The project must remain an extension of the existing L&D solver.

# Phase 1 — Define the QuantumGo L&D Problem

## Objective

Create the formal representation of a QuantumGo life-and-death problem.

The solver must start from an already-established position, just as a normal tsumego solver does.

## Required State

A QuantumGo problem must contain:

- B1 position
- B2 position
- entanglement relationships
- player to move
- target stones/groups
- attacker/defender role
- L&D objective
- ko rule
- board size
- any additional information required by the existing RZS solver

Conceptually:

    QuantumLDProblem
        ├── Board 1
        ├── Board 2
        ├── Entanglement
        ├── Player to move
        ├── Target
        ├── Objective
        └── Rules

## Critical Requirement

The target must be represented as a QuantumGo L&D target.

Do NOT assume:

    target = one ordinary Go group on one board

The target may depend on:

- groups on B1,
- groups on B2,
- entangled stones,
- cross-board capture consequences.

## Important

The 5–10 move complete game supplied by the project owner should be used to construct and validate example QuantumGo L&D positions.

It is NOT the specification of the solver architecture.

# Phase 2 — Implement the QuantumGo State Model

## Objective

Extend the existing Go state model into a joint QuantumGo state.

The state must contain:

    B1
    B2
    Entanglement Map
    Side to Move
    Relevant game history / ko information

## Required Capabilities

The state must support:

- reading B1,
- reading B2,
- placing stones,
- removing stones,
- identifying groups,
- identifying liberties,
- identifying entangled partners,
- modifying entanglement relationships,
- copying state,
- restoring state.

## Critical Requirement

B1 and B2 must NOT be treated as two independent games.

The solver must regard them as one joint state.

# Phase 3 — Implement Exact QuantumGo Move Semantics

## Objective

Implement the project's QuantumGo rules exactly.

## Opening Moves

The state model must recognize:

    Move 1:
        Black B1[p1] + B2[p2]

    Move 2:
        White B1[p3] + B2[p4]

The two coordinates of each opening move are checked independently.

## Common Phase

From move 3 onward:

    Move = coordinate p

and the move attempts:

    B1[p]
    B2[p]

The move is legal only when:

    Legal(B1, p) AND Legal(B2, p)

## Required Tests

The agent must test:

- legal on both → legal
- illegal on B1 → illegal
- illegal on B2 → illegal
- illegal on both → illegal

## Critical Restriction

Do NOT introduce alternative QuantumGo interpretations.

Do NOT implement:

- measurement,
- collapse,
- probabilistic board selection,
- "choose one surviving board",
- separate winners for B1 and B2.

# Phase 4 — Implement Entangled Capture Propagation

## Objective

Implement the defining cross-board tactical mechanic.

## Required Behaviour

If:

    B1[A] ↔ B2[B]

and B1[A] is captured:

    remove B1[A]
        ↓
    remove B2[B]
        ↓
    evaluate consequences on B2
        ↓
    propagate any resulting captures
        ↓
    continue until stable

The same applies in the opposite direction.

## Requirements

The agent must correctly support:

- single entangled captures,
- multiple simultaneous captured stones,
- capture cascades,
- multiple entangled pairs,
- partner already removed,
- cascades that return to the original board.

## Critical Requirement

Capture propagation is part of the QuantumGo state transition.

It must be deterministic.

There is no player choice during propagation.

# Phase 5 — Implement Exact Undo and State Restoration

## Objective

Make every QuantumGo transition completely reversible for search.

For:

    play(move)
    ...
    undo(move)

The state after `undo()` must be exactly identical to the state before `play()`.

The restoration must include:

- B1
- B2
- captured stones
- entanglement links
- side to move
- ko state
- search-relevant metadata
- hash state

## Critical Requirement

Do not optimize undo before correctness is proven.

First establish:

    state_before == state_after_undo

for thousands of automatically generated test positions.

# Phase 6 — Implement QuantumGo State Hashing

## Objective

Make QuantumGo states usable by the existing transposition-table/search infrastructure.

The state identity must account for:

- B1 position
- B2 position
- entanglement structure
- player to move
- relevant ko/history state

## Critical Test

These must be treated as DIFFERENT states:

    State A:
        B1[D4] ↔ B2[C3]

    State B:
        B1[D4] ↔ B2[F4]

even if the visible stone layouts are identical.

## Required Property

Equivalent states reached through different move orders should be recognized when the rules permit transposition equivalence.

# Phase 7 — Define QuantumGo L&D Terminal Conditions

## Objective

Adapt the solver's L&D termination logic to QuantumGo.

The solver must determine when the target has become:

- demonstrably dead,
- demonstrably alive,
- or still unresolved.

## Critical Requirement

Do NOT use ordinary board scoring.

The question is:

> Can the target be forced alive or dead?

not:

> Who owns more territory?

## Quantum Dependency

A target's status may depend on both boards because an entangled capture can alter the target on the other board.

Therefore:

    L&D(B1 target)

must NOT be evaluated independently from:

    L&D(B2)

# Phase 8 — Define Quantum Unconditional Life / Death

## Objective

Adapt the existing solver's unconditional-result concepts to the joint QuantumGo state.

The agent must formally define what constitutes:

- Quantum unconditional life
- Quantum unconditional death

The definition must account for:

- local Go liberties,
- eyes,
- capture threats,
- entangled partner removal,
- cross-board capture chains.

## Required Deliverable

Write a formal definition before implementation.

The implementation must follow the definition exactly.

Do not simply reuse normal-Go UCA logic without proving that it remains valid.

# Phase 9 — Design the Quantum Relevance Zone

## Objective

Extend the central RZS concept to QuantumGo.

Normal Go:

    relevant board positions

QuantumGo:

    relevant B1 positions
    +
    relevant B2 positions
    +
    entanglement relationships affecting those positions

## Required Property

Relevance must be able to propagate through:

### Local Go interactions

    B1[A] → B1[B]

### Entanglement interactions

    B1[A] ↔ B2[C]

Therefore:

    RZ(B1)
        ↓
    entangled partner
        ↓
    RZ(B2)

## Key Concept

The Quantum RZ should be the smallest region sufficient to prove the L&D result, subject to the RZS methodology.

Do NOT simply take the entire board.

Do NOT automatically take the same RZ on both boards.

# Phase 10 — Implement Dynamic Quantum RZ Expansion

## Objective

Preserve the defining RZS property:

> The relevance zone expands only when search proves that additional positions matter.

The solver should:

1. Construct an initial Quantum RZ.
2. Search relevant moves.
3. Detect when the current RZ is insufficient.
4. Expand the RZ.
5. Continue the proof.

## Entanglement Rule

When a relevant stone has an entangled partner, the partner and any tactically necessary surrounding positions may need to enter the Quantum RZ.

However:

> Entanglement alone does not automatically imply that the entire surrounding board is relevant.

Relevance must remain goal-directed.

# Phase 11 — Adapt Candidate Generation

## Objective

Modify the existing candidate-generation mechanism so that candidates are generated for QuantumGo L&D search.

A candidate can be relevant because it:

- affects the target locally,
- affects a relevant group,
- creates/removes a liberty,
- affects an eye,
- captures an entangled stone,
- triggers a cross-board capture,
- changes the Quantum RZ,
- or is otherwise necessary for the L&D proof.

## Common-Phase Restriction

Every candidate coordinate must satisfy the simultaneous legality rule:

    Legal(B1, p) AND Legal(B2, p)

## Critical Requirement

Do NOT replace RZS candidate generation with:

    "search every legal QuantumGo move."

That would defeat the purpose of the RZS solver.

# Phase 12 — Adapt Null-Move / Irrelevance Logic

## Objective

Preserve the existing RZS idea that moves proven irrelevant to the current L&D objective need not be searched normally.

For QuantumGo, the irrelevance test must account for cross-board entanglement.

A move that is geographically distant from the target may still be relevant if:

    move
      ↓
    affects relevant stone
      ↓
    entangled partner
      ↓
    target consequence on other board

Therefore the solver must not classify a move as irrelevant using single-board distance alone.

# Phase 13 — Integrate With the Existing L&D Search

## Objective

Connect the QuantumGo state and Quantum RZ to the existing search architecture.

The search node should conceptually represent:

    QuantumGo State
        +
    L&D Objective
        +
    Quantum RZ
        +
    Search information

Reuse existing search infrastructure wherever possible.

Do NOT rewrite the entire RZS algorithm simply to support two boards.

The implementation should modify the game-specific assumptions while preserving the L&D-oriented search architecture.

# Phase 14 — Implement Exact Quantum L&D Solving

## Objective

Produce an exact answer to the L&D problem.

The solver must be able to return:

    LIVE

or:

    DEAD

and identify the winning side.

For a kill problem:

    Can attacker force death?

For a life problem:

    Can defender force life?

The solver must support optimal play from both sides.

# Phase 15 — Generate Quantum Solution Trees

## Objective

Produce a human-readable proof/variation of the result.

The output should contain:

- winning move,
- best defense,
- winning continuation,
- terminal L&D result,
- relevant QuantumGo consequences.

For example:

    1. D5
       1... C4
       2. E5

       Result:
       Target DEAD

Where appropriate, the explanation should explicitly identify:

    B1 capture
        ↓
    entangled B2 removal
        ↓
    resulting tactical collapse

This makes the solver useful for research validation rather than merely producing a Boolean answer.

# Phase 16 — Build a QuantumGo L&D Test Suite

## Objective

Validate correctness before performance optimization.

Tests must include:

### State tests

- B1/B2 initialization
- entanglement creation
- entanglement removal
- state copy
- state restoration

### Rule tests

- move 1 legality
- move 2 legality
- common-phase legality
- suicide
- ko
- simultaneous move legality

### Capture tests

- B1 → B2 propagation
- B2 → B1 propagation
- multi-step cascades
- multiple entangled pairs

### L&D tests

- trivial life
- trivial death
- forced kill
- forced life
- cross-board tactical dependence
- positions where B1 and B2 cannot be solved independently

### RZS tests

- initial Quantum RZ
- entanglement-based RZ propagation
- dynamic RZ expansion
- irrelevant-move handling
- Quantum null moves

# Phase 17 — Validate Against the Provided 5–10 Move Games

## Objective

Use the complete QuantumGo game supplied by the project owner as a correctness benchmark.

The agent must:

1. Parse the game.
2. Reconstruct B1 and B2 after every move.
3. Reconstruct all entanglement relationships.
4. Verify every capture.
5. Verify every propagated capture.
6. Confirm common-phase legality.
7. Identify useful L&D positions from the game.

The game is a validation dataset.

It is NOT a replacement for formal QuantumGo rules.

# Phase 18 — Performance Optimization

## Objective

Only after correctness is established, optimize the solver.

Potential optimization targets:

- Bitboards
- Incremental liberty updates
- Incremental hashes
- Transposition tables
- Candidate caching
- RZ caching
- Capture propagation optimization
- Search ordering
- Pattern reuse
- Parallel search where compatible

Optimization must NEVER change the L&D semantics.

Correctness comes first.

# Phase 19 — Research Evaluation

## Objective

Evaluate whether Quantum RZS actually works as an extension of the original RZS methodology.

Compare:

    Normal Go RZS
    vs.
    QuantumGo RZS

Measure:

- solving time
- searched nodes
- effective branching factor
- RZ size
- RZ expansion count
- null-move count
- transposition-table hit rate
- maximum search depth
- number of entanglement propagations
- number of cross-board captures

The primary question should be:

> Does relevance-zone search remain effective when relevance can propagate through QuantumGo entanglement?

# Phase 20 — Final Deliverable

The completed system should be able to take:

    QuantumGo L&D problem
        ↓
    solve exactly
        ↓
    return LIVE / DEAD
        ↓
    return winning variation
        ↓
    return Quantum RZ
        ↓
    return search statistics

The final system should NOT be described as:

    "a QuantumGo game engine"

It should be described as:

    "an exact QuantumGo life-and-death solver
     based on relevance-zone search."

# Non-Negotiable Constraints

Every implementation agent must stop and reconsider the design if it introduces any of the following:

- Treating B1 and B2 as independent games
- Independent winners for B1 and B2
- Separate scoring of the two boards
- Collapse or measurement
- Probabilistic QuantumGo states
- Reverting to a different opening-colour convention
- Allowing a common-phase move when it is illegal on either board
- Ignoring entanglement during capture
- Ignoring entanglement during relevance analysis
- Searching the entire board as the default RZS strategy
- Replacing exact L&D solving with a general position evaluator
- Turning the project into a full-game AI before establishing the L&D solver

The implementation must always return to the core model:

    TWO BOARDS
        +
    ENTANGLEMENT
        +
    QUANTUMGO LEGALITY
        +
    LIFE-AND-DEATH OBJECTIVE
        +
    RELEVANCE-ZONE SEARCH
        =
    QUANTUMGO L&D SOLVER
