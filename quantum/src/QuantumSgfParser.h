#pragma once
// ============================================================================
// QuantumSgfParser.h  —  Parser & Replayer for QuantumGo SGF games
//
// Parses SGF files produced by QuantumGo self-play engines:
//   - Header: SZ, KM, RE
//   - Move 1 (Black): entangled pair (or comment notation)
//   - Move 2 (White): entangled pair (BlackQ:..., WhiteQ:...)
//   - Move 3+: synchronized single-coordinate moves B[xy], W[xy], B[], W[]
// ============================================================================

#include "QuantumTypes.h"
#include "QuantumBoardState.h"
#include "QuantumCapture.h"
#include <string>
#include <vector>

struct SgfNode {
    QColor color = QColor::EMPTY;
    int pos = QGO_INVALID_POS; // -1 for PASS
    std::string comment;
};

struct QuantumGameRecord {
    int boardSize = 9;
    float komi = 7.5f;
    std::string result;
    std::vector<SgfNode> moves;
};

class QuantumSgfParser {
public:
    // Parse an SGF string or file into a QuantumGameRecord
    static bool parseString(const std::string& sgfContent, QuantumGameRecord& record);
    static bool parseFile(const std::string& filePath, QuantumGameRecord& record);

    // Replay game up to `plyCount` moves into a QuantumBoardState
    static bool replayToPly(const QuantumGameRecord& record, int plyCount, QuantumBoardState& state);

    // Helper: convert SGF coordinate string (e.g. "ef" -> pos on board)
    static int sgfCoordToPos(const std::string& s, int boardSize);
    static std::string posToSgfCoord(int pos, int boardSize);
};
