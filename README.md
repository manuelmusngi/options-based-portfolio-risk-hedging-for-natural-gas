#### Options-Based Portfolio Risk Hedging for Natural Gas

This project is an exercise on a research-grade Options Strategies hedging implementation in Henry Hub Natural Gas portfolio. 

>📄 **Research Paper Reference:** Lai, S., Qiu, J., & Tao, Y. (2022). Option-based portfolio risk hedging strategy for gas generator based on mean-variance utility model. *Energy Conversion and Economics*, 3(1), 20–30. DOI: [10.1049/enc2.12036](https://doi.org/10.1049/enc2.12036)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![DOI](https://img.shields.io/badge/DOI-10.1049%2Fenc2.12036-orange.svg)](https://doi.org/10.1049/enc2.12036)
[![Status: Research](https://img.shields.io/badge/Status-Research-purple.svg)]()

---

🌊 Abstract

Natural gas generators face significant operational risks in electricity markets due to price volatility and uncertain demand. This repository implements the **option-based portfolio risk-hedging framework** proposed by Lai et al. (2022), which combines three financial option instruments — **short put**, **long put**, and **short call** — with two energy storage technologies — **Power-to-Gas (P2G)** and **battery** — to maximize the risk-adjusted utility of a gas generator. Optimal portfolio weights are determined via a **mean-variance utility model** (`Max U = E[r] − ½·A·Var[r]`), enabling the generator to tailor its hedging posture to its individual risk-aversion index *A*. 

Simulation results show the portfolio approach consistently outperforms both the unhedged baseline and any single-option strategy in terms of profit and risk reduction.

---

✨ Highlights

| # | Highlight |
|---|-----------|
| ✅ | Novel three-option hedging portfolio (short put + long put + short call) tailored for gas generators |
| ✅ | Dual energy storage integration: P2G and battery act as physical hedging buffers |
| ✅ | Mean-variance utility optimisation with configurable risk-aversion index *A* |
| ✅ | Estimation-invariant design — robust to demand and price forecast errors |
| ✅ | Outperforms traditional bilateral-contract hedging and single-option strategies |
| ✅ | Risk-preference sensitivity analysis: risk-averse → long put; risk-tolerant → short call |

---

🏗️ Project Architecture

gas-generator-option-hedging/\
├── README.md\
├── LICENSE\
├── requirements.txt\
├── setup.py\
├── data/\
│   ├── market_prices.csv\
│   ├── gas_costs.csv\
│   └── scenario_params.json\
├── src/\
│   ├── options/\
│   │   ├── [init.py](https://github.com/manuelmusngi/options-based-portfolio-risk-hedging-for-natural-gas/blob/main/src/options/__init__.py)\
│   │   ├── [short_put.py](https://github.com/manuelmusngi/options-based-portfolio-risk-hedging-for-natural-gas/blob/main/src/options/short_put.py)   # Short put payoff, premium, constraint models\
│   │   ├── [long_put.py](https://github.com/manuelmusngi/options-based-portfolio-risk-hedging-for-natural-gas/blob/main/src/options/long_put.py)      # Long put payoff, transfer mechanism models\
│   │   └── [short_call.py](https://github.com/manuelmusngi/options-based-portfolio-risk-hedging-for-natural-gas/blob/main/src/options/short_call.py)  # Short call payoff and exercise logic\
│   ├── storage/\
│   │   ├── p2g.py               # Power-to-Gas charging/discharging model\
│   │   └── battery.py           # Battery SOC dynamics and constraints\
│   ├── portfolio/\
│   │   ├── [mean_variance.py](https://github.com/manuelmusngi/options-based-portfolio-risk-hedging-for-natural-gas/blob/main/src/portfolio/mean_variance.py)     # Mean-variance utility: E[r] - 0.5·A·Var[r]\
│   │   ├── optimiser.py # QP weight optimisation\
│   │   └── risk_metrics.py      # CVaR, Sharpe ratio, return distribution\
│   └── utils/\
│       ├── scenario_gen.py      # Scenario generation (price + demand)\
│       └── plotting.py          # Efficient frontier and payoff profile plots\
│
├── notebooks/\
│   ├── 01_data_exploration.ipynb\
│   ├── 02_option_payoffs.ipynb\
│   ├── 03_storage_simulation.ipynb\
│   └── 04_portfolio_optimisation.ipynb\
│
├── tests/\
│   ├── test_options.py\
│   ├── test_storage.py\
│   └── test_portfolio.py\
│
└── diagrams/\
    ├── risk_flow_diagram.svg        # Research-grade risk-flow flowchart\
    ├── portfolio_infographic.svg    # Stakeholder-facing portfolio infographic\
    ├── risk_flow_diagram.png\
    └── portfolio_infographic.png\

---

☑️ Assumptions

1. **Time resolution:** 30-minute slots (48/day)
2. **Strike price:** Uniform across options for baseline — extend if paper specifies instrument-level strikes
3. **Scenario generation:** 1,000 Monte Carlo scenarios unless paper specifies otherwise
4. **P2G efficiency:** 60%; battery round-trip: 92% — adjust from paper Table 1
5. **No transaction costs** beyond explicit premiums are modelled
6. **Risk-free rate:** Assumed zero

---

📄 License

MIT — see [LICENSE](LICENSE). Not affiliated with or endorsed by the original authors.
