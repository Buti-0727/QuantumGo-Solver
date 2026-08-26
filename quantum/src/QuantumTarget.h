#pragma once
// ============================================================================
// QuantumTarget.h  —  L&D target model for QuantumGo
//
// A QuantumGo L&D target is NOT a single Go group on one board.
// It may involve groups on B1, groups on B2, and entangled stones
// (Protocol §13, Development Phases §1).
//
// Formal definition of Quantum Unconditional Life (Protocol §15):
//   A target T is quantum-unconditionally alive if and only if:
//     - On EVERY board (B1 and B2), every group of T has >= 2 genuine eyes OR
//       is Benson-safe; AND
//     - No entangled partner of any T-stone has been captured (which would
//       remove the T-stone from the other board); AND
//     - No sequence of moves by the attacker can simultaneously reduce both
//       B1 and B2 copies of the target to zero liberties.
//
// Formal definition of Quantum Unconditional Death:
//   A target T is quantum-unconditionally dead if and only if:
//     - There exists an attacker strategy such that under all defender replies,
//       the target's groups on BOTH B1 and B2 are eventually captured; OR
//     - An entanglement cascade triggered by attacker play causes
//       the target to lose all liberties on either board.
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include <vector>

struct QuantumTarget {
    // Stones belonging to the target (positions on B1 and B2)
    // NOTE: a target stone at B1[p] and its entangled partner B2[q]
    // are both part of the target if they belong to the defender's group.
    std::vector<int> b1Stones;   // positions on B1
    std::vector<int> b2Stones;   // positions on B2

    QColor  defenderColor = QColor::BLACK;  // colour of the target group
    QColor  attackerColor = QColor::WHITE;

    LDObjective objective = LDObjective::KILL;  // attacker's goal

    // ── Terminal condition tests ───────────────────────────────────────────────

    // Is the target immediately dead on both boards right now?
    // (All target stones removed from B1 AND B2)
    bool isImmediatelyDead(const QuantumBoardState& state) const;

    // Does the target have unconditional life right now?
    // Conservative fast test: checks >= 2 liberties per group and eye count.
    bool hasUnconditionalLife(const QuantumBoardState& state) const;

    // Update the target stone lists after a move (remove captured stones).
    void update(const QuantumBoardState& state);

    // Number of target stones still alive across both boards
    int aliveCount(const QuantumBoardState& state) const;
};
