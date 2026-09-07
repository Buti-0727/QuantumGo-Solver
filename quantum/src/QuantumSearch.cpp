// ============================================================================
// QuantumSearch.cpp  —  Exact AND/OR RZS search
// ============================================================================
#include "QuantumSearch.h"
#include <iostream>
#include <algorithm>

// ── Terminal test ─────────────────────────────────────────────────────────────
LDResult QuantumSearch::terminalTest(const QuantumBoardState& state,
                                     const QuantumTarget& target) const {
    if (target.isImmediatelyDead(state))   return LDResult::DEAD;
    if (target.hasUnconditionalLife(state)) return LDResult::ALIVE;
    return LDResult::UNKNOWN;
}

// ── RZS candidate generation ──────────────────────────────────────────────────
std::vector<QuantumMove> QuantumSearch::generateCandidates(
        const QuantumBoardState& state, const QuantumRZone& rzone) const {
    std::vector<QuantumMove> candidates;
    QColor c = state.sideToMove();
    int n = state.boardSize() * state.boardSize();

    for (int pos = 0; pos < n; ++pos) {
        // Protocol §18: filter by RZ relevance
        if (cfg_.useRZS && rzone.isIrrelevant(state, pos)) continue;
        // AND-legal on both boards
        if (!QuantumMoveGen::isLegalCommon(state, pos)) continue;
        candidates.push_back(QuantumMove::common(c, pos));
    }
    // Always include PASS (null move / irrelevant move handler)
    candidates.push_back(QuantumMove::pass(c));
    return candidates;
}

// ── AND/OR recursive search ───────────────────────────────────────────────────
LDResult QuantumSearch::search(QuantumBoardState& state,
                                QuantumTarget& target,
                                QuantumRZone& rzone,
                                int depth,
                                bool isAttacker,
                                std::vector<QuantumMove>& pv) {
    ++nodes_;

    // Terminal tests first
    LDResult term = terminalTest(state, target);
    if (term != LDResult::UNKNOWN) return term;

    if (depth <= 0) return LDResult::UNKNOWN;

    // Transposition table lookup
    ZKey h = state.hash();
    auto it = tt_.find(h);
    if (it != tt_.end()) return it->second;

    // Generate candidates
    auto candidates = generateCandidates(state, rzone);

    LDResult result = LDResult::UNKNOWN;
    QuantumUndoRecord rec;
    bool allOpponentWins = true;

    for (const auto& move : candidates) {
        QuantumCapture::applyMove(state, move, rec);

        std::vector<QuantumMove> localPv;
        LDResult childResult = search(state, target, rzone, depth - 1,
                                      !isAttacker, localPv);
        QuantumUndo::undo(state, rec);
        rec = {};  // clear for next iteration

        if (isAttacker) {
            // Attacker wants DEAD
            if (childResult == LDResult::DEAD) {
                result = LDResult::DEAD;
                pv.clear();
                pv.push_back(move);
                pv.insert(pv.end(), localPv.begin(), localPv.end());
                allOpponentWins = false;
                break;  // found a kill — stop
            } else if (childResult != LDResult::ALIVE) {
                allOpponentWins = false;
            }
        } else {
            // Defender wants ALIVE
            if (childResult == LDResult::ALIVE) {
                result = LDResult::ALIVE;
                pv.clear();
                pv.push_back(move);
                pv.insert(pv.end(), localPv.begin(), localPv.end());
                allOpponentWins = false;
                break;  // found a living defense — stop
            } else if (childResult != LDResult::DEAD) {
                allOpponentWins = false;
            }
        }
    }

    if (result == LDResult::UNKNOWN) {
        if (allOpponentWins && !candidates.empty()) {
            result = isAttacker ? LDResult::ALIVE : LDResult::DEAD;
        } else {
            result = LDResult::UNKNOWN;
        }
    }

    tt_[h] = result;
    return result;
}

// ── Top-level solve ───────────────────────────────────────────────────────────
SearchResult QuantumSearch::solve(QuantumBoardState& state,
                                  const QuantumTarget& target,
                                  QuantumRZone& rzone) {
    nodes_ = 0;
    tt_.clear();

    SearchResult res;
    std::vector<QuantumMove> pv;

    // Attacker moves first (objective == KILL)
    bool attackerFirst = (target.objective == LDObjective::KILL)
                         ? (state.sideToMove() == target.attackerColor)
                         : (state.sideToMove() == target.defenderColor);

    QuantumTarget tgt = target;
    res.result = search(state, tgt, rzone, cfg_.maxDepth, attackerFirst, pv);
    res.pv     = pv;
    res.nodesSearched = nodes_;
    res.maxDepth = cfg_.maxDepth;
    if (!pv.empty()) res.bestMove = pv[0];

    return res;
}
