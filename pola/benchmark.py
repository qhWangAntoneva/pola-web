"""
Benchmark dataset for critical bandwidth validation.

Each BenchmarkCase defines a Gaussian mixture with a known critical bandwidth,
established by high-precision binary search (tol=1e-8, max_iter=500).
"""

from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np


@dataclass
class BenchmarkCase:
    """A benchmark case with known critical bandwidth."""

    name: str
    description: str
    generator: Callable[[int], np.ndarray]
    h_crit_expected: float
    h_crit_tolerance: float = 0.05
    reference_method: str = "binary"


def _mixture(seed: int, components: list) -> np.ndarray:
    """Generate a Gaussian mixture sample.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.
    components : list of (mean, std, n_samples)
        Each tuple specifies a Gaussian component.

    Returns
    -------
    np.ndarray
        Concatenated samples from all components.
    """
    rng = np.random.default_rng(seed)
    samples = [rng.normal(mu, sigma, n) for mu, sigma, n in components]
    return np.concatenate(samples)


# --- Benchmark cases ---

BENCHMARK_CASES: Dict[str, BenchmarkCase] = {
    "well_separated_equal_var": BenchmarkCase(
        name="well_separated_equal_var",
        description=(
            "Two Gaussians: N(-2, 0.3) and N(2, 0.3), 200 points each. "
            "Symmetric, equal variance, well-separated."
        ),
        generator=lambda seed: _mixture(seed, [(-2, 0.3, 200), (2, 0.3, 200)]),
        h_crit_expected=1.86,
        h_crit_tolerance=0.10,
    ),
    "moderate_separation": BenchmarkCase(
        name="moderate_separation",
        description=(
            "Two Gaussians: N(-1, 0.5) and N(1.5, 0.5), 250 points each. "
            "Moderate separation, equal variance."
        ),
        generator=lambda seed: _mixture(seed, [(-1, 0.5, 250), (1.5, 0.5, 250)]),
        h_crit_expected=1.10,
        h_crit_tolerance=0.10,
    ),
    "barely_separated": BenchmarkCase(
        name="barely_separated",
        description=(
            "Two Gaussians: N(-0.5, 0.4) and N(0.5, 0.4), 300 points each. "
            "Barely separated, touching modes."
        ),
        generator=lambda seed: _mixture(seed, [(-0.5, 0.4, 300), (0.5, 0.4, 300)]),
        h_crit_expected=0.28,
        h_crit_tolerance=0.06,
    ),
    "unequal_variance": BenchmarkCase(
        name="unequal_variance",
        description=(
            "Two Gaussians: N(-2, 0.6) and N(2, 0.2), 200 points each. "
            "Left component wider, right tighter."
        ),
        generator=lambda seed: _mixture(seed, [(-2, 0.6, 200), (2, 0.2, 200)]),
        h_crit_expected=1.78,
        h_crit_tolerance=0.15,
    ),
    "unequal_weights": BenchmarkCase(
        name="unequal_weights",
        description=("Two Gaussians: N(-2, 0.3, 100) and N(2, 0.3, 400). Asymmetric sample sizes."),
        generator=lambda seed: _mixture(seed, [(-2, 0.3, 100), (2, 0.3, 400)]),
        h_crit_expected=1.26,
        h_crit_tolerance=0.10,
    ),
    "extreme_separation": BenchmarkCase(
        name="extreme_separation",
        description=(
            "Two Gaussians: N(-5, 0.5) and N(5, 0.5), 200 points each. Very wide separation."
        ),
        generator=lambda seed: _mixture(seed, [(-5, 0.5, 200), (5, 0.5, 200)]),
        h_crit_expected=4.69,
        h_crit_tolerance=0.20,
    ),
    "trimodal": BenchmarkCase(
        name="trimodal",
        description=(
            "Three Gaussians: N(-3, 0.3), N(0, 0.3), N(3, 0.3), 150 each. "
            "Three modes; the two outer peaks determine critical bandwidth."
        ),
        generator=lambda seed: _mixture(seed, [(-3, 0.3, 150), (0, 0.3, 150), (3, 0.3, 150)]),
        h_crit_expected=1.38,
        h_crit_tolerance=0.10,
    ),
}


def get_benchmark_case(name: str) -> BenchmarkCase:
    """Get a benchmark case by name."""
    if name not in BENCHMARK_CASES:
        raise KeyError(f"Unknown benchmark case: {name}. Available: {list(BENCHMARK_CASES.keys())}")
    return BENCHMARK_CASES[name]


def get_all_benchmark_cases() -> List[BenchmarkCase]:
    """Get all benchmark cases."""
    return list(BENCHMARK_CASES.values())
