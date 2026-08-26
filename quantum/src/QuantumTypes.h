#pragma once
// ============================================================================
// QuantumTypes.h  —  Fundamental types for the QuantumGo L&D Solver
//
// QuantumGo rules (authoritative — Coding Protocol §0.1):
//   B1 and B2 are two PERSISTENT boards that always coexist.
//   Move 1 (Black) and Move 2 (White) are "opening" quantum moves:
//     each selects one coordinate on B1 and one (different) coordinate on B2.
//     Those two stones form an entangled pair.
//   From Move 3 onward, every move is a single coordinate (x,y) played
//     SIMULTANEOUSLY on BOTH B1 and B2.  Illegal on either board → illegal.
//   Captures: local Go rules per board, PLUS if one stone of an entangled
//     pair is captured its partner is immediately removed from the other board.
//     This can cascade recursively until stable.
// ============================================================================

#include <cstdint>
#include <cstring>
#include <string>
#include <cassert>
#include <array>
#include <vector>
#include <ostream>

// ── Board parameters ─────────────────────────────────────────────────────────
inline constexpr int QGO_MAX_BOARD_SIZE = 19;
inline constexpr int QGO_MAX_GRIDS      = QGO_MAX_BOARD_SIZE * QGO_MAX_BOARD_SIZE;
inline constexpr int QGO_INVALID_POS    = -1;

// ── Stone colour ─────────────────────────────────────────────────────────────
enum class QColor : uint8_t {
    EMPTY  = 0,
    BLACK  = 1,
    WHITE  = 2,
    BORDER = 3
};

inline QColor opponent(QColor c) {
    assert(c == QColor::BLACK || c == QColor::WHITE);
    return (c == QColor::BLACK) ? QColor::WHITE : QColor::BLACK;
}

inline char toChar(QColor c) {
    switch (c) {
        case QColor::EMPTY:  return '.';
        case QColor::BLACK:  return 'X';
        case QColor::WHITE:  return 'O';
        default:             return '#';
    }
}

// ── Board identifier ─────────────────────────────────────────────────────────
enum class BoardId : uint8_t { B1 = 0, B2 = 1 };

inline BoardId otherBoard(BoardId b) {
    return (b == BoardId::B1) ? BoardId::B2 : BoardId::B1;
}

// ── Move phase ───────────────────────────────────────────────────────────────
//   OPENING  = Moves 1 and 2 (entangled pair placements)
//   COMMON   = Moves 3+ (synchronized single-coordinate moves)
enum class MovePhase : uint8_t { OPENING = 0, COMMON = 1 };

// ── L&D objective ────────────────────────────────────────────────────────────
enum class LDObjective : uint8_t { KILL = 0, LIVE = 1 };

// ── L&D result ───────────────────────────────────────────────────────────────
enum class LDResult : uint8_t {
    UNKNOWN = 0,
    ALIVE   = 1,
    DEAD    = 2,
    SEKI    = 3,
    KO      = 4
};

inline std::string toString(LDResult r) {
    switch (r) {
        case LDResult::ALIVE:   return "ALIVE";
        case LDResult::DEAD:    return "DEAD";
        case LDResult::SEKI:    return "SEKI";
        case LDResult::KO:      return "KO";
        default:                return "UNKNOWN";
    }
}

// ── Ko rule ──────────────────────────────────────────────────────────────────
enum class KoRule : uint8_t { SIMPLE = 0, SUPERKO_POSITIONAL = 1 };

// ── Position helpers ─────────────────────────────────────────────────────────
struct QPos {
    int x, y;                           // 0-indexed, (0,0) = bottom-left
    int boardSize;

    QPos() : x(-1), y(-1), boardSize(0) {}
    QPos(int x_, int y_, int bs) : x(x_), y(y_), boardSize(bs) {}

    bool valid() const { return x >= 0 && y >= 0 && x < boardSize && y < boardSize; }
    int  toIndex() const { return y * boardSize + x; }
    bool operator==(const QPos& o) const { return x == o.x && y == o.y; }
    bool operator!=(const QPos& o) const { return !(*this == o); }

    static QPos fromIndex(int idx, int bs) {
        return QPos(idx % bs, idx / bs, bs);
    }
    static QPos PASS() { return QPos(-1, -1, 0); }
    bool isPass() const { return x == -1 && y == -1; }
};

// ── Neighbours (up/down/left/right) ─────────────────────────────────────────
inline std::array<int,4> neighbours(int pos, int bs) {
    int x = pos % bs, y = pos / bs;
    std::array<int,4> nb{QGO_INVALID_POS, QGO_INVALID_POS, QGO_INVALID_POS, QGO_INVALID_POS};
    if (x > 0)      nb[0] = pos - 1;
    if (x < bs-1)   nb[1] = pos + 1;
    if (y > 0)      nb[2] = pos - bs;
    if (y < bs-1)   nb[3] = pos + bs;
    return nb;
}

// ── Zobrist key type ─────────────────────────────────────────────────────────
using ZKey = uint64_t;
