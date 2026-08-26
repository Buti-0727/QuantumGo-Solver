#pragma once
// ============================================================================
// QuantumMove.h  —  Move representation for both phases
//
// Opening phase (moves 1 and 2, Coding Protocol §0.1, §7):
//   b1pos and b2pos are INDEPENDENTLY selected coordinates.
//   b1pos may differ from b2pos (they belong to different boards).
//
// Common phase (move 3+):
//   b1pos == b2pos  (same coordinate on both boards).
//   Legal only if legal on BOTH B1 and B2.
//
// PASS: b1pos == b2pos == QGO_INVALID_POS.
// ============================================================================

#include "QuantumTypes.h"
#include <string>

struct QuantumMove {
    int       b1pos  = QGO_INVALID_POS;   // position on B1
    int       b2pos  = QGO_INVALID_POS;   // position on B2
    QColor    color  = QColor::EMPTY;
    MovePhase phase  = MovePhase::COMMON;

    // ── Factory helpers ───────────────────────────────────────────────────────
    static QuantumMove opening(QColor c, int p1, int p2) {
        QuantumMove m;
        m.color  = c;
        m.b1pos  = p1;
        m.b2pos  = p2;
        m.phase  = MovePhase::OPENING;
        return m;
    }

    static QuantumMove common(QColor c, int pos) {
        QuantumMove m;
        m.color  = c;
        m.b1pos  = pos;
        m.b2pos  = pos;   // same coordinate on both boards
        m.phase  = MovePhase::COMMON;
        return m;
    }

    static QuantumMove pass(QColor c) {
        QuantumMove m;
        m.color  = c;
        m.b1pos  = QGO_INVALID_POS;
        m.b2pos  = QGO_INVALID_POS;
        m.phase  = MovePhase::COMMON;
        return m;
    }

    bool isPass()    const { return b1pos == QGO_INVALID_POS && b2pos == QGO_INVALID_POS; }
    bool isOpening() const { return phase == MovePhase::OPENING; }
    bool isCommon()  const { return phase == MovePhase::COMMON; }

    // Invariant: common-phase moves must use the same coordinate
    bool isConsistent() const {
        if (isCommon() && !isPass()) return b1pos == b2pos;
        return true;
    }

    std::string toString(int boardSize = 9) const;
};
