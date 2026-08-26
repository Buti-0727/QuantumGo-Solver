// ============================================================================
// EntanglementTable.cpp
// ============================================================================
#include "EntanglementTable.h"
#include "QuantumHash.h"   // forward — defined later; Zobrist keys live there
#include <sstream>
#include <stdexcept>

EntanglementTable::EntanglementTable(int boardSize)
    : boardSize_(boardSize)
{
    reset();
}

void EntanglementTable::reset() {
    for (int i = 0; i < boardSize_ * boardSize_; ++i) {
        partner_[0][i] = INVALID;
        partner_[1][i] = INVALID;
    }
}

void EntanglementTable::link(int b1pos, int b2pos) {
    assert(b1pos >= 0 && b1pos < boardSize_ * boardSize_);
    assert(b2pos >= 0 && b2pos < boardSize_ * boardSize_);
    // Must not already be entangled
    assert(partner_[0][b1pos] == INVALID && "B1 stone already entangled");
    assert(partner_[1][b2pos] == INVALID && "B2 stone already entangled");

    partner_[0][b1pos] = b2pos;
    partner_[1][b2pos] = b1pos;
}

void EntanglementTable::unlink(BoardId b, int pos) {
    int bi = static_cast<int>(b);
    int oi = 1 - bi;
    int partner = partner_[bi][pos];
    if (partner == INVALID) return;   // nothing to do

    partner_[bi][pos]      = INVALID;
    partner_[oi][partner]  = INVALID;
}

bool EntanglementTable::hasPartner(BoardId b, int pos) const {
    return partner_[static_cast<int>(b)][pos] != INVALID;
}

int EntanglementTable::partnerOf(BoardId b, int pos) const {
    return partner_[static_cast<int>(b)][pos];
}

EntanglementTable::Snapshot EntanglementTable::snapshot() const {
    Snapshot s;
    std::memcpy(s.p0, partner_[0], sizeof(int) * QGO_MAX_GRIDS);
    std::memcpy(s.p1, partner_[1], sizeof(int) * QGO_MAX_GRIDS);
    return s;
}

void EntanglementTable::restore(const Snapshot& s) {
    std::memcpy(partner_[0], s.p0, sizeof(int) * QGO_MAX_GRIDS);
    std::memcpy(partner_[1], s.p1, sizeof(int) * QGO_MAX_GRIDS);
}

ZKey EntanglementTable::zobristHash() const {
    ZKey h = 0;
    int n = boardSize_ * boardSize_;
    for (int p = 0; p < n; ++p) {
        int q = partner_[0][p];
        if (q != INVALID) {
            h ^= QuantumHash::entangleKey(p, q);
        }
    }
    return h;
}

std::string EntanglementTable::toString() const {
    std::ostringstream oss;
    oss << "EntanglementTable {\n";
    int n = boardSize_ * boardSize_;
    for (int p = 0; p < n; ++p) {
        int q = partner_[0][p];
        if (q != INVALID) {
            int px = p % boardSize_, py = p / boardSize_;
            int qx = q % boardSize_, qy = q / boardSize_;
            oss << "  B1[" << (char)('A'+px) << (py+1) << "]"
                << " <-> B2[" << (char)('A'+qx) << (qy+1) << "]\n";
        }
    }
    oss << "}";
    return oss.str();
}
