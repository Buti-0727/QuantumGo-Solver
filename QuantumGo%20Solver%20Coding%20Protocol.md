# QuantumGo Solver Coding Protocol

## Purpose

This document is the implementation protocol for coding agents working on the QuantumGo Life-and-Death (L&D) solver based on the `study-LD-RZ-solver` folder.

The implementation must extend the repository's **Relevance-Zone-based exact life-and-death solving approach** to the project's QuantumGo rules.

This is **not** a protocol for building a general-purpose QuantumGo game engine.

The final product is an **exact QuantumGo life-and-death solver**.

---

# 0. Non-Negotiable Rules

Every coding agent MUST treat the following as authoritative.

## 0.1 QuantumGo Rules

- There are exactly two persistent boards: B1 and B2.
- Only moves 1 and 2 are quantum opening moves.
- Move 1 is Black's quantum move.
- Move 2 is White's quantum move.
- Each opening quantum move selects two distinct intersections:
  - one on B1,
  - one on B2.
- Each selected intersection receives a stone of the moving player's colour.
- The two stones created by the same opening move are an entangled pair.
- From move 3 onward, a move consists of exactly one coordinate.
- The same coordinate is played simultaneously on B1 and B2.
- A common-phase move is legal only if that coordinate is legal on BOTH boards.
- Normal Go legality applies on each board, including occupancy, suicide, and the chosen ko rule.
- Captures occur locally according to Go mechanics.
- If one stone of an entangled pair is captured, its partner is automatically removed on the other board.
- Cross-board capture propagation continues until no further consequences occur.
- There is no collapse, measurement, probabilistic board selection, or choice of surviving reality.
- B1 and B2 always remain present and jointly define one game state.
- Opening-colour conventions found in unrelated repositories or conflicting implementations MUST NOT override these rules.

## 0.2 Life-and-Death Scope

The solver's job is to answer a specified L&D problem:

- Can the attacker force the target dead?
- Can the defender force the target alive?

The solver is not primarily a full-game scoring engine.

Do not redesign the project around:

- final territory scoring,
- independent winners for B1 and B2,
- complete-game self-play,
- a general QuantumGo evaluator.

The architecture must stay centered on:

    L&D Problem
        -> QuantumGo State
        -> Quantum Target / Objective
        -> Quantum Relevance Zone
        -> Exact Search
        -> LIVE / DEAD result

---

# 1. Repository First, Code Second

Before writing implementation code, the agent MUST inspect the existing `study-LD-RZ` repository and identify the actual code paths for:

- board representation,
- group/liberty handling,
- move application,
- capture handling,
- ko handling,
- undo/rollback,
- candidate generation,
- relevance-zone construction and expansion,
- null/irrelevant move handling,
- L&D terminal evaluation,
- search nodes,
- transposition tables,
- problem input,
- solution-tree output.

The repository contains the core engine under `CGI/` and uses tsumego/L&D problem input and solver output. Reuse its architecture rather than replacing it wholesale.

The agent MUST produce a short repository map before major modifications.

Example format:

    Existing component              QuantumGo adaptation
    ----------------------------------------------------
    Board state                     Joint B1/B2 state
    Move generation                 Quantum move generation
    Capture                         Local + entangled propagation
    RZ                              Quantum RZ
    Target                          Quantum L&D target
    Terminal evaluation             Quantum L&D terminal test
    Hash                            Joint state + entanglement

Do not guess the implementation location when the repository can be inspected directly.

---

# 2. Preserve Existing Normal-Go L&D Behavior

The default normal-Go solver behavior must remain unchanged unless a feature is explicitly selected for QuantumGo.

Preferred architecture:

    Existing normal-Go L&D path
              |
              +---- unchanged
              |
              +---- QuantumGo-specific state/game adapter

Do not contaminate normal-Go logic with QuantumGo assumptions if a clean abstraction or subclass/adapter can avoid it.

A QuantumGo change is unacceptable if it silently changes results for the existing normal-Go tsumego suite.

---

# 3. Establish a QuantumGo Abstraction Boundary

The implementation should introduce a clearly identifiable QuantumGo layer.

