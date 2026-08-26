// ============================================================================
// test_games_eval.cpp  —  Validation on real self-play & game_eval datasets
// ============================================================================
#include "test_framework.h"
#include "../src/QuantumBoardState.h"
#include "../src/QuantumTarget.h"
#include "../src/QuantumLDSolver.h"
#include "../src/QuantumSgfParser.h"
#include <iostream>

struct GamesEvalTests {
    GamesEvalTests() {

        registerTest("GamesEval::parse_and_replay_game_00001", [](){
            std::string path = "/Users/lenovo/Desktop/QuantumGo Life-and-Death solver/game_eval/game_eval_sp00010000/9x9/game_00001.sgf";
            QuantumGameRecord record;
            bool ok = QuantumSgfParser::parseFile(path, record);
            CHECK(ok, "Failed to parse game_00001.sgf");
            CHECK(record.boardSize == 9, "Board size should be 9");
            CHECK(record.moves.size() > 20, "Should have more than 20 moves");

            // Replay to move 20
            QuantumBoardState state(9);
            ok = QuantumSgfParser::replayToPly(record, 20, state);
            CHECK(ok, "Replay to ply 20 failed");

            // Verify state invariants hold on the replayed state
            std::string err = state.checkInvariants();
            CHECK(err.empty(), "Invariants failed on ply 20: " + err);
        });

        registerTest("GamesEval::parse_and_replay_game_00002", [](){
            std::string path = "/Users/lenovo/Desktop/QuantumGo Life-and-Death solver/game_eval/game_eval_sp00010000/9x9/game_00002.sgf";
            QuantumGameRecord record;
            bool ok = QuantumSgfParser::parseFile(path, record);
            CHECK(ok, "Failed to parse game_00002.sgf");

            // Replay to move 30
            QuantumBoardState state(9);
            ok = QuantumSgfParser::replayToPly(record, 30, state);
            CHECK(ok, "Replay to ply 30 failed");

            std::string err = state.checkInvariants();
            CHECK(err.empty(), "Invariants failed on ply 30: " + err);
        });

        registerTest("GamesEval::solver_accuracy_on_game_position", [](){
            // Extract a mid-game tactical position from game_00001 at ply 35
            std::string path = "/Users/lenovo/Desktop/QuantumGo Life-and-Death solver/game_eval/game_eval_sp00010000/9x9/game_00001.sgf";
            QuantumGameRecord record;
            QuantumSgfParser::parseFile(path, record);

            QuantumBoardState state(9);
            QuantumSgfParser::replayToPly(record, 35, state);

            // Test target group: corner stones
            QuantumTarget target;
            target.defenderColor = QColor::BLACK;
            target.attackerColor = QColor::WHITE;
            target.objective     = LDObjective::KILL;
            // Target any living black stone on board
            for (int p = 0; p < 81; ++p) {
                if (state.board(BoardId::B1).colorAt(p) == QColor::BLACK) {
                    target.b1Stones.push_back(p);
                    break;
                }
            }

            QuantumSearch::Config cfg;
            cfg.maxDepth = 6;
            cfg.useRZS   = true;
            QuantumLDSolver solver(cfg);
            auto res = solver.solve(state, target);

            CHECK(res.nodesSearched > 0, "Solver should explore nodes");
            CHECK(res.result != LDResult::UNKNOWN, "Solver should reach definite proof");
        });
    }
} s_gamesEvalTests;
