// ============================================================================
// QuantumLDSolver.cpp
// ============================================================================
#include "QuantumLDSolver.h"
#include <sstream>
#include <iostream>

SearchResult QuantumLDSolver::solve(QuantumBoardState& state,
                                    const QuantumTarget& target) {
    // Build Quantum RZ from the initial position
    QuantumRZone rzone;
    rzone.build(state, target);

    return search_.solve(state, target, rzone);
}

std::string QuantumLDSolver::formatResult(const SearchResult& res,
                                          const QuantumBoardState& state,
                                          const QuantumTarget& target) {
    std::ostringstream oss;
    oss << "=== QuantumGo L&D Result ===\n";
    oss << "Result:      " << toString(res.result) << "\n";
    oss << "Objective:   " << (target.objective == LDObjective::KILL ? "KILL" : "LIVE") << "\n";
    oss << "Attacker:    " << (target.attackerColor == QColor::BLACK ? "Black" : "White") << "\n";
    oss << "Nodes:       " << res.nodesSearched << "\n";

    if (!res.pv.empty()) {
        oss << "Best line:   ";
        for (size_t i = 0; i < res.pv.size() && i < 10; ++i) {
            oss << res.pv[i].toString(state.boardSize());
            if (i + 1 < res.pv.size()) oss << " ";
        }
        oss << "\n";
    }

    oss << "\n--- B1 ---\n" << state.board(BoardId::B1).toString();
    oss << "--- B2 ---\n" << state.board(BoardId::B2).toString();
    oss << state.ent().toString() << "\n";
    return oss.str();
}