A conceptual design is:

    QuantumGoProblem
        |
        v
    QuantumGoState
        |
        +-- BoardState B1
        +-- BoardState B2
        +-- EntanglementManager
        +-- SideToMove
        +-- Ko/History State
        |
        v
    QuantumGoMoveGenerator
        |
        v
    QuantumGoTransition
        |
        v
    Quantum L&D / Quantum RZS adapter

The exact class names may differ to fit the repository's existing conventions.

Do not create duplicate implementations of core Go rules if the repository already provides a correct reusable implementation.

---

# 4. QuantumGo Problem Input

The solver must accept an already-established QuantumGo L&D position.

The input must represent at least:

- board size,
- B1 position,
- B2 position,
- entanglement pairs,
- player to move,
- target stones/groups,
- L&D objective (LIVE or KILL),
- ko rule,
- any existing problem metadata required by the original solver.

A conceptual representation is:

```text
QuantumGoProblem
  board_size
  board1
  board2
  entanglements
  to_move
  target
  objective
  ko_rule
```

The exact file format should follow the conventions of `study-LD-RZ` wherever practical.

Do not force QuantumGo L&D problems to reconstruct moves 1–2 unless a specific test requires replaying an opening sequence.

---

# 5. QuantumGo State Representation

Implement a single joint state object that owns or references:

```text
B1 state
B2 state
entanglement mapping
side to move
ko/history state
```

The state must have deterministic transitions.

## Required invariants

At all times:

1. Every occupied intersection has exactly one stone colour.
2. Every entanglement edge refers to valid paired stones unless the pair has just been removed and cleaned up.
3. No stone is entangled with more than one partner unless the formal QuantumGo rules are later extended to permit it.
4. The B1/B2 mapping is symmetric:

       partner(partner(S)) == S

5. Removing a stone removes its entanglement edge.
6. After capture propagation completes, no captured stone remains on either board.
7. The side to move is correct.
8. The state hash matches the actual state.

Agents must add assertions/checkers where practical.

---

# 6. Entanglement Representation

Use an explicit, deterministic mapping.

A conceptual structure is:

```cpp
struct EntangledStone {
    BoardId board;
    Position position;
};

class EntanglementManager {
public:
    bool hasPartner(EntangledStone stone) const;
    EntangledStone partnerOf(EntangledStone stone) const;
    void link(EntangledStone a, EntangledStone b);
    void unlink(EntangledStone stone);
};
```

The exact API must fit repository conventions.

Do not encode entanglement only in visual/UI metadata.

It is part of the game state and therefore part of:

- transition logic,
- hashing,
- undo,
- L&D analysis,
- RZ propagation.

---

# 7. Move Representation

Use one move abstraction capable of representing both phases.

Conceptually:

```cpp
struct QuantumMove {
    Position b1;
    Position b2;
};
```

For opening moves:

```text
b1 != b2 is allowed because coordinates belong to different boards.
```

For common-phase moves:

```text
b1 == b2
```

The implementation may instead use a tagged union or separate move types if that integrates more cleanly with the repository.

The important semantic invariant is:

- moves 1–2 = independently selected B1/B2 coordinates;
- moves >= 3 = same coordinate on both boards.

---

# 8. Legal Move Generation

## Opening moves

For move 1 and move 2:

```text
legal = legalOnB1(p1) AND legalOnB2(p2)
```

with independently selected coordinates.

## Common phase

For a shared coordinate `p`:

```text
legalQuantum(p) = legal(B1, p) AND legal(B2, p)
```

The move is rejected if it is illegal on either board.

Do not generate a move from the union of B1 and B2 legal moves.

Do not allow a move to be silently applied to only one board.

---

# 9. QuantumGo Transition Protocol

Every move must use a deterministic transition sequence.

Conceptually:

```text
1. Validate the move on the joint QuantumGo state.
2. Apply the required stone placements.
3. Perform ordinary local Go capture checks on both boards.
4. For every captured entangled stone, enqueue its partner.
5. Remove queued partners.
6. Check newly created local captures.
7. Continue propagation until the queue is empty and no new capture exists.
8. Update ko/history information.
9. Update side to move.
10. Update the state hash.
```

