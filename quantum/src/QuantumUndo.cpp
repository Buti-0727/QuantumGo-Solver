// ============================================================================
// QuantumUndo.cpp  —  Exact state rollback using entanglement snapshot
// ============================================================================
#include "QuantumUndo.h"

void QuantumUndo::undo(QuantumBoardState& state, const QuantumUndoRecord& rec) {
    // ── 1. Restore hash wholesale from snapshot ───────────────────────────────
    state.hash_ = rec.prevHash;

    // ── 2. Restore ko and side ────────────────────────────────────────────────
    state.ko_[0]      = rec.prevKo[0];
    state.ko_[1]      = rec.prevKo[1];
    state.sideToMove_ = rec.prevSide;
    state.moveNumber_ = rec.prevMoveNumber;

    // ── 3. Undo stone removals: restore removed stones in REVERSE order ───────
    // We restore in reverse so that union-find rebuilds correctly.
    for (int i = (int)rec.removed.size() - 1; i >= 0; --i) {
        const auto& r = rec.removed[i];
        state.board(r.board).placeStone(r.pos, r.color);
    }

    // ── 4. Undo stone placements: remove placed stones in REVERSE order ───────
    for (int i = (int)rec.placed.size() - 1; i >= 0; --i) {
        const auto& p = rec.placed[i];
        state.board(p.board).removeStone(p.pos);
    }

    // ── 5. Restore entanglement table from full snapshot ──────────────────────
    // This is O(N) but exactly correct regardless of cascade complexity.
    state.ent_.restore(rec.entSnapshot);

    // Protocol invariant: state after undo == state before play.
    // The caller may assert checkInvariants() in debug mode.
}
