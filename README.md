# Option-Based Portfolio Risk Hedging for Gas Generators

This project is an exercise in implementing a research-grade Options Strategies in Henry Hub Natural Gas that may be used in hedging. Two implementations are considered, one using Python-based while the other in C++ based structures.

> **Paper:** Lai, S., Qiu, J., & Tao, Y. (2022). Option-based portfolio risk hedging strategy for gas generator based on mean-variance utility model. *Energy Conversion and Economics*, 3(1), 20–30. DOI: [10.1049/enc2.12036](https://doi.org/10.1049/enc2.12036)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![DOI](https://img.shields.io/badge/DOI-10.1049%2Fenc2.12036-orange.svg)](https://doi.org/10.1049/enc2.12036)
[![Status: Research](https://img.shields.io/badge/Status-Research-purple.svg)]()

---

## Abstract

Natural gas generators face significant operational risks in electricity markets due to price volatility and uncertain demand. This repository implements the **option-based portfolio risk-hedging framework** proposed by Lai et al. (2022), which combines three financial option instruments — **short put**, **long put**, and **short call** — with two energy storage technologies — **Power-to-Gas (P2G)** and **battery** — to maximise the risk-adjusted utility of a gas generator. Optimal portfolio weights are determined via a **mean-variance utility model** (`Max U = E[r] − ½·A·Var[r]`), enabling the generator to tailor its hedging posture to its individual risk-aversion index *A*. Simulation results show the portfolio approach consistently outperforms both the unhedged baseline and any single-option strategy in terms of profit and risk reduction.

---

## Highlights

| # | Highlight |
|---|-----------|
| ✅ | Novel three-option hedging portfolio (short put + long put + short call) tailored for gas generators |
| ✅ | Dual energy storage integration: P2G and battery act as physical hedging buffers |
| ✅ | Mean-variance utility optimisation with configurable risk-aversion index *A* |
| ✅ | Estimation-invariant design — robust to demand and price forecast errors |
| ✅ | Outperforms traditional bilateral-contract hedging and single-option strategies |
| ✅ | Risk-preference sensitivity analysis: risk-averse → long put; risk-tolerant → short call |

---

## Project Architecture

```
gas-generator-option-hedging/
│
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
│
├── data/
│   ├── market_prices.csv
│   ├── gas_costs.csv
│   └── scenario_params.json
│
├── src/
│   ├── options/
│   │   ├── short_put.py         # Short put payoff, premium, constraint models
│   │   ├── long_put.py          # Long put payoff, transfer mechanism models
│   │   └── short_call.py        # Short call payoff and exercise logic
│   ├── storage/
│   │   ├── p2g.py               # Power-to-Gas charging/discharging model
│   │   └── battery.py           # Battery SOC dynamics and constraints
│   ├── portfolio/
│   │   ├── mean_variance.py     # Mean-variance utility: E[r] - 0.5·A·Var[r]
│   │   ├── optimiser.py         # QP weight optimisation
│   │   └── risk_metrics.py      # CVaR, Sharpe ratio, return distribution
│   └── utils/
│       ├── scenario_gen.py      # Scenario generation (price + demand)
│       └── plotting.py          # Efficient frontier and payoff profile plots
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_option_payoffs.ipynb
│   ├── 03_storage_simulation.ipynb
│   └── 04_portfolio_optimisation.ipynb
│
├── tests/
│   ├── test_options.py
│   ├── test_storage.py
│   └── test_portfolio.py
│
└── diagrams/
    ├── risk_flow_diagram.svg        # Research-grade risk-flow flowchart
    ├── portfolio_infographic.svg    # Stakeholder-facing portfolio infographic
    ├── risk_flow_diagram.png
    └── portfolio_infographic.png
```

---

## Installation

```bash
git clone https://github.com/your-org/gas-generator-option-hedging.git
cd gas-generator-option-hedging
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

**Key dependencies:**
```
numpy>=1.23 · scipy>=1.9 · pandas>=1.5 · cvxpy>=1.3 · matplotlib>=3.6 · seaborn>=0.12 · jupyter>=1.0 · pytest>=7.2
```

---

## Usage

```python
from src.options.short_put import ShortPut
from src.options.long_put import LongPut
from src.options.short_call import ShortCall
from src.storage.p2g import PowerToGas
from src.storage.battery import Battery
from src.portfolio.mean_variance import MeanVarianceOptimiser

short_put  = ShortPut(strike=80.0,  premium=5.0)
long_put   = LongPut(strike=80.0,   premium=4.5)
short_call = ShortCall(strike=80.0, premium=6.0)
p2g        = PowerToGas(capacity_mwh=50, efficiency=0.60)
battery    = Battery(capacity_mwh=30, charge_rate=10, efficiency=0.92)

optimiser = MeanVarianceOptimiser(
    instruments=[short_put, long_put, short_call, p2g, battery],
    risk_aversion=3, n_scenarios=1000, random_seed=42
)
result = optimiser.solve()
print(result.weights)
```

---

## Model Overview

```
Maximise:   U = E[r_portfolio(T)] − (1/2) · A · Var[r_portfolio(T)]

Subject to: Σ wᵢ = 1          (weights sum to 1)
            0 ≤ wᵢ ≤ 1        (no short-selling of instruments)
            SOC constraints     (battery state-of-charge bounds)
            P2G energy balance  (gas input = electrical output / η_P2G)
            Option exercise conditions (price vs. strike price)
```

---

## Assumptions

1. **Time resolution:** 30-minute slots (48/day)
2. **Strike price:** Uniform across options for baseline — extend if paper specifies instrument-level strikes
3. **Scenario generation:** 1,000 Monte Carlo scenarios unless paper specifies otherwise
4. **P2G efficiency:** 60%; battery round-trip: 92% — adjust from paper Table 1
5. **No transaction costs** beyond explicit premiums are modelled
6. **Risk-free rate:** Assumed zero

---

## Project Architecture in C++

```

OptionHedgingSystem/
├── CMakeLists.txt
├── cmake/
│   └── modules/
├── include/
│   ├── core/
│   ├── models/
│   ├── storage/
│   ├── optimization/
│   ├── simulation/
│   └── utils/
├── src/
│   ├── core/
│   ├── models/
│   ├── storage/
│   ├── optimization/
│   ├── simulation/
│   └── utils/
├── configs/
├── data/
├── tests/
└── examples/

```

## Citation

```bibtex
@article{lai2022option,
  title   = {Option-based portfolio risk hedging strategy for gas generator
             based on mean-variance utility model},
  author  = {Lai, Shuying and Qiu, Jing and Tao, Yuechuan},
  journal = {Energy Conversion and Economics},
  volume  = {3}, number = {1}, pages = {20--30}, year = {2022},
  doi     = {10.1049/enc2.12036}
}
```

## License

MIT — see [LICENSE](LICENSE). Not affiliated with or endorsed by the original authors.
