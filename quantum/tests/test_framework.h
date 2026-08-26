// ============================================================================
// test_framework.h  —  Shared declarations for tests
// ============================================================================
#pragma once
#include <string>
#include <functional>
#include <stdexcept>

void registerTest(const std::string& name, std::function<void()> fn);
void CHECK(bool cond, const std::string& msg);
