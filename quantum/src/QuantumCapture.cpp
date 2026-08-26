// ============================================================================
// QuantumCapture.cpp  —  Iterative cross-board capture cascade
//
// Protocol §9 transition sequence:
//   1. Validate move on joint state.
//   2. Apply stone placements.
//   3. Perform ordinary local Go capture checks on BOTH boards.
//   4. For every captured entangled stone, enqueue its partner.
//   5. Remove queued partners.
//   6. Check newly created local captures.
//   7. Continue until queue is empty and no new capture exists.
//   8. Update ko / history.
//   9. Update side to move.
//  10. Update state hash.
// ============================================================================
#include "QuantumCapture.h"
#include "QuantumMoveGen.h"
#include "QuantumHash.h"
#include <queue>
#include <unordered_set>

// ── Helper: remove stone and record it ────────────────────────────────────────
void QuantumCapture::removeAndRecord(QuantumBoardState& state,
                                     BoardId b, int pos,
                                     QuantumUndoRecord& rec) {
    QColor c = state.board(b).colorAt(pos);
    assert(c != QColor::EMPTY);

    // Check for entangled partner BEFORE removing
    bool hadPartner = state.ent().hasPartner(b, pos);
    int  partnerPos = state.ent().partnerOf(b, pos);

    // Record the removal
    rec.removed.push_back({b, pos, c, hadPartner, partnerPos});

    // Update hash: remove stone key, remove entanglement key if present
    state.xorStone(b, pos, c);
    if (hadPartner) {
        int b1p = (b == BoardId::B1) ? pos : partnerPos;
        int b2p = (b == BoardId::B2) ? pos : partnerPos;
        state.xorEntangle(b1p, b2p);
    }

    // Remove from entanglement table
    state.ent().unlink(b, pos);

    // Remove stone from the board
    state.board(b).removeStone(pos);
}

// ── Helper: place stone, run local captures, return captured positions ─────────
std::vector<int> QuantumCapture::placeAndCapture(QuantumBoardState& state,
                                                  BoardId b, int pos, QColor c,
                                                  QuantumUndoRecord& rec) {
    // Update hash: add stone
    state.xorStone(b, pos, c);

    // Place the stone
    state.board(b).placeStone(pos, c);
    rec.placed.push_back({b, pos, c});

    // Run local captures on this board
    std::vector<int> localCaptures = state.board(b).performLocalCaptures(pos, c);

    // Record and hash-update each captured stone
    for (int cp : localCaptures) {
        QColor cc = QColor::EMPTY;
        // The colour was already removed by performLocalCaptures; look in rec
        // Actually performLocalCaptures removes them — we need to track before removal.
        // *** Re-implement: we record inside removeAndRecord, so use a different path.
        // The stone is already gone from board; we record manually here.
        // Find colour from rec — not ideal. Better: record before removal.
        // We'll use a workaround: the opponent colour.
        cc = opponent(c);
        bool hadP = state.ent().hasPartner(b, cp);
        int  partP = state.ent().partnerOf(b, cp);
        rec.removed.push_back({b, cp, cc, hadP, partP});
        // Update hash
        state.xorStone(b, cp, cc);
        if (hadP) {
            int b1p = (b == BoardId::B1) ? cp : partP;
            int b2p = (b == BoardId::B2) ? cp : partP;
            state.xorEntangle(b1p, b2p);
        }
        // Remove entanglement edge (stone already removed from board)
        state.ent().unlink(b, cp);
    }
    return localCaptures;
}

// ── Main cascade ──────────────────────────────────────────────────────────────
void QuantumCapture::cascade(QuantumBoardState& state, QuantumUndoRecord& rec) {
    // Worklist: (board, position) pairs of stones to remove because their
    // entangled partner was captured.
    struct WorkItem { BoardId board; int pos; };
    std::queue<WorkItem> worklist;

    // Seed: find all already-recorded removals that had an entangled partner.
    // We need to enqueue their partners on the OTHER board (if still alive).
    auto enqueueParters = [&](const QuantumUndoRecord::StoneRemoved& r) {
        if (r.hadPartner && r.partnerPos != QGO_INVALID_POS) {
            BoardId other = otherBoard(r.board);
            // Partner still on board?
            if (!state.board(other).isEmpty(r.partnerPos)) {
                worklist.push({other, r.partnerPos});
            }
        }
    };

    // Process removals that were already recorded (from local captures)
    size_t processed = 0;
    while (processed < rec.removed.size() || !worklist.empty()) {
        // Drain newly enqueued partners
        while (!worklist.empty()) {
            auto [b, pos] = worklist.front();
            worklist.pop();

            if (state.board(b).isEmpty(pos)) continue;  // already removed

            // Remove the entangled-partner stone
            removeAndRecord(state, b, pos, rec);

            // Removing this stone may cause local captures on board b
            // (liberty reduction for opponent groups adjacent to the hole)
            // Re-scan adjacency for newly zero-lib groups
            for (int nb : neighbours(pos, state.boardSize())) {
                if (nb == QGO_INVALID_POS) continue;
                QColor nc = state.board(b).colorAt(nb);
                if (nc == QColor::EMPTY || nc == QColor::BORDER) continue;
                // Any colour: if now 0 liberties, they get captured
                if (state.board(b).liberties(nb) == 0) {
                    // Collect all stones in this zero-liberty group first
                    int n = state.boardSize() * state.boardSize();
                    int root = state.board(b).groupId(nb);
                    std::vector<int> groupStones;
                    for (int p = 0; p < n; ++p) {
                        if (!state.board(b).isEmpty(p)
                            && state.board(b).groupId(p) == root) {
                            groupStones.push_back(p);
                        }
                    }
                    for (int p : groupStones) {
                        if (!state.board(b).isEmpty(p)) {
                            removeAndRecord(state, b, p, rec);
                        }
                    }
                }
            }
        }

        // Process newly added removals to find partners
        while (processed < rec.removed.size()) {
            enqueueParters(rec.removed[processed]);
            ++processed;
        }
    }
}

