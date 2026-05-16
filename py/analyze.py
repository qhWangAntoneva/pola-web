"""
Pyodide-compatible wrappers for pola computation functions.

These functions are designed to be called from JavaScript via Pyodide's
pyodide.runPython() or by importing this module and calling functions
directly from JS via the pyodide.globals mechanism.

All return values use only JSON-serializable Python types
(dict, list, float, int, bool, str).
"""

import numpy as np

from pola import (
    bootstrap_critical_bandwidth,
    critical_bandwidth,
    detect_components,
    dip_test,
    find_trough,
    silverman_bandwidth,
)

# bimodality_strength and find_modes may not be in all pola versions
# Fall through to None if missing (callers should handle)
try:
    from pola import bimodality_strength
except ImportError:
    bimodality_strength = None
try:
    from pola import find_modes
except ImportError:
    find_modes = None
from pola.bandwidth import _validate_input
from pola.benchmark import BENCHMARK_CASES, get_benchmark_case


def _to_js(val):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.bool_):
        return bool(val)
    return val


def _convert_result(d):
    """Recursively convert all values in a dict to JSON-safe types."""
    if isinstance(d, dict):
        return {k: _convert_result(v) for k, v in d.items()}
    elif isinstance(d, (list, tuple)):
        return [_convert_result(v) for v in d]
    return _to_js(d)


def analyze_critical_bandwidth(
    data_list,
    kernel="gaussian",
    method="auto",
    tol=1e-6,
    max_iter=100,
):
    """
    Compute critical bandwidth from a list of data points.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    kernel : str, optional
        Kernel function ("gaussian", "epanechnikov", "uniform", "triangular").
    method : str, optional
        Search method ("auto", "binary", "brent").
    tol : float, optional
        Convergence tolerance.
    max_iter : int, optional
        Maximum iterations.

    Returns
    -------
    dict
        {"h_crit": float, "success": bool, "silverman_bandwidth": float, "n_points": int}
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)
    h_silver = float(silverman_bandwidth(x))
    h_crit, success = critical_bandwidth(
        x, tol=tol, max_iter=max_iter, method=method, kernel=kernel
    )
    return _convert_result(
        {
            "h_crit": h_crit,
            "success": success,
            "silverman_bandwidth": h_silver,
            "n_points": len(x),
            "kernel": kernel,
            "method": method,
        }
    )


def analyze_full(data_list, kernel="gaussian", h_factor=0.85, method="auto"):
    """
    Full analysis: critical bandwidth + trough + component decomposition.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    kernel : str, optional
        Kernel function.
    h_factor : float, optional
        Multiplier on h_crit for analysis bandwidth.
    method : str, optional
        Search method.

    Returns
    -------
    dict
        Analysis results with h_crit, trough, dip_ratio, components.
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)

    h_crit, success = critical_bandwidth(x, kernel=kernel, method=method)
    h_analysis = h_crit * h_factor
    trough = find_trough(x, h_analysis, kernel=kernel)

    result = {
        "h_crit": float(h_crit),
        "success": bool(success),
        "trough": float(trough) if trough is not None else None,
        "dip_ratio": None,
        "components": None,
    }

    try:
        decomp = detect_components(x, h_factor=h_factor, kernel=kernel)
        result["dip_ratio"] = float(decomp.dip_ratio)
        result["components"] = {
            "component1": {
                "mean": float(decomp.component1.mean),
                "std": float(decomp.component1.std),
                "weight": float(decomp.component1.weight),
            },
            "component2": {
                "mean": float(decomp.component2.mean),
                "std": float(decomp.component2.std),
                "weight": float(decomp.component2.weight),
            },
        }
        result["separation_point"] = float(decomp.separation_point)
    except ValueError:
        pass  # not sufficiently bimodal

    return result