The implementation should use an iterative queue/worklist for capture propagation rather than uncontrolled recursive calls.

---

# 10. Cross-Board Capture Propagation

This is one of the most important correctness components.

Example:

```text
B1[A] <-> B2[B]
```

If B1[A] is captured:

```text
capture B1[A]
    -> remove B2[B]
    -> inspect B2 for new local captures
    -> remove any newly captured entangled partners
    -> repeat
```

The system must support cascades in both directions.

The final state must be a stable fixed point of all local and entanglement-induced capture consequences.

---

# 11. Undo / Rollback Protocol

Every search transition must be exactly reversible.

The move record should be capable of restoring:

- all B1 changes,
- all B2 changes,
- all entanglement changes,
- all capture removals,
- ko/history state,
- side to move,
- incremental hashes,
- any RZS/search-visible state changed by the transition.

The agent must add an invariant test:

```text
S0
 -> play(M)
 -> undo(M)
 = S0
```

This must be checked across many generated and hand-crafted cases, including capture cascades.

---

# 12. QuantumGo Hashing

The transposition-table key must distinguish QuantumGo states that have:

- identical B1 positions,
- identical B2 positions,
- but different entanglement relationships.

The conceptual state key is:

```text
Hash =
    hash(B1)
  XOR hash(B2)
  XOR hash(entanglement structure)
  XOR hash(side-to-move)
  XOR hash(relevant ko/history)
```

The actual construction may use the repository's existing hashing system.

## Critical test

These must produce different keys:

```text
A:
B1[D4] <-> B2[C3]

B:
B1[D4] <-> B2[F4]
```

when all other state data are identical.

---

# 13. Quantum L&D Target Model

Do not assume that the target is one classical Go group.

A QuantumGo target may depend on:

- a group on B1,
- a group on B2,
- entangled stones,
- cross-board capture consequences.

Represent the target in a way compatible with exact L&D proof.

The target model must support at least:

```text
objective = LIVE or KILL
attacker
defender
target stones/groups
```

A target should not be evaluated independently on B1 and B2 unless the formal rules prove that independence is valid in that position.

---

# 14. Quantum L&D Terminal Logic

The terminal logic must answer an L&D question, not a scoring question.

Examples:

```text
KILL:
    attacker has forced target death

LIVE:
    defender has forced target survival
```

Do not use:

```text
score(B1) + score(B2)
```

as the primary terminal condition for an L&D tsumego.

If scoring is ever implemented, it must remain a separate full-game feature and must not replace the L&D objective.

---

# 15. Quantum Unconditional Life / Death

Before implementation, the agent must write down a formal rule for QuantumGo unconditional life and unconditional death.

The definition must account for:

- liberties,
- eyes,
- local capture,
- entanglement-triggered removal,
- cross-board tactical interactions.

Do not directly assume that ordinary Go UCA code remains sound without analysis.

The formal definition should be referenced by code comments and tests.

---

# 16. Quantum Relevance Zone

The Relevance Zone is central to this project.

Do not replace it with a whole-board search by default.

Conceptually:

```text
Quantum RZ =
    relevant positions on B1
    + relevant positions on B2
    + entanglement-linked relevant positions
```

The RZ should be **goal-directed** and sufficient for proving the current L&D result.

Do not automatically copy an RZ from B1 to B2.

Do not automatically include the whole of B1 or B2.

---

# 17. Cross-Board RZ Closure

RZ propagation must account for two connectivity types:

### Go locality

```text
adjacent positions / group liberties / captures
```

### Entanglement connectivity

```text
B1[A] <-> B2[B]
```

A relevant event on B1 can make B2 relevant through entanglement.

A relevant event on B2 can similarly make B1 relevant.

The implementation should compute an appropriate closure rather than using a single-board geometric radius.

---

# 18. Candidate Generation for RZS

Candidate generation must remain L&D-oriented.

A candidate can be relevant because it may:

- change target liberties,
- create/remove an eye,
- capture a target group,
- defend a target group,
- attack a relevant group,
- trigger a cross-board entangled capture,
- affect a relevant entangled partner,
- change the RZ proof boundary.

For moves >= 3, every candidate coordinate must pass:

