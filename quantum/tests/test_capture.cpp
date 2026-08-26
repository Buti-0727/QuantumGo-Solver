// ============================================================================
// test_capture.cpp  —  Layer B: Local + cross-board capture cascades
// ============================================================================
#include "test_framework.h"
#include "../src/QuantumBoardState.h"
#include "../src/QuantumCapture.h"
#include "../src/QuantumUndo.h"

struct CaptureTests {
    CaptureTests() {

        // ── Test 1: Local B1 capture ───────────────────────────────────────
        registerTest("Capture::local_B1_capture", [](){
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::BLACK;
            // Place white center on B1
            s.board(BoardId::B1).placeStone(4, QColor::WHITE);
            // Black surrounds except one liberty (pos 1)
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            s.board(BoardId::B1).placeStone(5, QColor::BLACK);
            s.board(BoardId::B1).placeStone(7, QColor::BLACK);
            // Black plays at pos 1 → captures white center
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::BLACK, 1), rec);
            CHECK(s.board(BoardId::B1).isEmpty(4), "White center captured on B1");
        });

        // ── Test 2: B1→B2 propagation ─────────────────────────────────────
        registerTest("Capture::B1_to_B2_propagation", [](){
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::BLACK;
            s.board(BoardId::B1).placeStone(4, QColor::WHITE);
            s.board(BoardId::B2).placeStone(4, QColor::WHITE);
            s.ent_.link(4, 4);
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            s.board(BoardId::B1).placeStone(5, QColor::BLACK);
            s.board(BoardId::B1).placeStone(7, QColor::BLACK);
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::BLACK, 1), rec);
            CHECK(s.board(BoardId::B1).isEmpty(4), "B1[4] captured");
            CHECK(s.board(BoardId::B2).isEmpty(4), "B2[4] auto-removed via entanglement");
        });

        // ── Test 3: B2→B1 propagation ─────────────────────────────────────
        registerTest("Capture::B2_to_B1_propagation", [](){
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::WHITE;
            s.board(BoardId::B2).placeStone(4, QColor::BLACK);
            s.board(BoardId::B1).placeStone(4, QColor::BLACK);
            s.ent_.link(4, 4);
            for (int p : {3, 5, 7}) s.board(BoardId::B2).placeStone(p, QColor::WHITE);
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::WHITE, 1), rec);
            CHECK(s.board(BoardId::B2).isEmpty(4), "B2[4] captured by white");
            CHECK(s.board(BoardId::B1).isEmpty(4), "B1[4] auto-removed via entanglement");
        });

        // ── Test 4: Multi-hop recursive cascade (B1 -> B2 -> B1) ──────────
        registerTest("Capture::multi_hop_recursive_cascade", [](){
            // 4x4 board
            // Stone A on B1[1] entangled with B2[1] (Stone A')
            // Stone B on B2[2] (adjacent to A') entangled with B1[5] (Stone B')
            // When A is captured on B1:
            //   1. A is removed from B1.
            //   2. A' is removed from B2 (entanglement).
            //   3. Removal of A' or surrounding stones causes B to have 0 liberties on B2.
            //   4. B is captured on B2.
            //   5. B' on B1[5] is removed via entanglement!
            QuantumBoardState s(4);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::BLACK;

            // Setup White stones
            s.board(BoardId::B1).placeStone(0, QColor::WHITE); // Stone A
            s.board(BoardId::B2).placeStone(0, QColor::WHITE); // Stone A'
            s.ent_.link(0, 0);

            s.board(BoardId::B2).placeStone(1, QColor::WHITE); // Stone B (next to A' at 0)
            s.board(BoardId::B1).placeStone(15, QColor::WHITE); // Stone B'
            s.ent_.link(15, 1);

            // Surround B1[0] except liberty at 4
            s.board(BoardId::B1).placeStone(1, QColor::BLACK);
            // Surround B2[1] on other sides (2 and 5) so it only relies on 0 for liberty or liberties
            s.board(BoardId::B2).placeStone(2, QColor::BLACK);
            s.board(BoardId::B2).placeStone(5, QColor::BLACK);

            // Play Black at pos 4 on both boards
            // On B1: Black[4] fills last liberty of White[0] -> White[0] captured!
            // Cascade: White[0] on B2 removed -> White[1] on B2 now has 0 liberties -> captured!
            // Cascade: White[1] on B2 captured -> White[15] on B1 removed!
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::BLACK, 4), rec);

            CHECK(s.board(BoardId::B1).isEmpty(0), "B1[0] captured");
            CHECK(s.board(BoardId::B2).isEmpty(0), "B2[0] removed via entanglement");
            CHECK(s.board(BoardId::B2).isEmpty(1), "B2[1] captured in cascade");
            CHECK(s.board(BoardId::B1).isEmpty(15), "B1[15] removed via 2nd-hop cascade");

            // Test exact undo of this multi-hop cascade
            QuantumUndo::undo(s, rec);
            CHECK(s.board(BoardId::B1).colorAt(0) == QColor::WHITE, "B1[0] restored");
            CHECK(s.board(BoardId::B2).colorAt(0) == QColor::WHITE, "B2[0] restored");
            CHECK(s.board(BoardId::B2).colorAt(1) == QColor::WHITE, "B2[1] restored");
            CHECK(s.board(BoardId::B1).colorAt(15) == QColor::WHITE, "B1[15] restored");
            CHECK(s.ent().hasPartner(BoardId::B1, 0), "Link A-A' restored");
            CHECK(s.ent().hasPartner(BoardId::B1, 15), "Link B-B' restored");
        });

        // ── Test 5: No double-removal (partner already gone) ──────────────
        registerTest("Capture::no_double_removal", [](){
            QuantumBoardState s(3);
            s.moveNumber_ = 3;
            s.sideToMove_ = QColor::BLACK;
            s.board(BoardId::B1).placeStone(0, QColor::WHITE);
            s.board(BoardId::B2).placeStone(0, QColor::WHITE);
            s.ent_.link(0, 0);
            // Remove B2[0] manually (simulates a prior cascade)
            s.board(BoardId::B2).removeStone(0);
            s.ent_.unlink(BoardId::B2, 0);
            // Now place black to surround B1[0]
            s.board(BoardId::B1).placeStone(1, QColor::BLACK);
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            QuantumUndoRecord rec;
            QuantumCapture::applyMove(s, QuantumMove::common(QColor::BLACK, 2), rec);
            CHECK(true, "No crash on already-removed partner");
        });
    }
} s_captureTests;
