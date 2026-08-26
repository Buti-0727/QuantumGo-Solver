// ============================================================================
// QuantumHash.cpp  —  Zobrist hash initialisation and key access
// ============================================================================
#include "QuantumHash.h"

// Static storage
ZKey QuantumHash::s_stoneKeys[2][MAX_N][3];
ZKey QuantumHash::s_entangleKeys[MAX_N][MAX_N];
ZKey QuantumHash::s_sideKey[3];
ZKey QuantumHash::s_koKeys[2][MAX_N];
bool QuantumHash::s_initialized = false;

// Simple splitmix64 PRNG — deterministic, no external dependency
static uint64_t splitmix64(uint64_t& state) {
    state += 0x9e3779b97f4a7c15ULL;
    uint64_t z = state;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

void QuantumHash::initialize(uint64_t seed) {
    if (s_initialized) return;
    s_initialized = true;
    uint64_t rng = seed;

    // Stone keys: two boards × MAX_N positions × 3 colours (0=EMPTY skipped)
    for (int b = 0; b < 2; ++b)
        for (int p = 0; p < MAX_N; ++p)
            for (int c = 0; c < 3; ++c)
                s_stoneKeys[b][p][c] = splitmix64(rng);

    // Entanglement keys: ordered B1[p]<->B2[q]  (p != q possible — different boards)
    for (int p = 0; p < MAX_N; ++p)
        for (int q = 0; q < MAX_N; ++q)
            s_entangleKeys[p][q] = splitmix64(rng);

    // Side keys
    for (int c = 0; c < 3; ++c)
        s_sideKey[c] = splitmix64(rng);

    // Ko keys
    for (int b = 0; b < 2; ++b)
        for (int p = 0; p < MAX_N; ++p)
            s_koKeys[b][p] = splitmix64(rng);
}

ZKey QuantumHash::stoneKey(BoardId b, int pos, QColor c) {
    assert(s_initialized);
    assert(pos >= 0 && pos < MAX_N);
    return s_stoneKeys[static_cast<int>(b)][pos][static_cast<int>(c)];
}

ZKey QuantumHash::entangleKey(int b1pos, int b2pos) {
    assert(s_initialized);
    assert(b1pos >= 0 && b1pos < MAX_N);
    assert(b2pos >= 0 && b2pos < MAX_N);
    return s_entangleKeys[b1pos][b2pos];
}

ZKey QuantumHash::sideKey(QColor c) {
    assert(s_initialized);
    return s_sideKey[static_cast<int>(c)];
}

ZKey QuantumHash::koKey(BoardId b, int pos) {
    assert(s_initialized);
    assert(pos >= 0 && pos < MAX_N);
    return s_koKeys[static_cast<int>(b)][pos];
}
