"""
Monte Carlo Options Simulation
=============================

Advanced Monte Carlo simulation engine for options pricing and risk analysis.

This package provides:
- Multi-asset Monte Carlo simulation with correlation
- Variance reduction techniques (antithetic variates, control variates, stratified sampling)
- Exotic options pricing (barrier, Asian, lookback, rainbow)
- Real-time Greeks calculation
- Path-dependent option valuation
- Risk metrics and scenario analysis

Author: Volatility Surface Explorer
Date: August 2025
Version: 1.0.0
"""

# Import main classes - these will be available when modules are created
__all__ = [
    'MonteCarloEngine',
    'PathGenerator', 
    'VarianceReductionEngine',
    'ExoticOptionsEngine',
    'GreeksCalculator',
    'RiskAnalyzer',
    'BarrierOption',
    'AsianOption',
    'LookbackOption',
    'RainbowOption',
    'DigitalOption',
    'AmericanOption',
    'CorrelationEngine',
    'CholeskySampler',
    'CopulaSampler'
]

__version__ = "1.0.0"
