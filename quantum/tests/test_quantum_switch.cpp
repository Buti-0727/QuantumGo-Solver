// ============================================================================
// test_quantum_switch.cpp  —  Tests for 2-Stone Quantum Switch Optimization
// ============================================================================
#include "test_framework.h"
#include "../src/QuantumBoardState.h"
#include "../src/QuantumTarget.h"
#include "../src/QuantumLDSolver.h"
#include "../src/QuantumCapture.h"
#include <vector>
#include <iostream>
#include <algorithm>

struct QuantumSwitchTests {
    QuantumSwitchTests() {

        // ── Test 1: Quantum switch increases search tree complexity ────────
        registerTest("QuantumSwitch::search_complexity_expansion", [](){
            // Base 5x5 board position with a contested corner
            // Classical state:
            QuantumBoardState classicalState(5);
            classicalState.moveNumber_ = 3;
            classicalState.sideToMove_ = QColor::BLACK;

            // Target black group
            classicalState.board(BoardId::B1).placeStone(0, QColor::BLACK); // A1
            classicalState.board(BoardId::B1).placeStone(1, QColor::BLACK); // B1
            classicalState.board(BoardId::B2).placeStone(0, QColor::BLACK);
            classicalState.board(BoardId::B2).placeStone(1, QColor::BLACK);

            // Surrounding white stones
            classicalState.board(BoardId::B1).placeStone(5, QColor::WHITE); // A2
            classicalState.board(BoardId::B1).placeStone(6, QColor::WHITE); // B2
            classicalState.board(BoardId::B2).placeStone(5, QColor::WHITE);
            classicalState.board(BoardId::B2).placeStone(6, QColor::WHITE);

            QuantumTarget target;
            target.defenderColor = QColor::BLACK;
            target.attackerColor = QColor::WHITE;
            target.objective     = LDObjective::LIVE;
            target.b1Stones      = {0, 1};
            target.b2Stones      = {0, 1};

            QuantumSearch::Config cfg;
            cfg.maxDepth = 4;
            cfg.useRZS   = true;

            QuantumLDSolver solver(cfg);
            auto resClassical = solver.solve(classicalState, target);

            // Now apply 2-Stone Quantum switch:
            // Switch Black stone at (1) to entangled pair (1 on B1 <-> 2 on B2)
            // Switch White stone at (6) to entangled pair (6 on B1 <-> 7 on B2)
            QuantumBoardState quantumState(5);
            quantumState.moveNumber_ = 3;
            quantumState.sideToMove_ = QColor::BLACK;

            quantumState.board(BoardId::B1).placeStone(0, QColor::BLACK);
            quantumState.board(BoardId::B1).placeStone(1, QColor::BLACK);
            quantumState.board(BoardId::B2).placeStone(0, QColor::BLACK);
            quantumState.board(BoardId::B2).placeStone(2, QColor::BLACK); // alternate on B2
            quantumState.ent_.link(1, 2);

            quantumState.board(BoardId::B1).placeStone(5, QColor::WHITE);
            quantumState.board(BoardId::B1).placeStone(6, QColor::WHITE);
            quantumState.board(BoardId::B2).placeStone(5, QColor::WHITE);
            quantumState.board(BoardId::B2).placeStone(7, QColor::WHITE); // alternate on B2
            quantumState.ent_.link(6, 7);

            QuantumTarget targetQ = target;
            targetQ.b2Stones = {0, 2};

            auto resQuantum = solver.solve(quantumState, targetQ);

            CHECK(resQuantum.nodesSearched >= resClassical.nodesSearched,
                  "Quantum switch creates broader branching factor and search complexity");
        });

        // ── Test 2: Entanglement cascade sensitivity ────────────────────────
        registerTest("QuantumSwitch::entanglement_cascade_trigger", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::WHITE;

            // Black at pos 12 (B1) entangled with pos 14 (B2)
            s.board(BoardId::B1).placeStone(12, QColor::BLACK);
            s.board(BoardId::B2).placeStone(14, QColor::BLACK);
            s.ent_.link(12, 14);

            // White surrounds B1[12] on 3 sides
            s.board(BoardId::B1).placeStone(7, QColor::WHITE);
            s.board(BoardId::B1).placeStone(11, QColor::WHITE);
            s.board(BoardId::B1).placeStone(17, QColor::WHITE);

            // Pos 13 is empty on both boards. Attacker (White) plays at pos 13 to capture B1[12]
            QuantumUndoRecord rec;
            bool ok = QuantumCapture::applyMove(s, QuantumMove::common(QColor::WHITE, 13), rec);
            CHECK(ok, "Attacker move applied successfully");

            // Verify B1[12] was captured, and entangled partner B2[14] is removed via cascade
            CHECK(s.board(BoardId::B1).colorAt(12) == QColor::EMPTY, "B1[12] captured");
            CHECK(s.board(BoardId::B2).colorAt(14) == QColor::EMPTY, "Entangled partner B2[14] removed via cascade");
        });

