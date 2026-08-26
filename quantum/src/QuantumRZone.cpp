// ============================================================================
// QuantumRZone.cpp
// ============================================================================
#include "QuantumRZone.h"
#include <queue>
#include <sstream>

// ── Internal: add position to the RZ of board b, then propagate ───────────────
void QuantumRZone::addAndPropagate(const QuantumBoardState& state,
                                   BoardId b, int pos) {
    auto& rz = (b == BoardId::B1) ? rz_b1_ : rz_b2_;
    if (rz.count(pos)) return;  // already in RZ
    rz.insert(pos);

    // Propagate through entanglement: if this position has an entangled partner
    // on the other board, add it to the other board's RZ.
    if (state.ent().hasPartner(b, pos)) {
        int partner = state.ent().partnerOf(b, pos);
        BoardId other = otherBoard(b);
        addAndPropagate(state, other, partner);
    }
}

// ── Add all liberties of the group containing pos ─────────────────────────────
void QuantumRZone::addGroupLiberties(const QuantumBoardState& state,
                                     BoardId b, int pos) {
    const SingleBoard& board = state.board(b);
    int bs = state.boardSize();
    int root = board.groupId(pos);

    // Flood-fill group, collecting empty neighbours (liberties)
    std::vector<bool> visited(bs * bs, false);
    std::queue<int> q;
    q.push(pos);
    visited[pos] = true;

    while (!q.empty()) {
        int cur = q.front(); q.pop();
        for (int nb : neighbours(cur, bs)) {
            if (nb == QGO_INVALID_POS) continue;
            if (board.isEmpty(nb)) {
                addAndPropagate(state, b, nb);
            } else if (!visited[nb] && board.groupId(nb) == root) {
                visited[nb] = true;
                q.push(nb);
            }
        }
    }
}

// ── Build initial RZ ──────────────────────────────────────────────────────────
void QuantumRZone::build(const QuantumBoardState& state,
                         const QuantumTarget& target) {
    rz_b1_.clear();
    rz_b2_.clear();

    // Seed: target stones and their liberties on each board
    for (int p : target.b1Stones) {
        if (state.board(BoardId::B1).isOccupied(p)) {
            addAndPropagate(state, BoardId::B1, p);
            addGroupLiberties(state, BoardId::B1, p);
        }
    }
    for (int p : target.b2Stones) {
        if (state.board(BoardId::B2).isOccupied(p)) {
            addAndPropagate(state, BoardId::B2, p);
            addGroupLiberties(state, BoardId::B2, p);
        }
    }

    // Also add opponent stones adjacent to target (they threaten capture)
    int bs = state.boardSize();
    QColor att = target.attackerColor;
    for (int p : target.b1Stones) {
        for (int nb : neighbours(p, bs)) {
            if (nb == QGO_INVALID_POS) continue;
            if (state.board(BoardId::B1).colorAt(nb) == att)
                addAndPropagate(state, BoardId::B1, nb);
        }
    }
    for (int p : target.b2Stones) {
        for (int nb : neighbours(p, bs)) {
            if (nb == QGO_INVALID_POS) continue;
            if (state.board(BoardId::B2).colorAt(nb) == att)
                addAndPropagate(state, BoardId::B2, nb);
        }
    }
}

// ── Dynamic expansion ─────────────────────────────────────────────────────────
void QuantumRZone::expand(const QuantumBoardState& state, BoardId b, int pos) {
    addAndPropagate(state, b, pos);
    addGroupLiberties(state, b, pos);
}

// ── Candidate test ────────────────────────────────────────────────────────────
bool QuantumRZone::isCandidatePosition(const QuantumBoardState& state,
                                       int pos) const {
    int bs = state.boardSize();
    // In RZ on either board
    if (rz_b1_.count(pos) || rz_b2_.count(pos)) return true;
    // Adjacent to RZ on either board (one-step expansion boundary)
    for (int nb : neighbours(pos, bs)) {
        if (nb == QGO_INVALID_POS) continue;
        if (rz_b1_.count(nb) || rz_b2_.count(nb)) return true;
    }
    // Has entangled partner in RZ
    if (state.ent().hasPartner(BoardId::B1, pos)) {
        int q = state.ent().partnerOf(BoardId::B1, pos);
        if (rz_b2_.count(q)) return true;
    }
    if (state.ent().hasPartner(BoardId::B2, pos)) {
        int q = state.ent().partnerOf(BoardId::B2, pos);
        if (rz_b1_.count(q)) return true;
    }
    return false;
}

// ── Irrelevance test ─────────────────────────────────────────────────────────
// A move is irrelevant ONLY IF it cannot affect any position in RZ_Q
// through either local Go adjacency OR entanglement.
// Never use only distance. (Protocol §19)
bool QuantumRZone::isIrrelevant(const QuantumBoardState& state, int pos) const {
    return !isCandidatePosition(state, pos);
}

// ── Debug ─────────────────────────────────────────────────────────────────────
std::string QuantumRZone::toString(const QuantumBoardState& state) const {
    std::ostringstream oss;
    int bs = state.boardSize();
    oss << "RZ_B1 (" << rz_b1_.size() << "): ";
    for (int p : rz_b1_) {
        int x = p % bs, y = p / bs;
        oss << (char)('A' + x) << (y + 1) << " ";
    }
    oss << "\nRZ_B2 (" << rz_b2_.size() << "): ";
    for (int p : rz_b2_) {
        int x = p % bs, y = p / bs;
        oss << (char)('A' + x) << (y + 1) << " ";
    }
    oss << "\n";
    return oss.str();
}
