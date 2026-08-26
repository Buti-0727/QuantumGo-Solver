cmake_minimum_required(VERSION 3.10)
project(QuantumGoSolver CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O0 -g")

# ── Paths ────────────────────────────────────────────────────────────────────
set(CGI_DIR  "${CMAKE_SOURCE_DIR}/../study-LD-RZ-solver/CGI")
set(MCTPS_DIR "${CMAKE_SOURCE_DIR}/../study-LD-RZ-solver/MCTPS")

# ── Source files ─────────────────────────────────────────────────────────────
set(QGO_SRCS
    src/SingleBoard.cpp
    src/EntanglementTable.cpp
    src/QuantumBoardState.cpp
    src/QuantumHash.cpp
    src/QuantumMoveGen.cpp
    src/QuantumCapture.cpp
    src/QuantumUndo.cpp
    src/QuantumTarget.cpp
    src/QuantumRZone.cpp
    src/QuantumSearch.cpp
    src/QuantumLDSolver.cpp
    src/QuantumSgfParser.cpp
)

# ── Library ───────────────────────────────────────────────────────────────────
add_library(qgo_lib STATIC ${QGO_SRCS})
target_include_directories(qgo_lib PUBLIC src)

# ── Main solver executable ────────────────────────────────────────────────────
add_executable(qgo_solver main.cpp)
target_link_libraries(qgo_solver qgo_lib)

# ── Tests ─────────────────────────────────────────────────────────────────────
add_subdirectory(tests)
