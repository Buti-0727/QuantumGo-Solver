// ============================================================================
// test_entanglement.cpp  —  Layer A: Entanglement table invariants
// ============================================================================
#include "test_framework.h"
#include "EntanglementTable.h"
#include "QuantumHash.h"

// Register via static initialiser
struct EntanglementTests {
    EntanglementTests() {
        QuantumHash::initialize();

        registerTest("EntanglementTable::link_and_partnerOf", [](){
            EntanglementTable t(9);
            t.link(0, 5);
            CHECK(t.hasPartner(BoardId::B1, 0), "B1[0] should have partner");
            CHECK(t.partnerOf(BoardId::B1, 0) == 5, "B1[0] partner should be 5");
            CHECK(t.hasPartner(BoardId::B2, 5), "B2[5] should have partner");
            CHECK(t.partnerOf(BoardId::B2, 5) == 0, "B2[5] partner should be 0");
        });

        registerTest("EntanglementTable::symmetry_invariant", [](){
            EntanglementTable t(9);
            t.link(3, 7);
            // partner(partner(S)) == S
            int q = t.partnerOf(BoardId::B1, 3);
            int p = t.partnerOf(BoardId::B2, q);
            CHECK(p == 3, "Symmetry: partner(partner(B1[3])) == 3");
        });

        registerTest("EntanglementTable::unlink_removes_both_ends", [](){
            EntanglementTable t(9);
            t.link(2, 6);
            t.unlink(BoardId::B1, 2);
            CHECK(!t.hasPartner(BoardId::B1, 2), "B1[2] should be unlinked");
            CHECK(!t.hasPartner(BoardId::B2, 6), "B2[6] should be unlinked");
        });

        registerTest("EntanglementTable::snapshot_restore", [](){
            EntanglementTable t(9);
            t.link(0, 5);
            t.link(1, 8);
            auto snap = t.snapshot();
            t.unlink(BoardId::B1, 0);
            CHECK(!t.hasPartner(BoardId::B1, 0), "Unlinked");
            t.restore(snap);
            CHECK(t.hasPartner(BoardId::B1, 0), "Restored B1[0]");
            CHECK(t.partnerOf(BoardId::B1, 0) == 5, "Restored partner == 5");
        });

        registerTest("EntanglementTable::different_entanglement_different_hash", [](){
            // Protocol §12 critical test
            EntanglementTable a(9), b(9);
            a.link(30, 20);  // B1[D4]<->B2[C3] conceptually
            b.link(30, 23);  // B1[D4]<->B2[F4] conceptually
            ZKey ha = a.zobristHash();
            ZKey hb = b.zobristHash();
            CHECK(ha != hb, "Different entanglement must produce different hashes");
        });
    }
} s_entanglementTests;
