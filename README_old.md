# Volatility Surface Explorer

A comprehensive tool for modeling and visualizing implied volatility (IV) surfaces across strikes and expirations, featuring advanced Black-Scholes analytics and robust options pricing infrastructure.

## 🚀 Features

### Core Pricing Engine
- **Enhanced Black-Scholes Implementation**
  - Vectorized pricing for calls and puts with comprehensive validation
  - Robust implied volatility calculation (Newton-Raphson + Brent's method)  
  - Extensive input validation and error handling
  - Performance optimizations for bulk calculations

### Greeks Analytics
- **Complete Greeks Suite**: Delta, Gamma, Vega, Theta, Rho
- **Analytical Formulas**: Fast, accurate calculations
- **Vectorized Operations**: Bulk calculations for option chains
- **Edge Case Handling**: Proper treatment of T=0 and extreme parameters

### Data & Visualization
- **Real-time Options Data**: Yahoo Finance API integration
- **3D Volatility Surfaces**: Interactive Plotly visualizations
- **Greeks Heatmaps**: Visual analysis of risk exposures
- **Surface Interpolation**: Bicubic spline fitting

### Dashboard Features
- **Interactive Streamlit Interface**
- **Live Options Chain Analysis**
- **Sensitivity Analysis Tools**
- **Option Value Decomposition** (intrinsic vs time value)

## 🧮 Mathematical Implementation

### Black-Scholes Formula
```
Call: C = S₀N(d₁) - Ke⁻ʳᵀN(d₂)
Put:  P = Ke⁻ʳᵀN(-d₂) - S₀N(-d₁)

where:
d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T
```

### Greeks Implementation
- **Delta**: ∂V/∂S (price sensitivity)
- **Gamma**: ∂²V/∂S² (delta sensitivity) 
- **Vega**: ∂V/∂σ (volatility sensitivity)
- **Theta**: ∂V/∂T (time decay)
- **Rho**: ∂V/∂r (interest rate sensitivity)

### Implied Volatility
- **Newton-Raphson Method**: Fast convergence using Vega
- **Brent's Method**: Robust fallback for difficult cases
- **Vectorized Implementation**: Efficient bulk calculations
- **Convergence Safeguards**: Automatic bounds checking and validation

## 🛠️ Installation & Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run dashboard/app.py
```

### Quick Example
```python
from core.black_scholes import black_scholes_price, implied_volatility
from core.greeks import all_greeks

# Price a call option
price = black_scholes_price(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type='call')

# Calculate all Greeks
greeks = all_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type='call')

# Back out implied volatility
iv = implied_volatility(price=5.99, S=100, K=100, T=0.25, r=0.05, option_type='call')
```

## 📁 Project Structure
```
volatility_surface_explorer/
├── core/                   # Core quantitative models
│   ├── black_scholes.py   # Enhanced BS pricing & IV
│   ├── greeks.py          # Greeks calculations  
│   ├── heston.py          # Heston model (planned)
│   ├── interpolation.py  # Surface interpolation
│   └── surface_model.py  # Advanced surface modeling
├── dashboard/             # Streamlit interface
│   ├── app.py            # Main dashboard
│   └── components.py     # UI components
├── visuals/              # Plotting utilities
│   ├── plot_surface.py   # 3D surface plots
│   └── heatmaps.py       # Greeks heatmaps
├── utils/                # Data & utilities
│   ├── fetch_data.py     # Options data fetching
│   └── arbitrage.py      # Arbitrage detection
├── tests/                # Test suite
│   ├── test_black_scholes.py  # Comprehensive BS tests
│   └── test_smoke.py     # Basic functionality
├── data/                 # Data storage
├── notebooks/            # Analysis notebooks
└── requirements.txt      # Dependencies
```

## 🧪 Testing

The implementation includes comprehensive test coverage:

```bash
# Run all tests
pytest tests/

# Run specific test module  
pytest tests/test_black_scholes.py -v
```

### Test Coverage
- **Pricing Accuracy**: Put-call parity validation
- **Greeks Consistency**: Cross-validation of analytical formulas
- **Implied Volatility**: Round-trip accuracy testing
- **Edge Cases**: T=0, extreme parameters, vectorization
- **Input Validation**: Comprehensive error handling

## 🎯 Roadmap

### Phase 1: Enhanced Modeling ✅
- [x] Production-grade Black-Scholes implementation
- [x] Complete Greeks analytics 
- [x] Robust implied volatility calculation
- [x] Comprehensive test suite

### Phase 2: Advanced Features (Planned)
- [ ] Heston model implementation
- [ ] Advanced surface modeling (Gaussian processes)
- [ ] Arbitrage detection algorithms
- [ ] Time-lapse surface animation
- [ ] Statistical outlier detection (Z-scores, PCA)

### Phase 3: Production Features (Planned)  
- [ ] Multiple data sources (Barchart API)
- [ ] Real-time streaming updates
- [ ] Portfolio-level Greeks aggregation
- [ ] Advanced visualization themes
- [ ] Export/reporting functionality

## 📊 Key Differentiators

1. **Mathematical Rigor**: Analytical Greeks, robust numerics, comprehensive validation
2. **Performance**: Vectorized operations, optimized algorithms
3. **Robustness**: Extensive error handling, edge case coverage
4. **Extensibility**: Modular design, clean interfaces
5. **Testing**: Comprehensive test suite with edge cases
6. **Documentation**: Detailed docstrings, mathematical formulas

## 🔬 Technical Highlights

- **Vectorization**: Full NumPy vectorization for bulk calculations
- **Numerical Stability**: Proper handling of T→0, extreme strikes
- **Error Handling**: Custom exceptions, input validation
- **Method Diversity**: Multiple IV calculation methods for robustness
- **Memory Efficiency**: Optimized array operations
- **Type Safety**: Type hints throughout codebase

---

*This project demonstrates advanced quantitative finance implementation with production-quality code, comprehensive testing, and sophisticated mathematical modeling suitable for professional trading applications.*

