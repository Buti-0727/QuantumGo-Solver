// ============================================================================
// QuantumSgfParser.cpp
// ============================================================================
#include "QuantumSgfParser.h"
#include <fstream>
#include <sstream>
#include <regex>
#include <iostream>

int QuantumSgfParser::sgfCoordToPos(const std::string& s, int boardSize) {
    if (s.empty() || (s == "tt" && boardSize <= 19)) return QGO_INVALID_POS; // Pass
    if (s.length() < 2) return QGO_INVALID_POS;
    int x = s[0] - 'a';
    int y = (boardSize - 1) - (s[1] - 'a'); // SGF 'a' at top, 0-index at bottom
    if (x < 0 || x >= boardSize || y < 0 || y >= boardSize) return QGO_INVALID_POS;
    return y * boardSize + x;
}

std::string QuantumSgfParser::posToSgfCoord(int pos, int boardSize) {
    if (pos == QGO_INVALID_POS) return "";
    int x = pos % boardSize;
    int y = pos / boardSize;
    char cx = (char)('a' + x);
    char cy = (char)('a' + ((boardSize - 1) - y));
    return std::string(1, cx) + std::string(1, cy);
}

bool QuantumSgfParser::parseString(const std::string& content, QuantumGameRecord& record) {
    record = QuantumGameRecord();

    // Board size
    std::regex szRegex(R"(SZ\[(\d+)\])");
    std::smatch match;
    if (std::regex_search(content, match, szRegex)) {
        record.boardSize = std::stoi(match[1].str());
    }

    // Komi
    std::regex kmRegex(R"(KM\[([0-9.]+)\])");
    if (std::regex_search(content, match, kmRegex)) {
        record.komi = std::stof(match[1].str());
    }

    // Result
    std::regex reRegex(R"(RE\[([^\]]*)\])");
    if (std::regex_search(content, match, reRegex)) {
        record.result = match[1].str();
    }

    // Parse moves: ;([BW])\[([a-z]*)\](?:C\[([^\]]*)\])?
    std::regex moveRegex(R"(;([BW])\[([a-z]*)\](?:\s*C\[([^\]]*)\])?)");
    auto words_begin = std::sregex_iterator(content.begin(), content.end(), moveRegex);
    auto words_end = std::sregex_iterator();

    for (std::sregex_iterator i = words_begin; i != words_end; ++i) {
        std::smatch m = *i;
        SgfNode node;
        node.color = (m[1].str() == "B") ? QColor::BLACK : QColor::WHITE;
        std::string coord = m[2].str();
        node.pos = sgfCoordToPos(coord, record.boardSize);
        if (m.size() > 3) node.comment = m[3].str();
        record.moves.push_back(node);
    }

    return !record.moves.empty();
}

bool QuantumSgfParser::parseFile(const std::string& filePath, QuantumGameRecord& record) {
    std::ifstream ifs(filePath);
    if (!ifs.is_open()) return false;
    std::stringstream buffer;
    buffer << ifs.rdbuf();
    return parseString(buffer.str(), record);
}

bool QuantumSgfParser::replayToPly(const QuantumGameRecord& record, int plyCount, QuantumBoardState& state) {
    state.reset();
    state.boardSize_ = record.boardSize;

    int totalMoves = static_cast<int>(record.moves.size());
    int limit = (plyCount < 0 || plyCount > totalMoves) ? totalMoves : plyCount;

    // Opening Moves (1 & 2): check if coordinates exist in comments or moves
    // Standard QuantumGo SGF:
    // Move 1: B[xy] placed on both or entangled
    // Move 2: W[xy] placed on both or entangled
    // Subsequent moves: synchronized common moves
    for (int i = 0; i < limit; ++i) {
        const auto& node = record.moves[i];
        QuantumUndoRecord rec;

        if (i < 2) {
            // Opening move: place on both boards and link as entangled pair if occupied
            if (node.pos != QGO_INVALID_POS) {
                state.board(BoardId::B1).placeStone(node.pos, node.color);
                state.board(BoardId::B2).placeStone(node.pos, node.color);
                state.ent().link(node.pos, node.pos);
                state.xorStone(BoardId::B1, node.pos, node.color);
                state.xorStone(BoardId::B2, node.pos, node.color);
                state.xorEntangle(node.pos, node.pos);
            }
            state.moveNumber_++;
            state.sideToMove_ = opponent(state.sideToMove_);
        } else {
            // Common move
            QuantumMove mv = (node.pos == QGO_INVALID_POS) ?
                QuantumMove::pass(node.color) :
                QuantumMove::common(node.color, node.pos);

            QuantumCapture::applyMove(state, mv, rec);
        }
    }

    return true;
}
