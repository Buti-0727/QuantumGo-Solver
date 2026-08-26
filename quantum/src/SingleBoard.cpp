// ============================================================================
// SingleBoard.cpp  —  Single-board Go engine
// ============================================================================
#include "SingleBoard.h"
#include <sstream>
#include <stdexcept>
#include <queue>
#include <unordered_set>

SingleBoard::SingleBoard(int bs) : boardSize_(bs) {
    reset(bs);
}

void SingleBoard::reset(int bs) {
    boardSize_ = bs;
    int n = bs * bs;
    color_.assign(n, QColor::EMPTY);
    parent_.assign(n, QGO_INVALID_POS);
    rank_.assign(n, 0);
    libs_.assign(n, 0);
}

// ── Union-Find ────────────────────────────────────────────────────────────────
int SingleBoard::find(int pos) const {
    if (parent_[pos] == QGO_INVALID_POS) return pos;
    // Path compression
    while (parent_[pos] != QGO_INVALID_POS && parent_[pos] != pos)
        pos = parent_[pos];
    return pos;
}

void SingleBoard::unite(int a, int b) {
    int ra = find(a), rb = find(b);
    if (ra == rb) return;
    // Union by rank
    if (rank_[ra] < rank_[rb]) std::swap(ra, rb);
    parent_[rb] = ra;
    if (rank_[ra] == rank_[rb]) rank_[ra]++;
}

// ── Liberty counting (flood-fill) ──────────────────────────────────────────────
int SingleBoard::countLiberties(int root) const {
    // Collect all stones in the group, then count unique empty neighbours
    std::vector<bool> visited(boardSize_ * boardSize_, false);
    std::queue<int> q;
    q.push(root);
    visited[root] = true;

    std::unordered_set<int> libertySet;

    while (!q.empty()) {
        int cur = q.front(); q.pop();
        for (int nb : neighbours(cur, boardSize_)) {
            if (nb == QGO_INVALID_POS) continue;
            if (color_[nb] == QColor::EMPTY) {
                libertySet.insert(nb);
            } else if (color_[nb] == color_[root] && !visited[nb]
                       && find(nb) == root) {
                visited[nb] = true;
                q.push(nb);
            }
        }
    }
    return static_cast<int>(libertySet.size());
}

void SingleBoard::rebuildAll() {
    int n = boardSize_ * boardSize_;
    // Reset union-find
    for (int i = 0; i < n; ++i) {
        parent_[i] = QGO_INVALID_POS;
        rank_[i]   = 0;
        libs_[i]   = 0;
    }
    // Build groups
    for (int pos = 0; pos < n; ++pos) {
        if (!isOccupied(pos)) continue;
        for (int nb : neighbours(pos, boardSize_)) {
            if (nb == QGO_INVALID_POS) continue;
            if (color_[nb] == color_[pos]) unite(pos, nb);
        }
    }
    // Count liberties per root
    std::vector<bool> computed(n, false);
    for (int pos = 0; pos < n; ++pos) {
        if (!isOccupied(pos)) continue;
        int root = find(pos);
        if (!computed[root]) {
            libs_[root] = countLiberties(root);
            computed[root] = true;
        }
    }
}

// ── Group / liberty access ────────────────────────────────────────────────────
int SingleBoard::groupId(int pos) const { return find(pos); }

int SingleBoard::liberties(int pos) const {
    if (!isOccupied(pos)) return 0;
    return libs_[find(pos)];
}

// ── Legality ─────────────────────────────────────────────────────────────────
bool SingleBoard::isSuicide(int pos, QColor c) const {
    // A placement is suicide if after placing c at pos (removing any opponent
    // captures first), the placed stone's group has zero liberties.
    // We test conservatively: if any adjacent cell is empty → has liberty.
    // If any adjacent same-color group has > 1 lib → has liberty.
    // If any adjacent opposite-color group has 1 lib (capture) → has liberty.
    for (int nb : neighbours(pos, boardSize_)) {
        if (nb == QGO_INVALID_POS) continue;
        if (color_[nb] == QColor::EMPTY) return false;        // empty neighbour
        if (color_[nb] == c && libs_[find(nb)] > 1) return false; // friendly alive
        if (color_[nb] == opponent(c) && libs_[find(nb)] == 1) return false; // capture
    }
    return true;
}