def run_bootstrap(data_list, n_resamples=99, alpha=0.05, random_state=42, kernel="gaussian"):
    """
    Bootstrap confidence interval for critical bandwidth.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    n_resamples : int, optional
        Number of bootstrap resamples (max 999).
    alpha : float, optional
        Significance level (default 0.05 = 95% CI).
    random_state : int, optional
        Random seed.
    kernel : str, optional
        Kernel function.

    Returns
    -------
    dict
        Bootstrap results with CI bounds, SE, and distribution.
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)

    result = bootstrap_critical_bandwidth(
        x,
        n_resamples=min(n_resamples, 999),
        alpha=alpha,
        random_state=random_state,
        kernel=kernel,
    )

    return _convert_result(
        {
            "h_crit": result.h_crit,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "standard_error": result.standard_error,
            "distribution": result.distribution,
            "n_resamples": result.n_resamples,
            "confidence_level": result.confidence_level,
            "n_failed": result.n_failed,
        }
    )


def list_benchmarks():
    """
    List all available benchmark cases.

    Returns
    -------
    list[dict]
        Each with name, description, h_crit_expected, h_crit_tolerance.
    """
    cases = []
    for case in BENCHMARK_CASES.values():
        cases.append(
            {
                "name": case.name,
                "description": case.description,
                "h_crit_expected": float(case.h_crit_expected),
                "h_crit_tolerance": float(case.h_crit_tolerance),
            }
        )
    return cases


def analyze_benchmark(name, seed=42, kernel="gaussian", h_factor=0.85):
    """
    Generate and analyze a benchmark case.

    Parameters
    ----------
    name : str
        Benchmark case name.
    seed : int, optional
        Random seed.
    kernel : str, optional
        Kernel function.
    h_factor : float, optional
        Multiplier on h_crit.

    Returns
    -------
    dict
        Benchmark analysis including expected vs actual h_crit.
    """
    case = get_benchmark_case(name)
    x = case.generator(seed)

    h_crit, success = critical_bandwidth(x, kernel=kernel)
    trough = find_trough(x, h_crit * h_factor, kernel=kernel)

    result = {
        "name": name,
        "description": case.description,
        "h_crit_expected": float(case.h_crit_expected),
        "h_crit_tolerance": float(case.h_crit_tolerance),
        "h_crit": float(h_crit),
        "h_crit_error": float(h_crit - case.h_crit_expected),
        "success": bool(success),
        "n_points": len(x),
        "trough": float(trough) if trough is not None else None,
        "x": x.tolist(),
    }

    try:
        decomp = detect_components(x, h_factor=h_factor, kernel=kernel)
        result["dip_ratio"] = float(decomp.dip_ratio)
        result["components"] = {
            "component1": {
                "mean": float(decomp.component1.mean),
                "std": float(decomp.component1.std),
                "weight": float(decomp.component1.weight),
            },
            "component2": {
                "mean": float(decomp.component2.mean),
                "std": float(decomp.component2.std),
                "weight": float(decomp.component2.weight),
            },
        }
    except ValueError:
        pass

    return result


def find_modes_analysis(
    data_list,
    h=None,
    grid_points=None,
    prominence=0.01,
    kernel="gaussian",
):
    """
    Find modes (peaks) in the KDE of a dataset.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    h : float, optional
        Bandwidth. If None, uses Silverman's rule.
    grid_points : int, optional
        Number of grid points for KDE evaluation.
    prominence : float, optional
        Minimum prominence for peak detection.
    kernel : str, optional
        Kernel function.

    Returns
    -------
    dict
        ``{"n_modes": int, "modes": list[dict], "bandwidth": float, "grid_points": int}``
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)

    if find_modes is None:
        return {"error": "find_modes not available in this pola version"}

    if h is None:
        h = float(silverman_bandwidth(x))

    result = find_modes(
        x, h=h, grid_points=grid_points, prominence=prominence, kernel=kernel
    )

    return _convert_result(
        {
            "n_modes": result.n_modes,
            "modes": [
                {
                    "position": m.position,
                    "height": m.height,
                    "width": m.width,
                    "prominence": m.prominence,
                    "left_base": m.left_base,
                    "right_base": m.right_base,
                }
                for m in result.modes
            ],
            "bandwidth": result.bandwidth,
            "grid_points": result.grid_points,
        }
    )


def bimodality_strength_analysis(
    data_list,
    h_factor=0.85,
    kernel="gaussian",
):
    """
    Assess bimodality strength using dip ratio and mode count.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    h_factor : float, optional
        Multiplier on Silverman bandwidth.
    kernel : str, optional
        Kernel function.

    Returns
    -------
    dict
        ``{"dip_ratio": float, "h_crit_ratio": float, "n_modes": int,
        "strength": str, "strength_score": float}``
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)

    if bimodality_strength is None:
        return {"error": "bimodality_strength not available in this pola version"}

    result = bimodality_strength(x, h_factor=h_factor, kernel=kernel)

    return _convert_result(
        {
            "dip_ratio": result.dip_ratio,
            "h_crit_ratio": result.h_crit_ratio,
            "n_modes": result.n_modes,
            "strength": result.strength,
            "strength_score": result.strength_score,
        }
    )


def dip_test_analysis(
    data_list,
    n_boot=999,
    random_state=None,
):
    """
    Run Hartigan's dip test for unimodality.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    n_boot : int, optional
        Number of bootstrap resamples.
    random_state : int, optional
        Random seed.

    Returns
    -------
    dict
        ``{"dip": float, "p_value": float, "n_boot": int, "n_extreme": int,
           "capped": bool, "subsampled": bool, "n_original": int}``
    """
    x = np.array(data_list, dtype=float)
    _validate_input(x)
    n_original = len(x)
    capped = False
    subsampled = False

    # Subsample large datasets for WASM performance (O(n²) algorithm)
    if len(x) > 100:
        rng = np.random.default_rng(random_state)
        x = rng.choice(x, 100, replace=False)
        subsampled = True
        if random_state is not None:
            random_state = random_state + 1  # shift for bootstrap

    # Adaptive bootstrap cap based on data size
    if len(x) <= 50:
        max_boot = 99
    elif len(x) <= 100:
        max_boot = 50
    else:
        max_boot = 30

    if n_boot > max_boot:
        n_boot = max_boot
        capped = True

    result = dip_test(x, n_boot=n_boot, random_state=random_state)

    return _convert_result(
        {
            "dip": result.dip,
            "p_value": result.p_value,
            "n_boot": result.n_boot,
            "n_extreme": result.n_extreme,
            "capped": capped,
            "subsampled": subsampled,
            "n_original": n_original,
        }
    )


def get_pola_version():
    """Return pola package version."""
    from pola import __version__

    return __version__


def supported_kernels():
    """Return list of supported kernel names."""
    return ["gaussian", "epanechnikov", "uniform", "triangular"]


def supported_methods():
    """Return list of supported search methods."""
    return ["auto", "binary", "brent"]


def supported_formats():
    """Return list of supported file extensions for upload."""
    return [
        ".csv",
        ".tsv",
        ".txt",
        ".json",
        ".md",
        ".html",
        ".htm",
        ".xlsx",
        ".xls",
        ".docx",
        ".pdf",
    ]
