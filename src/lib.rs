use pyo3::prelude::*;

mod swing_predictor;
mod technical_analysis;
mod market_microstructure;
mod regime_detection;
mod volatility_models;
mod risk_metrics;

use swing_predictor::SwingTradingPredictor;
use technical_analysis::TechnicalAnalyzer;
use market_microstructure::MarketMicrostructure;
use regime_detection::RegimeDetector;
use volatility_models::VolatilityModels;
use risk_metrics::RiskCalculator;

/// IVSURF High-Performance Rust Module
/// Ultra-fast mathematical calculations for swing trading predictions
#[pymodule]
fn ivsurf_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<SwingTradingPredictor>()?;
    m.add_class::<TechnicalAnalyzer>()?;
    m.add_class::<MarketMicrostructure>()?;
    m.add_class::<RegimeDetector>()?;
    m.add_class::<VolatilityModels>()?;
    m.add_class::<RiskCalculator>()?;
    Ok(())
}
