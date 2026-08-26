#pragma once
// ============================================================================
// QuantumCapture.h  —  Iterative cross-board capture cascade
//
// Protocol §9–10, §0.2:
//   After any stone placement:
//   1. Perform local Go captures on both boards.
//   2. For every captured stone that has an entangled partner,
//      enqueue the partner for removal on the OTHER board.
//   3. Remove queued partners.
//   4. Perform local captures triggered by the removals.
//   5. Repeat until the worklist is empty (stable fixed point).
//
// This is deterministic and uses an iterative queue (not recursion).
//
// The result of applyMove() is stored in a QuantumUndoRecord so
// it can be exactly reversed by QuantumUndo::undo().
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include "QuantumMove.h"
#include "EntanglementTable.h"
#include <vector>

// ── Undo record ───────────────────────────────────────────────────────────────
// Stores everything needed to exactly reverse one QuantumMove.
struct QuantumUndoRecord {
    QuantumMove move;

    // Stones placed (pos, board, colour)
    struct StonePlaced { BoardId board; int pos; QColor color; };
    std::vector<StonePlaced> placed;

    // Stones removed during cascade (pos, board, colour, had_partner, partner_pos)
    struct StoneRemoved {
        BoardId board;
        int     pos;
        QColor  color;
        bool    hadPartner;
        int     partnerPos;   // pos on the OTHER board; valid if hadPartner
    };
    std::vector<StoneRemoved> removed;

    // Entanglement links created by this move (opening moves only)
    struct EntLink { int b1pos; int b2pos; };
    std::vector<EntLink> linksAdded;

    // Ko state before the move
    int   prevKo[2]  = {QGO_INVALID_POS, QGO_INVALID_POS};
    // Ko state after the move (set by applyMove)
    int   newKo[2]   = {QGO_INVALID_POS, QGO_INVALID_POS};

    // Side to move before the move
    QColor prevSide = QColor::BLACK;

    // Move number before the move
    int prevMoveNumber = 0;

    // Hash before the move
    ZKey prevHash = 0;

    // Full entanglement snapshot before the move (for exact undo)
    EntanglementTable::Snapshot entSnapshot;
};

// ── Cascade engine ────────────────────────────────────────────────────────────
class QuantumCapture {
public:
    // Apply move to state, filling rec with the undo record.
    // Returns true on success; false if the move is illegal (caller must check
    // with QuantumMoveGen::isLegal() first).
    static bool applyMove(QuantumBoardState& state,
                          const QuantumMove& move,
                          QuantumUndoRecord& rec);

    // Perform only the cascade (used after direct stone manipulation in tests).
    // Appends to rec.removed and updates entanglement.
    static void cascade(QuantumBoardState& state, QuantumUndoRecord& rec);

private:
    // Place stone on one board and run local captures; append to rec.
    static std::vector<int> placeAndCapture(QuantumBoardState& state,
                                            BoardId b, int pos, QColor c,
                                            QuantumUndoRecord& rec);

    // Remove stone from board b at pos (entangled or cascade-triggered).
    static void removeAndRecord(QuantumBoardState& state,
                                BoardId b, int pos,
                                QuantumUndoRecord& rec);
};
