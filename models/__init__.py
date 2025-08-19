"""
Advanced Models Module
Regime switching and GARCH models for volatility analysis
"""

try:
    from .heston_advanced import HestonAdvanced
    from .jump_diffusion import JumpDiffusion
except ImportError:
    HestonAdvanced = None
    JumpDiffusion = None

from .regime_switching import MarkovRegimeSwitching
from .garch import GARCHModel, VolatilityBreakpointDetection

__all__ = ['MarkovRegimeSwitching', 'GARCHModel', 'VolatilityBreakpointDetection']

if HestonAdvanced:
    __all__.extend(['HestonAdvanced', 'JumpDiffusion'])
