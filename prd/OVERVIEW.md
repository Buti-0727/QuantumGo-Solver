# QuantumGo Life-and-Death Solver — Overview

## 1. Introduction
The **QuantumGo Life-and-Death (L&D) Solver** is a specialized engine designed to compute exact L&D outcomes for the variant game "QuantumGo". Unlike traditional Go, QuantumGo is played on two simultaneous boards (B1 and B2), where stones on different boards can be "entangled". 

The core objective is to determine if a target group (which could span both boards) can be forced to live or die, by adapting the **Relevance-Zone Search (RZS)** algorithm originally developed for single-board Go L&D problems.

## 2. Core Business Logic & Rules of QuantumGo

### 2.1 The Two-Board State & Entanglement
- **Game State**: A valid QuantumGo state consists of the combined positions on Board 1 (B1) and Board 2 (B2), the side to move, game history (like ko), and the explicit entanglement relationships between stones.
- **Entanglement**: Stones on B1 can be entangled with stones on B2. If a stone is captured on one board, its entangled partner on the other board is instantly removed.
- **Capture Cascades**: Removing an entangled stone might cause another group to lose its last liberty, leading to a new capture. This cross-board capture propagation continues recursively until the board reaches a stable state.

### 2.2 Move Generation and Execution
- **Opening Moves**: The first two moves allow Black and then White to play one stone independently on each board.
- **Common Phase (Synchronized Moves)**: From move 3 onward, a player selects a single coordinate. The move is played on both B1 and B2 simultaneously. The move is only legal if it is legal on *both* boards.
- **Execution**: The solver places the stones, evaluates local captures, propagates entanglement captures, and verifies standard Go rules (suicide, ko, occupancy) across the joint state.

## 3. L&D Solving & Relevance-Zone Search (RZS)

### 3.1 Quantum Relevance Zone (RZ_Q)
To efficiently search for a solution without exploring the entire board, the solver uses a Quantum Relevance Zone. This zone identifies which intersections are tactically relevant to the L&D target. 
In QuantumGo, RZ_Q includes:
- Relevant positions on B1.
- Relevant positions on B2.
- Positions connected via entanglement.

The solver must dynamically expand this zone as new tactical dependencies are discovered during the search, propagating relevance across the two boards through entanglement links.

### 3.2 Move Filtering & Null Moves
- The solver generates candidate moves within the RZ_Q. 
- Moves outside the relevance zone that cannot affect the L&D target (even via entanglement) are treated as null/irrelevant moves. This prunes the search tree significantly.

### 3.3 Exact Solving & Terminal States
- The solver aims to prove an exact L&D outcome: either the attacker can force a kill, or the defender can force life.
- It returns the final result, the winning side, the best move, and a solution tree (principal variation) proving the outcome.

## 4. Architecture Summary
The solver is built by extending an existing single-board RZS solver (`study-LD-RZ-solver`). Rather than rewriting the search algorithm, the project adapts the game-specific layer:
- **Search Framework**: Retains the RZS search logic, tree generation, and candidate filtering.
- **QuantumGo Adapter**: Replaces the single-board representation with a joint two-board state, managing synchronized moves and cross-board capture resolution.
- **Entanglement Layer**: Tracks entanglement links and propagates captures and relevance across the boards.

*This document focuses purely on the product specifications and business logic of the QuantumGo L&D Solver. It serves as the foundation for the subsequent PRD documents.*