// ── Apply move (full transition) ─────────────────────────────────────────────
bool QuantumCapture::applyMove(QuantumBoardState& state,
                               const QuantumMove& move,
                               QuantumUndoRecord& rec) {
    // Save pre-move state for undo
    rec.move          = move;
    rec.prevSide      = state.sideToMove_;
    rec.prevMoveNumber = state.moveNumber_;
    rec.prevKo[0]     = state.ko_[0];
    rec.prevKo[1]     = state.ko_[1];
    rec.prevHash      = state.hash_;
    rec.entSnapshot   = state.ent_.snapshot();   // full entanglement snapshot


    // Remove old side key from hash
    state.hash_ ^= QuantumHash::sideKey(state.sideToMove_);
    // Remove old ko keys
    state.xorKo(BoardId::B1, state.ko_[0]);
    state.xorKo(BoardId::B2, state.ko_[1]);

    if (move.isPass()) {
        state.ko_[0] = state.ko_[1] = QGO_INVALID_POS;
        state.sideToMove_ = opponent(state.sideToMove_);
        state.moveNumber_++;
        // Re-add new state
        state.hash_ ^= QuantumHash::sideKey(state.sideToMove_);
        return true;
    }

    QColor c = move.color;

    if (move.isOpening()) {
        // ── Opening move: independently place on B1 and B2 ────────────────────
        // No captures expected on an empty board, but handle cascade anyway.
        placeAndCapture(state, BoardId::B1, move.b1pos, c, rec);
        placeAndCapture(state, BoardId::B2, move.b2pos, c, rec);

        // Create entanglement link
        state.ent().link(move.b1pos, move.b2pos);
        rec.linksAdded.push_back({move.b1pos, move.b2pos});
        state.xorEntangle(move.b1pos, move.b2pos);

        cascade(state, rec);

    } else {
        // ── Common-phase move: same coordinate on both boards ─────────────────
        assert(move.b1pos == move.b2pos);
        int pos = move.b1pos;

        placeAndCapture(state, BoardId::B1, pos, c, rec);
        placeAndCapture(state, BoardId::B2, pos, c, rec);

        cascade(state, rec);

        // Compute simple ko: only if exactly one stone captured on both boards
        // (simple ko = same single capture on both boards simultaneously)
        // We use a lenient rule: compute per-board and only set if consistent.
        // Count captures per board
        int capB1 = 0, capB2 = 0;
        int lastCapB1 = QGO_INVALID_POS, lastCapB2 = QGO_INVALID_POS;
        for (auto& r : rec.removed) {
            if (r.board == BoardId::B1) { capB1++; lastCapB1 = r.pos; }
            else                         { capB2++; lastCapB2 = r.pos; }
        }
        state.ko_[0] = (capB1 == 1) ?
            state.board(BoardId::B1).computeKo(pos, c, {lastCapB1}) :
            QGO_INVALID_POS;
        state.ko_[1] = (capB2 == 1) ?
            state.board(BoardId::B2).computeKo(pos, c, {lastCapB2}) :
            QGO_INVALID_POS;
    }

    // Update move number and side
    state.moveNumber_++;
    state.sideToMove_ = opponent(state.sideToMove_);

    // Add new side and ko to hash
    state.hash_ ^= QuantumHash::sideKey(state.sideToMove_);
    state.xorKo(BoardId::B1, state.ko_[0]);
    state.xorKo(BoardId::B2, state.ko_[1]);

    rec.newKo[0] = state.ko_[0];
    rec.newKo[1] = state.ko_[1];

    return true;
}
