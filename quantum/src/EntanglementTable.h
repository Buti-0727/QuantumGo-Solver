#pragma once
// ============================================================================
// EntanglementTable.h  —  Cross-board entanglement map
//
// An entangled pair is a (B1_pos, B2_pos) link created by one opening move.
// Invariants (Coding Protocol §6):
//   1.  partner(partner(S)) == S   (symmetric)
//   2.  Removing a stone removes its entanglement edge.
//   3.  No stone has more than one entangled partner.
//   4.  After any capture cascade the table contains only live stones.
// ============================================================================

#include "QuantumTypes.h"

class EntanglementTable {
public:
    // partner_[0][pos] = partner position on B2 for a B1 stone, or INVALID
    // partner_[1][pos] = partner position on B1 for a B2 stone, or INVALID
    static constexpr int INVALID = QGO_INVALID_POS;

    explicit EntanglementTable(int boardSize = 9);

    void reset();

    // Create a mutual link: B1[b1pos] <-> B2[b2pos]
    // Asserts that neither position is already entangled.
    void link(int b1pos, int b2pos);

    // Remove all entanglement edges touching b_pos on board b.
    void unlink(BoardId b, int pos);

    // Query
    bool hasPartner(BoardId b, int pos) const;
    int  partnerOf(BoardId b, int pos) const;   // returns INVALID if none

    // Iterate all active pairs: fn(b1pos, b2pos)
    template<typename Fn>
    void forEach(Fn fn) const {
        for (int p = 0; p < boardSize_ * boardSize_; ++p) {
            int q = partner_[0][p];   // b1->b2
            if (q != INVALID) fn(p, q);
        }
    }

    // For undo: snapshot and restore the whole table (cheap: just two arrays)
    struct Snapshot {
        int p0[QGO_MAX_GRIDS];
        int p1[QGO_MAX_GRIDS];
    };
    Snapshot snapshot() const;
    void     restore(const Snapshot& s);

    // Zobrist contribution — must be XOR-ed into the global hash
    ZKey zobristHash() const;

    // Debug
    std::string toString() const;

    int boardSize() const { return boardSize_; }

private:
    int boardSize_;
    int partner_[2][QGO_MAX_GRIDS];   // [board_id][pos]
};
