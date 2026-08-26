#pragma once
// ============================================================================
// SingleBoard.h  —  Self-contained single-board Go state
//
// Tracks stones, groups (by flood-fill identity), liberties, and ko.
// Does NOT encode QuantumGo semantics — those live in QuantumBoardState.
//
// Group representation: union-find with path compression.
// Liberty tracking: counted per group; decremented/incremented on play/undo.
// ============================================================================

#include "QuantumTypes.h"
#include <vector>

class SingleBoard {
public:
    explicit SingleBoard(int bs = 9);
    void reset(int bs);
    void reset() { reset(boardSize_); }

    int boardSize() const { return boardSize_; }
    int numCells()  const { return boardSize_ * boardSize_; }

    // ── Stone access ──────────────────────────────────────────────────────────
    QColor colorAt(int pos) const { return color_[pos]; }
    bool   isEmpty(int pos) const { return color_[pos] == QColor::EMPTY; }
    bool   isOccupied(int pos) const { return color_[pos] == QColor::BLACK
                                             || color_[pos] == QColor::WHITE; }

    // ── Group (chain) access ──────────────────────────────────────────────────
    int  groupId(int pos) const;              // canonical root of union-find
    int  liberties(int pos) const;            // liberties of the group at pos
    bool hasLiberty(int pos) const { return liberties(pos) > 0; }

    // ── Move legality (single-board) ──────────────────────────────────────────
    // Returns true iff placing `c` at `pos` is legal (occupancy, suicide, ko).
    // ko_pos: the simple-ko forbidden point (-1 if none).
    bool isLegal(int pos, QColor c, int ko_pos = QGO_INVALID_POS) const;

    // ── Place stone (no capture, just occupy + rebuild adjacency) ─────────────
    // Used internally; callers should go through QuantumCapture.
    void placeStone(int pos, QColor c);

    // ── Remove stone (used by capture cascade) ────────────────────────────────
    void removeStone(int pos);

    // ── Capture all opponent stones with zero liberties adjacent to pos ───────
    // Returns bitset of captured positions (as vector).
    std::vector<int> performLocalCaptures(int pos, QColor placed_color);

    // ── Would this placement be suicide? ─────────────────────────────────────
    bool isSuicide(int pos, QColor c) const;

    // ── After placing c at pos, what would the resulting ko point be? ────────
    // Returns QGO_INVALID_POS if no simple ko arises.
    int computeKo(int pos, QColor c, const std::vector<int>& captured) const;

    // ── State copy / equality ─────────────────────────────────────────────────
    SingleBoard clone() const;
    bool operator==(const SingleBoard& o) const;

    // ── Debug ─────────────────────────────────────────────────────────────────
    std::string toString() const;

private:
    // ── Internal union-find ───────────────────────────────────────────────────
    int find(int pos) const;
    void unite(int a, int b);
    void rebuildGroup(int root);   // recount liberties after change

    // ── Full liberty recount for a group (flood-fill) ────────────────────────
    int countLiberties(int root) const;

    // ── Rebuild all groups from scratch ──────────────────────────────────────
    void rebuildAll();

    int boardSize_;
    std::vector<QColor> color_;    // [pos]
    mutable std::vector<int> parent_;  // union-find parent
    mutable std::vector<int> rank_;    // union-find rank
    std::vector<int>  libs_;       // liberty count per canonical root
    // libs_ is only valid for roots (pos == find(pos)); others are stale.
};
