#include <cassert>
#include <memory>
#include "models/ShortPut.hpp"
#include "models/Portfolio.hpp"

using namespace hedging;

int main() {
    Portfolio p;
    p.add_position(std::make_unique<ShortPut>(100.0, 5.0), -1.0);
    double payoff = p.payoff(90.0);
    // Short 1 put: premium 5, intrinsic 10 → 5 - 10 = -5, quantity -1 → +5
    assert(payoff > 0.0);
    return 0;
}