```text
legal(B1, p) AND legal(B2, p)
```

Do not fall back to all-board exhaustive candidate generation unless explicitly requested as a diagnostic baseline.

---

# 19. Quantum Null / Irrelevant Moves

Preserve the RZS principle that moves that provably cannot affect the current L&D objective need not be explored as normal tactical branches.

However:

```text
far from target != automatically irrelevant
```

A move may be relevant through an entanglement chain.

The irrelevance test therefore needs to account for:

```text
local effect
+
entanglement effect
+
possible cross-board consequence
```

Never classify a move as irrelevant using only Euclidean/Manhattan distance or a single-board radius.

---

# 20. Search Integration

The QuantumGo state should be plugged into the existing search framework through the smallest possible interface change.

The conceptual search node is:

```text
QuantumGoState
    +
L&D objective
    +
Quantum RZ information
    +
search metadata
```

Reuse existing components where their semantics remain valid.

Examples of likely reusable infrastructure include:

- search tree logic,
- candidate ordering infrastructure,
- transposition-table infrastructure,
- result handling,
- solution-tree output,
- statistics collection.

Where existing components encode a single-board assumption that is semantically unsafe, create a QuantumGo-specific adapter or implementation instead of silently bending the original logic.

---

# 21. Do Not Rewrite the RZS Algorithm Blindly

Agents must not replace the RZS mechanism with generic MCTS merely because it is easier to connect to a new board representation.

If the original RZS method relies on:

- RZ construction,
- RZ expansion,
- candidate filtering,
- null moves,
- UCA/terminal proof conditions,

those principles must be retained.

The job is to generalize the relevant game-specific assumptions from:

```text
single-board Go
```

to:

```text
joint two-board QuantumGo
```

not to abandon RZS.

---

# 22. Solution Output

The solver must return more than a Boolean result when possible.

Recommended result data:

```text
Result:
    LIVE / DEAD
Winning side:
    BLACK / WHITE
Best move:
    ...
Principal variation:
    ...
Quantum capture events:
    ...
RZ summary:
    ...
Search statistics:
    ...
```

The solution tree should remain compatible with the research goals of the original L&D solver.

---

# 23. Required Diagnostics

During development, provide a debug representation of a QuantumGo state.

It should be possible to print:

```text
B1 board
B2 board
entanglement pairs
side to move
RZ(B1)
RZ(B2)
target
objective
hash
```

For capture debugging, log a cascade such as:

```text
B1[D4] captured
    -> partner B2[C3] removed
    -> B2[E3-E4] group captured
    -> partner B1[...] removed
```

The format can be temporary, but it must make cross-board propagation auditable.

---

# 24. Testing Protocol

All QuantumGo implementation work must use layered tests.

## Layer A — Rule tests

Test:

- move 1,
- move 2,
- shared move legality,
- occupancy,
- suicide,
- ko.

## Layer B — Capture tests

Test:

- local B1 capture,
- local B2 capture,
- B1 -> B2 propagation,
- B2 -> B1 propagation,
- multi-step cascades,
- multiple entangled pairs.

## Layer C — State tests

Test:

- clone/copy,
- hash,
- undo,
- exact state restoration.

## Layer D — L&D tests

Test:

- immediate life,
- immediate death,
- forced life,
- forced kill,
- cross-board tactical dependence.

At least one test must demonstrate that solving B1 and B2 independently gives the wrong L&D conclusion.

## Layer E — RZS tests

Test:

- initial RZ,
- cross-board RZ propagation,
- RZ expansion,
- relevant candidate generation,
- irrelevant/null move handling.

## Layer F — Regression tests

Run the existing normal-Go L&D tests and verify that their results do not change.

---

# 25. Required Validation From the Provided 5–10 Move Game

When the project owner provides the complete QuantumGo game:

1. Parse every move.
2. Reconstruct B1 and B2 after each move.
3. Verify the special rules for moves 1 and 2.
4. Verify common-phase synchronized moves.
5. Verify every local capture.
6. Verify every entanglement-triggered capture.
7. Record entanglement pairs after every move.
8. Use resulting positions to construct at least one L&D test case.

