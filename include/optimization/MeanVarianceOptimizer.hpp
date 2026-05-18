#pragma once

#include <vector>

namespace hedging {

class MeanVarianceOptimizer {
public:
    // μ: expected returns (size n)
    // cov: covariance matrix (row-major, n*n)
    // gamma: risk aversion
    // returns weights w (size n), sum(w) = 1
    [[nodiscard]] std::vector<double>
    solve(const std::vector<double>& mu,
          const std::vector<double>& cov,
          double gamma) const;
};

} // namespace hedging
