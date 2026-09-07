// ============================================================================
// QuantumTarget.cpp
// ============================================================================
#include "QuantumTarget.h"

static int countTrueEyes(const SingleBoard& board, const std::vector<int>& targetStones, QColor defenderColor) {
    int eyes = 0;
    int bs = board.boardSize();
    int n = bs * bs;
    for (int p = 0; p < n; ++p) {
        if (!board.isEmpty(p)) continue;
        bool allDefender = true;
        int targetAdjacentCount = 0;
        int validNeighbours = 0;
        for (int nb : neighbours(p, bs)) {
            if (nb == QGO_INVALID_POS) continue;
            validNeighbours++;
            if (board.colorAt(nb) != defenderColor) {
                allDefender = false;
                break;
            }
            for (int tp : targetStones) {
                if (nb == tp) targetAdjacentCount++;
            }
        }
        if (validNeighbours > 0 && allDefender && targetAdjacentCount > 0) {
            eyes++;
        }
    }
    return eyes;
}

bool QuantumTarget::isImmediatelyDead(const QuantumBoardState& state) const {
    // Target is dead when ALL its target stones have been removed from BOTH boards.
    if (b1Stones.empty() && b2Stones.empty()) return false;
    for (int p : b1Stones) {
        if (state.board(BoardId::B1).colorAt(p) == defenderColor) return false;
    }
    for (int p : b2Stones) {
        if (state.board(BoardId::B2).colorAt(p) == defenderColor) return false;
    }
    return true;
}

bool QuantumTarget::hasUnconditionalLife(const QuantumBoardState& state) const {
    // A target group has unconditional life if it has at least 2 independent true eyes
    // on both boards.
    if (b1Stones.empty() && b2Stones.empty()) return false;
    int eyes1 = b1Stones.empty() ? 2 : countTrueEyes(state.board(BoardId::B1), b1Stones, defenderColor);
    int eyes2 = b2Stones.empty() ? 2 : countTrueEyes(state.board(BoardId::B2), b2Stones, defenderColor);
    return eyes1 >= 2 && eyes2 >= 2;
}

void QuantumTarget::update(const QuantumBoardState& /*state*/) {
    // Retain initial target reference coordinates across search
}

int QuantumTarget::aliveCount(const QuantumBoardState& state) const {
    int count = 0;
    for (int p : b1Stones)
        if (state.board(BoardId::B1).colorAt(p) == defenderColor) count++;
    for (int p : b2Stones)
        if (state.board(BoardId::B2).colorAt(p) == defenderColor) count++;
    return count;
}
