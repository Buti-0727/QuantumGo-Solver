#pragma once
// ============================================================================
// QuantumUndo.h  —  Exact state rollback using QuantumUndoRecord
//
// Protocol §11:
//   play(M) followed by undo(M) must restore the state to EXACTLY S0.
//   Includes: B1, B2, entanglement, ko, side-to-move, hash.
// ============================================================================
#include "QuantumCapture.h"   // brings in QuantumUndoRecord

class QuantumUndo {
public:
    // Undo the move recorded in rec, restoring state to what it was before
    // QuantumCapture::applyMove() was called.
    static void undo(QuantumBoardState& state, const QuantumUndoRecord& rec);
};
