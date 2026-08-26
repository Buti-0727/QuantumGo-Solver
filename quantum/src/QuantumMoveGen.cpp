// ============================================================================
// QuantumMoveGen.cpp
// ============================================================================
#include "QuantumMoveGen.h"
#include <string>

// ── Common-phase legality ─────────────────────────────────────────────────────
bool QuantumMoveGen::isLegalCommon(const QuantumBoardState& state, int pos) {
    // Protocol §8: legal on B1 AND legal on B2 — never union.
    QColor c = state.sideToMove();
    bool okB1 = state.board(BoardId::B1).isLegal(pos, c, state.ko(BoardId::B1));
    bool okB2 = state.board(BoardId::B2).isLegal(pos, c, state.ko(BoardId::B2));
    return okB1 && okB2;
}

// ── Opening-phase legality ────────────────────────────────────────────────────
bool QuantumMoveGen::isLegalOpening(const QuantumBoardState& state,
                                    int b1pos, int b2pos, QColor c) {
    if (b1pos < 0 || b2pos < 0) return false;
    bool okB1 = state.board(BoardId::B1).isLegal(b1pos, c, QGO_INVALID_POS);
    bool okB2 = state.board(BoardId::B2).isLegal(b2pos, c, QGO_INVALID_POS);
    return okB1 && okB2;
}

// ── Full legality dispatch ────────────────────────────────────────────────────
bool QuantumMoveGen::isLegal(const QuantumBoardState& state, const QuantumMove& move) {
    if (move.isPass()) return true;   // pass is always legal in common phase
    if (!move.isConsistent()) return false;
    if (move.color != state.sideToMove()) return false;

    if (move.isOpening()) {
        if (state.phase() != MovePhase::OPENING) return false;
        return isLegalOpening(state, move.b1pos, move.b2pos, move.color);
    }
    // Common phase
    if (state.phase() == MovePhase::OPENING) return false;
    return isLegalCommon(state, move.b1pos);
}

// ── Generate all legal common-phase moves ─────────────────────────────────────
std::vector<QuantumMove> QuantumMoveGen::generateCommon(const QuantumBoardState& state) {
    std::vector<QuantumMove> moves;
    QColor c   = state.sideToMove();
    int    n   = state.boardSize() * state.boardSize();
    for (int pos = 0; pos < n; ++pos) {
        if (isLegalCommon(state, pos)) {
            moves.push_back(QuantumMove::common(c, pos));
        }
    }
    return moves;
}

// ── Generate all legal opening moves ─────────────────────────────────────────
// (Expensive O(n²) — only used for testing / move 1–2 setup)
std::vector<QuantumMove> QuantumMoveGen::generateOpening(
        const QuantumBoardState& state, QColor c) {
    std::vector<QuantumMove> moves;
    int n = state.boardSize() * state.boardSize();
    for (int p1 = 0; p1 < n; ++p1) {
        if (!state.board(BoardId::B1).isLegal(p1, c, QGO_INVALID_POS)) continue;
        for (int p2 = 0; p2 < n; ++p2) {
            if (!state.board(BoardId::B2).isLegal(p2, c, QGO_INVALID_POS)) continue;
            moves.push_back(QuantumMove::opening(c, p1, p2));
        }
    }
    return moves;
}

// ── QuantumMove::toString ─────────────────────────────────────────────────────
std::string QuantumMove::toString(int bs) const {
    auto posStr = [&](int pos) -> std::string {
        if (pos == QGO_INVALID_POS) return "PASS";
        int x = pos % bs, y = pos / bs;
        char col = (char)('A' + x + (x >= 8 ? 1 : 0));
        return std::string(1, col) + std::to_string(y + 1);
    };
    std::string s = (color == QColor::BLACK ? "B" : "W");
    s += "[";
    if (isOpening()) {
        s += "B1:" + posStr(b1pos) + " B2:" + posStr(b2pos);
    } else {
        s += posStr(b1pos);
    }
    s += "]";
    return s;
}
