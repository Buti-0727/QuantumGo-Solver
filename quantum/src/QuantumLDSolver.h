#pragma once
// ============================================================================
// QuantumLDSolver.h  —  Top-level L&D solver API
// ============================================================================
#include "QuantumBoardState.h"
#include "QuantumTarget.h"
#include "QuantumRZone.h"
#include "QuantumSearch.h"
#include <string>

class QuantumLDSolver {
public:
    QuantumLDSolver() : search_{} {}
    explicit QuantumLDSolver(const QuantumSearch::Config& cfg) : search_(cfg) {}

    // Solve the given position. Returns the full SearchResult.
    SearchResult solve(QuantumBoardState& state, const QuantumTarget& target);

    // Pretty-print the result (Protocol §22)
    static std::string formatResult(const SearchResult& res,
                                    const QuantumBoardState& state,
                                    const QuantumTarget& target);

private:
    QuantumSearch search_;
};
