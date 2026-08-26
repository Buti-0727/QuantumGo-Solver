// ============================================================================
// test_state.cpp  —  Layer C: Clone, hash, and undo tests (Protocol §11, §12)
// ============================================================================
#include "test_framework.h"
#include "QuantumBoardState.h"
#include "QuantumCapture.h"
#include "QuantumUndo.h"
#include "QuantumMoveGen.h"

struct StateTests {
    StateTests() {

        // ── Test 1: Clone produces identical state ─────────────────────────
        registerTest("State::clone_identical", [](){
            QuantumBoardState s(5);
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            s.board(BoardId::B2).placeStone(7, QColor::WHITE);
            s.ent_.link(3, 7);
            auto c = s.clone();
            CHECK(c.board(BoardId::B1).colorAt(3) == QColor::BLACK, "B1 clone correct");
            CHECK(c.board(BoardId::B2).colorAt(7) == QColor::WHITE, "B2 clone correct");
            CHECK(c.ent().hasPartner(BoardId::B1, 3), "Entanglement cloned");
            CHECK(c.hash() == s.hash(), "Hash cloned identically");
        });

        // ── Test 2: Different entanglement → different hash (Protocol §12) ──
        registerTest("State::hash_distinguishes_entanglement", [](){
            QuantumBoardState a(9), b(9);
            // Same stone layout on both boards
            a.board(BoardId::B1).placeStone(30, QColor::BLACK);
            a.board(BoardId::B2).placeStone(20, QColor::BLACK);
            b.board(BoardId::B1).placeStone(30, QColor::BLACK);
            b.board(BoardId::B2).placeStone(23, QColor::BLACK);
            // Different entanglement
            a.ent_.link(30, 20);
            b.ent_.link(30, 23);
            // Recompute hashes manually
            ZKey ha = QuantumHash::stoneKey(BoardId::B1, 30, QColor::BLACK)
                    ^ QuantumHash::stoneKey(BoardId::B2, 20, QColor::BLACK)
                    ^ QuantumHash::entangleKey(30, 20)
                    ^ QuantumHash::sideKey(QColor::BLACK);
            ZKey hb = QuantumHash::stoneKey(BoardId::B1, 30, QColor::BLACK)
                    ^ QuantumHash::stoneKey(BoardId::B2, 23, QColor::BLACK)
                    ^ QuantumHash::entangleKey(30, 23)
                    ^ QuantumHash::sideKey(QColor::BLACK);
            CHECK(ha != hb, "Protocol §12: different entanglement → different hash");
        });

        // ── Test 3: play → undo restores exact state ───────────────────────
        registerTest("State::undo_restores_exact_state", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            auto before = s.clone();

            QuantumMove mv = QuantumMove::common(QColor::BLACK, 5);
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, mv, rec);

            QuantumUndo::undo(s, rec);

            // Compare
            for (int p = 0; p < 25; ++p) {
                CHECK(s.board(BoardId::B1).colorAt(p) == before.board(BoardId::B1).colorAt(p),
                      "B1 restored at " + std::to_string(p));
                CHECK(s.board(BoardId::B2).colorAt(p) == before.board(BoardId::B2).colorAt(p),
                      "B2 restored at " + std::to_string(p));
            }
            CHECK(s.hash() == before.hash(), "Hash restored");
            CHECK(s.sideToMove() == before.sideToMove(), "Side restored");
            CHECK(s.moveNumber() == before.moveNumber(), "MoveNumber restored");
        });

        // ── Test 4: Undo with capture cascade ─────────────────────────────
        registerTest("State::undo_with_capture_cascade", [](){
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(4, QColor::WHITE);
            s.board(BoardId::B2).placeStone(4, QColor::WHITE);
            s.ent_.link(4, 4);
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            s.board(BoardId::B1).placeStone(5, QColor::BLACK);
            s.board(BoardId::B1).placeStone(7, QColor::BLACK);

            auto before = s.clone();

            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::BLACK, 1), rec);
            // B1[4] and B2[4] should be captured
            QuantumUndo::undo(s, rec);

            CHECK(s.board(BoardId::B1).colorAt(4) == QColor::WHITE, "B1[4] restored after undo");
            CHECK(s.board(BoardId::B2).colorAt(4) == QColor::WHITE, "B2[4] restored after undo");
            CHECK(s.ent().hasPartner(BoardId::B1, 4), "Entanglement restored");
            CHECK(s.hash() == before.hash(), "Hash restored after cascade undo");
        });

        // ── Test 5: Invariant checker passes on valid state ────────────────
        registerTest("State::invariant_checker_passes", [](){
            QuantumBoardState s(5);
            s.board(BoardId::B1).placeStone(0, QColor::BLACK);
            s.board(BoardId::B2).placeStone(5, QColor::BLACK);
            s.ent_.link(0, 5);
            auto err = s.checkInvariants();
            CHECK(err.empty(), "Invariants pass: " + err);
        });
    }
} s_stateTests;
