// ============================================================================
// QuantumBoardState.cpp
// ============================================================================
#include "QuantumBoardState.h"
#include "QuantumHash.h"
#include <sstream>

QuantumBoardState::QuantumBoardState(int boardSize)
    : boardSize_(boardSize), b1_(boardSize), b2_(boardSize), ent_(boardSize)
{
    QuantumHash::initialize();
    reset();
}

void QuantumBoardState::reset() {
    b1_.reset(boardSize_);
    b2_.reset(boardSize_);
    ent_.reset();
    sideToMove_ = QColor::BLACK;
    moveNumber_ = 0;
    ko_[0] = ko_[1] = QGO_INVALID_POS;
    hash_ = 0;
    // Initial hash: side to move is BLACK
    hash_ ^= QuantumHash::sideKey(QColor::BLACK);
}

std::string QuantumBoardState::checkInvariants() const {
    int n = boardSize_ * boardSize_;
    // Invariant 1: every stone has exactly one colour
    for (int p = 0; p < n; ++p) {
        QColor c1 = b1_.colorAt(p);
        QColor c2 = b2_.colorAt(p);
        if (c1 == QColor::BORDER || c2 == QColor::BORDER)
            return "BORDER colour found at pos " + std::to_string(p);
    }
    // Invariant 2/3: entanglement symmetry + no duplicate partners
    for (int p = 0; p < n; ++p) {
        int q = ent_.partnerOf(BoardId::B1, p);
        if (q == QGO_INVALID_POS) continue;
        // partner(partner(S)) == S
        if (ent_.partnerOf(BoardId::B2, q) != p)
            return "Entanglement asymmetry: B1[" + std::to_string(p) + "]<->B2[" + std::to_string(q) + "]";
        // Both endpoints must be occupied
        if (b1_.isEmpty(p))
            return "Entangled B1[" + std::to_string(p) + "] is empty";
        if (b2_.isEmpty(q))
            return "Entangled B2[" + std::to_string(q) + "] is empty";
    }
    return "";   // pass
}

QuantumBoardState QuantumBoardState::clone() const {
    QuantumBoardState copy(boardSize_);
    copy.b1_         = b1_.clone();
    copy.b2_         = b2_.clone();
    copy.ent_        = ent_;
    copy.sideToMove_ = sideToMove_;
    copy.moveNumber_ = moveNumber_;
    copy.ko_[0]      = ko_[0];
    copy.ko_[1]      = ko_[1];
    copy.hash_       = hash_;
    return copy;
}

std::string QuantumBoardState::toString() const {
    std::ostringstream oss;
    oss << "=== QuantumBoardState (move " << moveNumber_
        << ", " << (sideToMove_ == QColor::BLACK ? "Black" : "White") << " to move) ===\n";
    oss << "--- B1 ---\n" << b1_.toString();
    oss << "--- B2 ---\n" << b2_.toString();
    oss << ent_.toString() << "\n";
    oss << "Hash: 0x" << std::hex << hash_ << std::dec << "\n";
    if (ko_[0] != QGO_INVALID_POS)
        oss << "Ko on B1 at " << ko_[0] << "\n";
    if (ko_[1] != QGO_INVALID_POS)
        oss << "Ko on B2 at " << ko_[1] << "\n";
    return oss.str();
}