        // ── Test 3: Exhaustive pair switch complexity benchmark ─────────────
        registerTest("QuantumSwitch::exhaustive_pair_benchmark", [](){
            std::vector<int> blackStones = {0, 1, 5};
            std::vector<int> whiteStones = {18, 19, 23};

            struct SwitchScore {
                int b, w;
                int nodes;
            };
            std::vector<SwitchScore> scores;

            for (int b : blackStones) {
                for (int w : whiteStones) {
                    QuantumBoardState s(5);
                    s.moveNumber_ = 3;
                    s.sideToMove_ = QColor::BLACK;

                    for (int p : blackStones) {
                        s.board(BoardId::B1).placeStone(p, QColor::BLACK);
                        s.board(BoardId::B2).placeStone(p, QColor::BLACK);
                    }
                    for (int p : whiteStones) {
                        s.board(BoardId::B1).placeStone(p, QColor::WHITE);
                        s.board(BoardId::B2).placeStone(p, QColor::WHITE);
                    }

                    // Choose disjoint empty coordinates for B2 partner
                    int b_partner = (b == 0) ? 6 : (b == 1 ? 7 : 11);
                    int w_partner = (w == 18) ? 13 : (w == 19 ? 14 : 22);

                    s.board(BoardId::B2).removeStone(b);
                    s.board(BoardId::B2).placeStone(b_partner, QColor::BLACK);
                    s.ent_.link(b, b_partner);

                    s.board(BoardId::B2).removeStone(w);
                    s.board(BoardId::B2).placeStone(w_partner, QColor::WHITE);
                    s.ent_.link(w, w_partner);

                    QuantumTarget target;
                    target.defenderColor = QColor::BLACK;
                    target.attackerColor = QColor::WHITE;
                    target.objective     = LDObjective::LIVE;
                    target.b1Stones      = blackStones;
                    target.b2Stones      = {0, 1, 5};
                    for (size_t i = 0; i < target.b2Stones.size(); ++i) {
                        if (target.b2Stones[i] == b) target.b2Stones[i] = b_partner;
                    }

                    QuantumSearch::Config cfg;
                    cfg.maxDepth = 4;
                    cfg.useRZS   = false;
                    QuantumLDSolver solver(cfg);
                    auto res = solver.solve(s, target);

                    scores.push_back({b, w, res.nodesSearched});
                }
            }

            CHECK(scores.size() == 9, "Evaluated all 9 pair combinations (3x3)");
            auto maxElem = std::max_element(scores.begin(), scores.end(),
                [](const SwitchScore& a, const SwitchScore& b) { return a.nodes < b.nodes; });
            CHECK(maxElem->nodes > 0, "Max complexity pair found with positive search nodes");
        });
    }
} s_quantumSwitchTests;