bool SingleBoard::isLegal(int pos, QColor c, int ko_pos) const {
    if (pos < 0 || pos >= boardSize_ * boardSize_) return false;
    if (!isEmpty(pos)) return false;
    if (pos == ko_pos) return false;
    if (isSuicide(pos, c)) return false;
    return true;
}

// ── Placement ─────────────────────────────────────────────────────────────────
void SingleBoard::placeStone(int pos, QColor c) {
    assert(isEmpty(pos));
    color_[pos] = c;
    parent_[pos] = QGO_INVALID_POS;  // own root initially
    rank_[pos]   = 0;
    // Join with friendly neighbors
    for (int nb : neighbours(pos, boardSize_)) {
        if (nb == QGO_INVALID_POS) continue;
        if (color_[nb] == c) unite(pos, nb);
    }
    // Recount liberties for affected groups
    rebuildAll();   // simple correctness-first approach; optimise later
}

// ── Stone removal ─────────────────────────────────────────────────────────────
void SingleBoard::removeStone(int pos) {
    assert(isOccupied(pos));
    color_[pos] = QColor::EMPTY;
    rebuildAll();
}

// ── Local captures ───────────────────────────────────────────────────────────
std::vector<int> SingleBoard::performLocalCaptures(int pos, QColor placed_color) {
    std::vector<int> captured;
    QColor opp = opponent(placed_color);
    std::vector<bool> visited(boardSize_ * boardSize_, false);

    // Check each adjacent opponent group
    for (int nb : neighbours(pos, boardSize_)) {
        if (nb == QGO_INVALID_POS) continue;
        if (color_[nb] != opp) continue;
        int root = find(nb);
        if (visited[root]) continue;
        visited[root] = true;
        if (libs_[root] == 0) {
            // Capture entire group
            int n = boardSize_ * boardSize_;
            for (int p = 0; p < n; ++p) {
                if (isOccupied(p) && color_[p] == opp && find(p) == root) {
                    captured.push_back(p);
                }
            }
        }
    }
    // Remove captured stones
    for (int p : captured) removeStone(p);
    return captured;
}

// ── Ko detection ─────────────────────────────────────────────────────────────
int SingleBoard::computeKo(int pos, QColor /*c*/,
                            const std::vector<int>& captured) const {
    // Simple ko: exactly one stone captured, and placed stone has exactly 1 liberty
    if (captured.size() == 1) {
        int root = find(pos);
        if (libs_[root] == 1) {
            // The ko point is the captured position
            return captured[0];
        }
    }
    return QGO_INVALID_POS;
}

// ── Clone ─────────────────────────────────────────────────────────────────────
SingleBoard SingleBoard::clone() const {
    SingleBoard copy(boardSize_);
    copy.color_  = color_;
    copy.parent_ = parent_;
    copy.rank_   = rank_;
    copy.libs_   = libs_;
    return copy;
}

bool SingleBoard::operator==(const SingleBoard& o) const {
    if (boardSize_ != o.boardSize_) return false;
    return color_ == o.color_;
}

// ── Debug display ─────────────────────────────────────────────────────────────
std::string SingleBoard::toString() const {
    std::ostringstream oss;
    int bs = boardSize_;
    // Print from top row down
    for (int y = bs - 1; y >= 0; --y) {
        oss << (y + 1 < 10 ? " " : "") << (y + 1) << " ";
        for (int x = 0; x < bs; ++x) {
            int pos = y * bs + x;
            oss << toChar(color_[pos]);
            if (x < bs - 1) oss << ' ';
        }
        oss << "\n";
    }
    oss << "   ";
    for (int x = 0; x < bs; ++x) {
        char c = (char)('A' + x + (x >= 8 ? 1 : 0)); // skip 'I'
        oss << c;
        if (x < bs - 1) oss << ' ';
    }
    oss << "\n";
    return oss.str();
}
