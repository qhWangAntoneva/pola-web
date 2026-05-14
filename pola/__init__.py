"""
pola: Python package for calculating critical bandwidth for bimodal distributions

This package implements algorithms to detect the critical bandwidth in kernel density
estimation, which is the smallest bandwidth where the density estimate remains unimodal.
"""

from .bandwidth import (
    BimodalDecomposition,
    Component,
    critical_bandwidth,
    detect_components,
    find_trough,
    gaussian_kde,
    silverman_bandwidth,
)
from .bootstrap import BootstrapResult, bootstrap_critical_bandwidth

__version__ = "0.0.3"
__all__ = [
    "silverman_bandwidth",
    "critical_bandwidth",
    "gaussian_kde",
    "find_trough",
    "detect_components",
    "Component",
    "BimodalDecomposition",
    "bootstrap_critical_bandwidth",
    "BootstrapResult",
]
