// ============================================================================
// main.cpp  —  QuantumGo L&D Solver CLI entry point
// ============================================================================
#include "src/QuantumBoardState.h"
#include "src/QuantumTarget.h"
#include "src/QuantumLDSolver.h"
#include <iostream>

int main() {
    QuantumHash::initialize();

    std::cout << "QuantumGo L&D Solver — ready.\n";
    std::cout << "Usage: configure QuantumBoardState and QuantumTarget in code,\n";
    std::cout << "       or use the test suite (qgo_tests) for validation.\n\n";

    // ── Example: Black to play first to kill target group on 5×5 board ─────
    QuantumBoardState state(5);
    state.moveNumber_ = 3;
    state.sideToMove_ = QColor::BLACK;  // Black plays first!

    // White group at center (12 / C3) on both boards, entangled
    state.board(BoardId::B1).placeStone(12, QColor::WHITE);
    state.board(BoardId::B2).placeStone(12, QColor::WHITE);
    state.ent_.link(12, 12);

    // Black surrounds White at C2 (7), B3 (11), C4 (17), leaving D3 (13) in atari
    for (int p : {7, 11, 17}) {
        state.board(BoardId::B1).placeStone(p, QColor::BLACK);
        state.board(BoardId::B2).placeStone(p, QColor::BLACK);
    }

    QuantumTarget target;
    target.defenderColor = QColor::WHITE;
    target.attackerColor = QColor::BLACK;
    target.objective     = LDObjective::KILL;
    target.b1Stones      = {12};
    target.b2Stones      = {12};

    QuantumSearch::Config cfg;
    cfg.maxDepth = 10;
    cfg.useRZS   = true;

    QuantumLDSolver solver(cfg);
    SearchResult result = solver.solve(state, target);

    std::cout << QuantumLDSolver::formatResult(result, state, target);
    return 0;
}
