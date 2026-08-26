#pragma once
// ============================================================================
// QuantumMoveGen.h  —  Legal move generation for QuantumGo
//
// Common-phase rule (Coding Protocol §8, §18):
//   legalQuantum(p) = legal(B1, p) AND legal(B2, p)
//   NOT the union; a move illegal on either board is ILLEGAL.
//
// Opening-phase rule:
//   For move 1 (Black): any (p1, p2) with p1 legal on B1 AND p2 legal on B2,
//                        p1 and p2 may be the same or different coordinates.
//   For move 2 (White): same rule.
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include "QuantumMove.h"
#include <vector>

class QuantumMoveGen {
public:
    // ── Legality tests ────────────────────────────────────────────────────────

    // Full legality check for a proposed move on the given state.
    static bool isLegal(const QuantumBoardState& state, const QuantumMove& move);

    // Common-phase legality for a single coordinate (AND of both boards).
    static bool isLegalCommon(const QuantumBoardState& state, int pos);

    // Opening-phase legality for independently chosen (p1, p2).
    static bool isLegalOpening(const QuantumBoardState& state,
                                int b1pos, int b2pos, QColor c);

    // ── Move generation ───────────────────────────────────────────────────────

    // Generate all legal common-phase moves (positions legal on BOTH boards).
    // Excludes PASS; caller may append PASS if needed.
    static std::vector<QuantumMove> generateCommon(const QuantumBoardState& state);

    // Generate opening moves for the given colour (used in full-game play,
    // not typically needed in L&D solving which starts post-opening).
    static std::vector<QuantumMove> generateOpening(const QuantumBoardState& state,
                                                    QColor c);
};
