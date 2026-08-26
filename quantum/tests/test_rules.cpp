// ============================================================================
// test_rules.cpp  —  Layer A: Move legality (Protocol §3, §8)
// ============================================================================
#include "test_framework.h"
#include "QuantumBoardState.h"
#include "QuantumMoveGen.h"

struct RulesTests {
    RulesTests() {
        registerTest("Rules::common_legal_on_both_boards", [](){
            QuantumBoardState s(5);
            // Empty 5x5, move 3+ (manually set move number past opening)
            s.moveNumber_ = 3;
            // Any empty position should be AND-legal on empty boards
            CHECK(QuantumMoveGen::isLegalCommon(s, 0), "pos 0 legal on empty 5x5");
            CHECK(QuantumMoveGen::isLegalCommon(s, 12), "center legal on empty 5x5");
        });

        registerTest("Rules::common_illegal_if_occupied_on_B1", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            // Place black stone on B1 at pos 5
            s.board(BoardId::B1).placeStone(5, QColor::BLACK);
            // Should be illegal: occupied on B1
            CHECK(!QuantumMoveGen::isLegalCommon(s, 5),
                  "occupied on B1 -> illegal for common move");
        });

        registerTest("Rules::common_illegal_if_occupied_on_B2", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B2).placeStone(5, QColor::WHITE);
            CHECK(!QuantumMoveGen::isLegalCommon(s, 5),
                  "occupied on B2 -> illegal for common move");
        });

        registerTest("Rules::common_illegal_if_occupied_on_both", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(5, QColor::BLACK);
            s.board(BoardId::B2).placeStone(5, QColor::WHITE);
            CHECK(!QuantumMoveGen::isLegalCommon(s, 5),
                  "occupied on both -> illegal");
        });

        registerTest("Rules::opening_legal_independent_coords", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 1;
            // p1=0 on B1, p2=24 on B2 — both empty
            CHECK(QuantumMoveGen::isLegalOpening(s, 0, 24, QColor::BLACK),
                  "Opening legal with independent coords");
        });

        registerTest("Rules::suicide_illegal", [](){
            // Build a position where placing at pos is suicide on B1
            // 3x3 board: surround pos 4 (center) with opponent stones
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::WHITE;
            // Black surrounds the center on B1
            for (int nb : {1, 3, 5, 7}) {
                s.board(BoardId::B1).placeStone(nb, QColor::BLACK);
            }
            // White playing center on B1 would be suicide (no liberty)
            // B2 is empty — but AND-legal requires B1 also legal
            CHECK(!QuantumMoveGen::isLegalCommon(s, 4),
                  "Suicide on B1 makes move illegal");
        });
    }
} s_rulesTests;
