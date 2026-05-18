#include "optimization/MeanVarianceOptimizer.hpp"
#include <Eigen/Dense>

namespace hedging {

std::vector<double> MeanVarianceOptimizer::solve(
    const std::vector<double>& mu,
    const std::vector<double>& cov,
    double gamma) const
{
    using Eigen::VectorXd;
    using Eigen::MatrixXd;

    size_t n = mu.size();
    VectorXd mu_v(n);
    for (size_t i=0;i<n;i++) mu_v(i)=mu[i];

    MatrixXd Sigma(n,n);
    for (size_t i=0;i<n;i++)
        for (size_t j=0;j<n;j++)
            Sigma(i,j)=cov[i*n+j];

    VectorXd w = (1.0/(2*gamma)) * Sigma.inverse() * mu_v;
    w /= w.sum();

    std::vector<double> out(n);
    for (size_t i=0;i<n;i++) out[i]=w(i);
    return out;
}

}
