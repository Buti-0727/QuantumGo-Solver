// ============================================================================
// QuantumTarget.cpp
// ============================================================================
#include "QuantumTarget.h"

bool QuantumTarget::isImmediatelyDead(const QuantumBoardState& state) const {
    // Target is dead when ALL its stones have been removed from BOTH boards.
    for (int p : b1Stones)
        if (!state.board(BoardId::B1).isEmpty(p)) return false;
    for (int p : b2Stones)
        if (!state.board(BoardId::B2).isEmpty(p)) return false;
    return !b1Stones.empty() || !b2Stones.empty();
}

bool QuantumTarget::hasUnconditionalLife(const QuantumBoardState& state) const {
    // Conservative: each target group on each board must have >= 2 liberties
    // as a fast lower bound. Full Benson analysis is done in QuantumSearch.
    auto checkBoard = [&](const std::vector<int>& stones, BoardId bid) -> bool {
        const SingleBoard& board = state.board(bid);
        for (int p : stones) {
            if (board.isEmpty(p)) return false;  // stone gone
            if (board.liberties(p) < 2) return false;
        }
        return true;
    };
    if (!b1Stones.empty() && !checkBoard(b1Stones, BoardId::B1)) return false;
    if (!b2Stones.empty() && !checkBoard(b2Stones, BoardId::B2)) return false;
    return true;
}

void QuantumTarget::update(const QuantumBoardState& state) {
    auto filterAlive = [&](std::vector<int>& stones, BoardId bid) {
        stones.erase(
            std::remove_if(stones.begin(), stones.end(),
                [&](int p){ return state.board(bid).isEmpty(p); }),
            stones.end());
    };
    filterAlive(b1Stones, BoardId::B1);
    filterAlive(b2Stones, BoardId::B2);
}

int QuantumTarget::aliveCount(const QuantumBoardState& state) const {
    int count = 0;
    for (int p : b1Stones)
        if (!state.board(BoardId::B1).isEmpty(p)) count++;
    for (int p : b2Stones)
        if (!state.board(BoardId::B2).isEmpty(p)) count++;
    return count;
}
