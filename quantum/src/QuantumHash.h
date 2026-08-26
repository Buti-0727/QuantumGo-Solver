#pragma once
// ============================================================================
// QuantumHash.h  —  Zobrist hashing for the joint QuantumGo state
//
// Hash = hash(B1_stones) XOR hash(B2_stones) XOR hash(entanglement)
//        XOR hash(side_to_move) XOR hash(ko_state)
//
// Critical test (Coding Protocol §12):
//   State A: B1[D4]<->B2[C3]
//   State B: B1[D4]<->B2[F4]
//   Must produce DIFFERENT keys even when stone layouts are identical.
// ============================================================================

#include "QuantumTypes.h"

class QuantumHash {
public:
    static constexpr int MAX_BS = QGO_MAX_BOARD_SIZE;
    static constexpr int MAX_N  = QGO_MAX_GRIDS;

    // Call once at program start
    static void initialize(uint64_t seed = 0xDEADBEEFCAFEBABEULL);

    // Per-stone hash (board b, position pos, colour c)
    static ZKey stoneKey(BoardId b, int pos, QColor c);

    // Entanglement pair key: XOR when a B1[p]<->B2[q] link is active
    // Symmetric: entangleKey(p,q) == entangleKey(p,q) — NOT q,p (ordered pair
    // because the pair has a canonical B1/B2 orientation).
    static ZKey entangleKey(int b1pos, int b2pos);

    // Side-to-move key
    static ZKey sideKey(QColor sideToMove);

    // Ko key (position on B1 or B2 where ko is in effect, board id, or -1)
    static ZKey koKey(BoardId b, int pos);

private:
    static ZKey s_stoneKeys[2][MAX_N][3];    // [board][pos][colour]
    static ZKey s_entangleKeys[MAX_N][MAX_N]; // [b1pos][b2pos]
    static ZKey s_sideKey[3];                 // [QColor]
    static ZKey s_koKeys[2][MAX_N];           // [board][pos]
    static bool s_initialized;
};
