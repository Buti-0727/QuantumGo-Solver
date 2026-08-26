#pragma once
// ============================================================================
// QuantumRZone.h  —  Quantum Relevance Zone (RZ_Q)
//
// RZ_Q = RZ_B1 ∪ RZ_B2 ∪ EntangledPartners(RZ)   (Protocol §16–17)
//
// Relevance can propagate through TWO connectivity types:
//   1. Go locality: adjacent positions / group liberties / captures
//   2. Entanglement: B1[A]<->B2[B]  →  if A ∈ RZ_B1 then B ∈ RZ_B2
//
// A move is classified as irrelevant (and treated as a null move) only if
// it cannot affect ANY position in RZ_Q through EITHER path (Protocol §19).
// Geographic distance alone is NEVER sufficient for irrelevance.
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include "QuantumTarget.h"
#include <vector>
#include <unordered_set>

class QuantumRZone {
public:
    // ── Construction ─────────────────────────────────────────────────────────
    QuantumRZone() = default;

    // Build the initial Quantum RZ from a position and target.
    // Seeds with target stones, their liberties, and their entangled partners.
    void build(const QuantumBoardState& state, const QuantumTarget& target);

    // ── Queries ───────────────────────────────────────────────────────────────
    bool inRZ_B1(int pos) const { return rz_b1_.count(pos) > 0; }
    bool inRZ_B2(int pos) const { return rz_b2_.count(pos) > 0; }
    bool inRZ(BoardId b, int pos) const {
        return (b == BoardId::B1) ? inRZ_B1(pos) : inRZ_B2(pos);
    }

    // Is a common-phase move at `pos` within or adjacent to the RZ?
    bool isCandidatePosition(const QuantumBoardState& state, int pos) const;

    // Is a position potentially IRRELEVANT to the L&D objective?
    // A move is irrelevant only if it cannot reach RZ_Q through any chain.
    bool isIrrelevant(const QuantumBoardState& state, int pos) const;

    // ── Dynamic expansion ─────────────────────────────────────────────────────
    // Called when search detects that a boundary move matters.
    // Expands RZ to include pos on board b, propagates through entanglement.
    void expand(const QuantumBoardState& state, BoardId b, int pos);

    int sizeB1() const { return (int)rz_b1_.size(); }
    int sizeB2() const { return (int)rz_b2_.size(); }

    std::string toString(const QuantumBoardState& state) const;

private:
    void addAndPropagate(const QuantumBoardState& state, BoardId b, int pos);
    void addGroupLiberties(const QuantumBoardState& state, BoardId b, int pos);

    std::unordered_set<int> rz_b1_;
    std::unordered_set<int> rz_b2_;
};
