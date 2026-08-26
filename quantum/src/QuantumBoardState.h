#pragma once
// ============================================================================
// QuantumBoardState.h  —  Joint B1 + B2 game state
//
// This is the central data structure.  It owns:
//   m_b1          — Board 1 (a self-contained single-board Go state)
//   m_b2          — Board 2 (a self-contained single-board Go state)
//   m_ent         — Entanglement table (B1 <-> B2 position links)
//   m_sideToMove  — Whose turn
//   m_moveNumber  — 1-indexed; moves 1–2 are opening phase
//   m_ko[2]       — Ko position per board (-1 = no ko)
//   m_hash        — Incremental Zobrist hash over the joint state
//
// B1 and B2 are NEVER treated as independent games (Protocol §0.1).
// Every operation that touches one board may also touch the other via
// the entanglement cascade defined in QuantumCapture.
// ============================================================================

#include "QuantumTypes.h"
#include "EntanglementTable.h"
#include "SingleBoard.h"
#include "QuantumHash.h"

class QuantumBoardState {
public:
    // ── Construction ─────────────────────────────────────────────────────────
    explicit QuantumBoardState(int boardSize = 9);
    void reset();

    // ── Accessors ────────────────────────────────────────────────────────────
    int          boardSize()    const { return boardSize_; }
    int          moveNumber()   const { return moveNumber_; }
    QColor       sideToMove()   const { return sideToMove_; }
    ZKey         hash()         const { return hash_; }
    MovePhase    phase()        const {
        return (moveNumber_ <= 2) ? MovePhase::OPENING : MovePhase::COMMON;
    }

    const SingleBoard& board(BoardId b) const {
        return (b == BoardId::B1) ? b1_ : b2_;
    }
    SingleBoard& board(BoardId b) {
        return (b == BoardId::B1) ? b1_ : b2_;
    }
    const EntanglementTable& ent() const { return ent_; }
    EntanglementTable&       ent()       { return ent_; }

    int ko(BoardId b) const { return ko_[static_cast<int>(b)]; }

    // ── Stone queries ─────────────────────────────────────────────────────────
    QColor colorAt(BoardId b, int pos) const { return board(b).colorAt(pos); }
    bool   isEmpty(BoardId b, int pos) const {
        return colorAt(b, pos) == QColor::EMPTY;
    }

    // ── Hash helpers (incremental) ────────────────────────────────────────────
    // Toggle a stone in the running hash (called internally by play/undo)
    void xorStone(BoardId b, int pos, QColor c) {
        hash_ ^= QuantumHash::stoneKey(b, pos, c);
    }
    void xorEntangle(int b1pos, int b2pos) {
        hash_ ^= QuantumHash::entangleKey(b1pos, b2pos);
    }
    void xorSide() {
        hash_ ^= QuantumHash::sideKey(sideToMove_);
    }
    void xorKo(BoardId b, int pos) {
        if (pos != QGO_INVALID_POS) hash_ ^= QuantumHash::koKey(b, pos);
    }

    // ── Invariant checker (debug) ────────────────────────────────────────────
    // Returns empty string on pass, error description on failure.
    std::string checkInvariants() const;

    // ── State copy ───────────────────────────────────────────────────────────
    QuantumBoardState clone() const;

    // ── Debug display ────────────────────────────────────────────────────────
    std::string toString() const;

    // ── Internal fields exposed to QuantumCapture / QuantumUndo ─────────────
    // (kept public for friend access in the move subsystem)
    int       boardSize_;
    SingleBoard b1_;
    SingleBoard b2_;
    EntanglementTable ent_;
    QColor    sideToMove_  = QColor::BLACK;
    int       moveNumber_  = 0;
    int       ko_[2]       = {QGO_INVALID_POS, QGO_INVALID_POS};
    ZKey      hash_        = 0;
};
