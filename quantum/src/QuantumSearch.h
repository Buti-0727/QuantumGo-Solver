#pragma once
// ============================================================================
// QuantumSearch.h  —  Exact AND/OR RZS search for QuantumGo L&D
//
// Implements depth-limited alpha-beta AND/OR search following the
// RZS (Relevance Zone Search) methodology (Protocol §20–21):
//   - Candidates are filtered through QuantumRZone
//   - Irrelevant moves are treated as null/pass
//   - Exact terminal conditions: ALIVE / DEAD / UNKNOWN
//   - Transposition table keyed on joint QuantumGo hash
//
// This is NOT MCTS. It is an exact proof search.
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include "QuantumTarget.h"
#include "QuantumRZone.h"
#include "QuantumCapture.h"
#include "QuantumUndo.h"
#include "QuantumMoveGen.h"
#include <unordered_map>
#include <vector>
#include <string>

struct SearchResult {
    LDResult result  = LDResult::UNKNOWN;
    QuantumMove bestMove;
    std::vector<QuantumMove> pv;  // principal variation
    int nodesSearched = 0;
    int maxDepth      = 0;
};

class QuantumSearch {
public:
    struct Config {
        int  maxDepth       = 60;
        bool useRZS         = true;   // enable RZS candidate filtering
        bool verbose        = false;
    };

    QuantumSearch() : cfg_{} {}
    explicit QuantumSearch(const Config& cfg) : cfg_(cfg) {}

    // Main solve entry point
    SearchResult solve(QuantumBoardState& state,
                       const QuantumTarget& target,
                       QuantumRZone& rzone);

    // Statistics
    int nodesSearched() const { return nodes_; }

private:
    // AND/OR search: returns LDResult from the perspective of the attacker.
    // depth: plies remaining. isAttacker: true when it's the attacker's turn.
    LDResult search(QuantumBoardState& state,
                    QuantumTarget& target,
                    QuantumRZone& rzone,
                    int depth,
                    bool isAttacker,
                    std::vector<QuantumMove>& pv);

    // Terminal test (fast)
    LDResult terminalTest(const QuantumBoardState& state,
                          const QuantumTarget& target) const;

    // RZS candidate generation: positions in or adjacent to RZ, AND-legal
    std::vector<QuantumMove> generateCandidates(const QuantumBoardState& state,
                                                 const QuantumRZone& rzone) const;

    Config cfg_;
    int    nodes_ = 0;
    std::unordered_map<ZKey, LDResult> tt_;  // simple transposition table
};