The game is primarily a **rule-validation and state-construction reference**.

It does not define the solver's L&D architecture by itself.

---

# 26. Performance Baseline

Do not optimize before correctness.

Once correctness is established, measure:

- nodes searched,
- candidate count,
- relevant candidate count,
- null/irrelevant move count,
- maximum search depth,
- RZ size on B1,
- RZ size on B2,
- number of RZ expansions,
- transposition-table hit rate,
- capture-propagation events,
- solving time.

Optimization targets may include:

- bitboards,
- incremental liberty tracking,
- incremental hashing,
- cached entanglement effects,
- candidate caching,
- RZ caching,
- search ordering,
- transposition tables.

No optimization may change the formal QuantumGo or L&D semantics.

---

# 27. Agent Workflow

Every coding agent should follow this workflow.

### Step 1 — Read

Read:

- this protocol,
- the capability specification,
- the development-phase document,
- the relevant files in `study-LD-RZ`.

### Step 2 — Identify

State exactly which existing code path the task affects.

### Step 3 — Design

State the intended change and the invariants it preserves.

### Step 4 — Implement

Make the smallest coherent change necessary.

### Step 5 — Test

Add or update tests immediately.

### Step 6 — Verify QuantumGo Semantics

Explicitly check:

- two boards,
- opening rules,
- synchronized common-phase legality,
- entangled capture,
- no collapse.

### Step 7 — Verify L&D Semantics

Explicitly check:

- target definition,
- attacker/defender objective,
- exact terminal conditions,
- RZ behavior.

### Step 8 — Regression Test

Ensure existing normal-Go solver behavior is preserved.

### Step 9 — Document

Record:

- changed files,
- new interfaces,
- tests,
- assumptions,
- known limitations.

---

# 28. Commit Protocol

When the project uses version control, prefer logically isolated commits.

Recommended progression:

```text
1. QuantumGo state abstraction
2. Entanglement representation
3. Quantum move legality
4. Quantum transition + capture propagation
5. Undo + hashing
6. Quantum L&D target/terminal logic
7. Quantum RZ
8. Candidate/null-move integration
9. Search integration
10. Solution output
11. Test suite
12. Performance optimization
```

Do not mix unrelated refactors into these commits unless necessary for compilation or correctness.

---

# 29. Acceptance Criteria

A phase is complete only when:

- the relevant tests pass,
- the formal QuantumGo rules are preserved,
- the exact L&D semantics are preserved,
- the RZS principle remains intact,
- normal-Go regression behavior is unaffected where applicable,
- the implementation is documented.

A feature is NOT complete merely because the code compiles.

---

# 30. Final System Acceptance Test

The project should eventually support this workflow:

```text
QuantumGo L&D input
        |
        v
 Joint B1/B2 state
        |
        v
 Entanglement-aware target
        |
        v
 Quantum Relevance Zone
        |
        v
 Relevant QuantumGo candidate generation
        |
        v
 Exact RZS search
        |
        v
 Cross-board capture propagation
        |
        v
 Quantum L&D terminal proof
        |
        v
 LIVE / DEAD
        |
        v
 Winning variation + RZ + statistics
```

The implementation has succeeded only when the above workflow works as an **L&D proof system**, not merely as a legal-move simulator.

---

# 31. Final Reminder to Coding Agents

Before implementing any feature, ask two questions:

### Question 1

**Does this obey the project's exact QuantumGo rules?**

### Question 2

**Does this help solve a life-and-death problem using relevance-zone-based exact search?**

If the answer to either question is no, do not implement the feature without first revisiting the architecture.

The target architecture is:

```text
                 QuantumGo L&D Solver
                          |
             +------------+------------+
             |                         |
        QuantumGo State             RZS
             |                         |
      +------+-------+          +------+------+
      |              |          |             |
     B1             B2      Quantum RZ   Exact Search
      |              |          |             |
      +------+-------+----------+-------------+
             |
       Entanglement
             |
             v
    Cross-board consequences
             |
             v
       L&D proof/result
```

**Do not turn this into a generic QuantumGo engine. Build the smallest correct QuantumGo machinery needed to support an exact, relevance-zone-based life-and-death solver.**
