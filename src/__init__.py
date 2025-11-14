"""
NBA Predictor - Minimal package for NBA prediction experiments.
"""

__version__ = "0.1.0"

from .data_collector import NBADataCollector
from .analyzer import NBAAnalyzer

__all__ = ["NBADataCollector", "NBAAnalyzer"]
