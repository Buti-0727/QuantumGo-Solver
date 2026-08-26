cmake_minimum_required(VERSION 3.10)
project(QGoTests CXX)

set(CMAKE_CXX_STANDARD 17)

set(TEST_SRCS
    test_main.cpp
    test_entanglement.cpp
    test_rules.cpp
    test_capture.cpp
    test_state.cpp
    test_ld.cpp
    test_rzone.cpp
)

add_executable(qgo_tests ${TEST_SRCS})
target_link_libraries(qgo_tests qgo_lib)
target_include_directories(qgo_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}
)
