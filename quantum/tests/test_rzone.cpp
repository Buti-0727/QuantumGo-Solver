// ============================================================================
// test_rzone.cpp  —  Layer E: Quantum RZone tests
// ============================================================================
#include "test_framework.h"
#include "QuantumBoardState.h"
#include "QuantumRZone.h"
#include "QuantumTarget.h"

struct RZoneTests {
    RZoneTests() {

        // ── Test 1: Initial RZ contains target stones ──────────────────────
        registerTest("RZone::initial_RZ_contains_target", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(12, QColor::BLACK);
            s.board(BoardId::B2).placeStone(12, QColor::BLACK);

            QuantumTarget t;
            t.defenderColor = QColor::BLACK;
            t.attackerColor = QColor::WHITE;
            t.b1Stones = {12};
            t.b2Stones = {12};

            QuantumRZone rz;
            rz.build(s, t);
            CHECK(rz.inRZ_B1(12), "Target pos 12 in RZ_B1");
            CHECK(rz.inRZ_B2(12), "Target pos 12 in RZ_B2");
        });

        // ── Test 2: RZ propagates through entanglement ─────────────────────
        registerTest("RZone::propagates_through_entanglement", [](){
            // Target on B1 at pos 3. Entangled with B2 pos 7.
            // Building RZ should include B2[7] via entanglement propagation.
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(3, QColor::BLACK);
            s.board(BoardId::B2).placeStone(7, QColor::BLACK);
            s.ent_.link(3, 7);

            QuantumTarget t;
            t.defenderColor = QColor::BLACK;
            t.attackerColor = QColor::WHITE;
            t.b1Stones = {3};
            t.b2Stones = {};  // explicitly NOT listed, but entangled

            QuantumRZone rz;
            rz.build(s, t);
            CHECK(rz.inRZ_B1(3), "B1[3] in RZ");
            CHECK(rz.inRZ_B2(7), "B2[7] in RZ via entanglement propagation");
        });

        // ── Test 3: Far-away position not classified irrelevant if entangled
        registerTest("RZone::entangled_position_not_irrelevant", [](){
            // B1 target at pos 12 (center of 5x5). B2 partner at pos 0 (corner).
            // pos 0 is geographically far from target but linked by entanglement.
            // Must NOT be classified as irrelevant.
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(12, QColor::BLACK);
            s.board(BoardId::B2).placeStone(0,  QColor::BLACK);
            s.ent_.link(12, 0);

            QuantumTarget t;
            t.defenderColor = QColor::BLACK;
            t.attackerColor = QColor::WHITE;
            t.b1Stones = {12};
            t.b2Stones = {0};

            QuantumRZone rz;
            rz.build(s, t);
            // B2[0] is the entangled partner of B1[12] — must be in RZ
            CHECK(!rz.isIrrelevant(s, 0), "pos 0 is NOT irrelevant (entangled to target)");
        });

        // ── Test 4: Dynamic RZ expansion ──────────────────────────────────
        registerTest("RZone::dynamic_expansion", [](){
            QuantumBoardState s(5);
            s.moveNumber_ = 3;
            s.board(BoardId::B1).placeStone(12, QColor::BLACK);

            QuantumTarget t;
            t.defenderColor = QColor::BLACK;
            t.b1Stones = {12};

            QuantumRZone rz;
            rz.build(s, t);
            int sz_before = rz.sizeB1();

            // Expand to include pos 20 (far from center)
            rz.expand(s, BoardId::B1, 20);
            CHECK(rz.sizeB1() > sz_before, "RZ expanded after expand()");
            CHECK(rz.inRZ_B1(20), "pos 20 in RZ after expansion");
        });
    }
} s_rzoneTests;
