// ============================================================================
// test_main.cpp  —  Test runner entry point
// ============================================================================
#include "test_framework.h"
#include <iostream>
#include <vector>

struct TestEntry {
    std::string name;
    std::function<void()> fn;
};

static std::vector<TestEntry>& registry() {
    static std::vector<TestEntry> r;
    return r;
}

void registerTest(const std::string& name, std::function<void()> fn) {
    registry().push_back({name, fn});
}

void CHECK(bool cond, const std::string& msg) {
    if (!cond) throw std::runtime_error(msg);
}

int main() {
    int passed = 0, failed = 0;
    for (auto& t : registry()) {
        std::cout << "[TEST] " << t.name << " ... ";
        try {
            t.fn();
            std::cout << "PASS\n";
            ++passed;
        } catch (std::exception& e) {
            std::cout << "FAIL (" << e.what() << ")\n";
            ++failed;
        }
    }
    std::cout << "\n=== " << passed << " passed, " << failed << " failed ===\n";
    return failed > 0 ? 1 : 0;
}
