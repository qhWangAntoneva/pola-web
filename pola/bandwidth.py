"""
Bandwidth calculation functions for kernel density estimation.
Includes Silverman's rule of thumb and critical bandwidth detection for bimodal distributions.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple, Union

import numpy as np
from scipy import signal
from scipy.optimize import brentq

# ---------------------------------------------------------------------------
# Kernel functions
# ---------------------------------------------------------------------------

_KERNELS: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "gaussian": lambda u: np.exp(-(u**2) / 2) / np.sqrt(2 * np.pi),
    "epanechnikov": lambda u: 0.75 * (1 - u**2) * (np.abs(u) <= 1),
    "uniform": lambda u: 0.5 * (np.abs(u) <= 1).astype(float),
    "triangular": lambda u: (1 - np.abs(u)) * (np.abs(u) <= 1),
}


def _resolve_kernel(kernel: Union[str, Callable]) -> Callable[[np.ndarray], np.ndarray]:
    """Resolve kernel parameter to a callable kernel function."""
    if callable(kernel):
        return kernel
    if kernel not in _KERNELS:
        raise ValueError(
            f"Unknown kernel '{kernel}'. Built-in kernels: {', '.join(sorted(_KERNELS))}"
        )
    return _KERNELS[kernel]


def _validate_input(x: np.ndarray) -> None:
    """Validate input array: must be 1D, non-empty, finite."""
    if x.ndim != 1:
        raise ValueError(f"Input must be 1-dimensional, got {x.ndim} dimensions")
    if len(x) == 0:
        raise ValueError("Input must not be empty")
    if not np.all(np.isfinite(x)):
        raise ValueError("Input contains NaN or infinite values")


def _kde_grid_points(n: int, min_grid: int = 200, max_grid: int = 800) -> int:
    """Adapt KDE grid resolution to data size for performance.

    Larger datasets need fewer grid points relative to size because the
    KDE becomes smoother with more data. Smaller datasets benefit from
    finer grids to capture detail.

    Returns grid_points clamped to [min_grid, max_grid].
    Formula: min(max_grid, max(min_grid, n // 10))
    """
    return min(max_grid, max(min_grid, n // 10))


def silverman_bandwidth(x: np.ndarray) -> float:
    """
    Calculate Silverman's rule of thumb bandwidth for univariate data.

    Parameters
    ----------
    x : np.ndarray
        1D array of input data points

    Returns
    -------
    float
        Silverman's rule of thumb bandwidth value

    Notes
    -----
    Formula: h = 1.06 * min(std, IQR/1.34) * n^(-1/5)
    """
    _validate_input(x)
    n = len(x)

    if n == 1:
        return 1.0  # Default bandwidth for single point

    std = np.std(x, ddof=1)
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    h = 1.06 * np.min([std, iqr / 1.34]) * (n ** (-0.2))
    return h if h > 0 else 0.01  # floor at 0.01 for constant data


def count_modes(
    x: np.ndarray,
    h: float,
    grid_points: Optional[int] = None,
    prominence: float = 0.01,
    kernel: Union[str, Callable] = "gaussian",
) -> int:
    """
    Count number of modes in kernel density estimate for given bandwidth.

    Uses scipy.signal.find_peaks with a prominence threshold to filter out
    spurious modes caused by numerical noise.

    Parameters
    ----------
    x : np.ndarray
        Input data
    h : float
        Bandwidth value
    grid_points : int, optional
        Number of evaluation points. Defaults to adaptive based on data size.
    prominence : float, optional
        Minimum prominence as a fraction of max density (default 0.01).
        Peaks below this fraction of the maximum KDE height are ignored.

    Returns
    -------
    int
        Number of detected modes
    """
    _validate_input(x)
    if h <= 0:
        return 1  # zero or negative bandwidth is always unimodal
    if grid_points is None:
        grid_points = _kde_grid_points(len(x))
    grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, grid_points)
    kde_vals = gaussian_kde(x, grid, h, kernel=kernel)

    peaks, _ = signal.find_peaks(kde_vals, prominence=prominence * np.max(kde_vals))
    return len(peaks)


def _trough_ratio(
    x: np.ndarray,
    h: float,
    grid_points: Optional[int] = None,
    prominence: float = 0.01,
    kernel: Union[str, Callable] = "gaussian",
) -> float:
    """
    Continuous measure of bimodality strength at bandwidth h.

    Returns dip_ratio = min_valley / min_peak_height, a value in (0, 1].

    - dip_ratio near 0: deep trough between modes (strongly bimodal)
    - dip_ratio near 1: no meaningful trough (unimodal)
    - dip_ratio approx 0.5: approximate critical bandwidth

    For KDE with < 2 peaks, returns 1.0 (unimodal signal).
    """
    _validate_input(x)
    if h <= 0:
        return 1.0

    if grid_points is None:
        grid_points = _kde_grid_points(len(x))

    grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, grid_points)
    kde_vals = gaussian_kde(x, grid, h, kernel=kernel)

    peaks = signal.find_peaks(kde_vals, prominence=prominence * np.max(kde_vals))[0]
    if len(peaks) < 2:
        return 1.0

    # Get the two highest peaks
    peak_heights = kde_vals[peaks]
    top_two = np.argsort(peak_heights)[-2:]
    peak_indices = np.sort(peaks[top_two])

    # Minimum KDE value between the two peaks
    left, right = peak_indices[0], peak_indices[1]
    valley_val = np.min(kde_vals[left : right + 1])
    min_peak = min(kde_vals[left], kde_vals[right])

    return valley_val / min_peak if min_peak > 0 else 1.0


def gaussian_kde(
    x: np.ndarray,
    grid: np.ndarray,
    h: float,
    kernel: Union[str, Callable] = "gaussian",
) -> np.ndarray:
    """
    Kernel density estimation using vectorized broadcasting.

    Parameters
    ----------
    x : np.ndarray
        Input data points
    grid : np.ndarray
        Points where density is evaluated
    h : float
        Bandwidth
    kernel : str or callable, optional
        Kernel function. Built-in options: "gaussian" (default),
        "epanechnikov", "uniform", "triangular".
        Callables must accept an ndarray of standardized distances
        u = (x - xi)/h and return an ndarray of kernel weights.

    Returns
    -------
    np.ndarray
        Density estimates at grid points
    """
    _validate_input(x)
    n = len(x)
    kernel_func = _resolve_kernel(kernel)
    # Broadcasting: (grid_n, 1) - (1, n) → (grid_n, n), sum over data axis
    diff = grid[:, np.newaxis] - x[np.newaxis, :]
    u = diff / h
    density = np.sum(kernel_func(u), axis=1)
    return density / (n * h)


def _bracket_critical(
    x: np.ndarray,
    h_min: float,
    h_max: float,
    max_iter: int = 10,
    kernel: Union[str, Callable] = "gaussian",
) -> Tuple[float, float]:
    """
    Narrow bracket around critical bandwidth using binary search on count_modes.

    Returns (low, high) where count_modes(x, low) >= 2 and count_modes(x, high) == 1.
    Caller must ensure boundary conditions are met before calling.
    """
    low, high = h_min, h_max
    for _ in range(max_iter):
        mid = (low + high) / 2
        if count_modes(x, mid, kernel=kernel) >= 2:
            low = mid
        else:
            high = mid
    return low, high


def critical_bandwidth(
    x: np.ndarray,
    h_min: Optional[float] = None,
    h_max: Optional[float] = None,
    tol: float = 1e-6,
    max_iter: int = 100,
    method: str = "auto",
    kernel: Union[str, Callable] = "gaussian",
) -> Tuple[float, bool]:
    """
    Calculate critical bandwidth for bimodal distribution.

    Critical bandwidth is the smallest bandwidth where the kernel density
    estimate becomes unimodal.

    Parameters
    ----------
    x : np.ndarray
        1D array of input data
    h_min : float, optional
        Lower bound for bandwidth search
    h_max : float, optional
        Upper bound for bandwidth search
    tol : float, optional
        Convergence tolerance
    max_iter : int, optional
        Maximum number of iterations
    method : str, optional
        Search method: "auto" (default, hybrid Brent+binary),
        "binary" (pure binary search), or "brent" (pure Brent).
    kernel : str or callable, optional
        Kernel function. Built-in: "gaussian" (default), "epanechnikov",
        "uniform", "triangular". Also accepts callables.

    Returns
    -------
    tuple
        (critical_bandwidth_value, convergence_success)
    """
    _validate_input(x)

    if h_min is None:
        h_min = silverman_bandwidth(x) / 20.0
    if h_max is None:
        h_max = silverman_bandwidth(x) * 10.0

    if h_min <= 0:
        h_min = 1e-8

    # Check boundary conditions
    modes_min = count_modes(x, h_min, kernel=kernel)
    modes_max = count_modes(x, h_max, kernel=kernel)

    if modes_max >= 2:
        return h_max, False
    if modes_min == 1:
        return h_min, False

    # --- Pure binary search ---
    if method == "binary":
        low, high = h_min, h_max
        for _ in range(max_iter):
            mid = (low + high) / 2
            if count_modes(x, mid, kernel=kernel) >= 2:
                low = mid
            else:
                high = mid
            if high - low < tol:
                break
        return (low + high) / 2, True

    # --- Brent / hybrid method ---
    if method == "auto":
        # Coarse binary search to narrow bracket
        low, high = _bracket_critical(x, h_min, h_max, min(10, max_iter // 3), kernel=kernel)
    else:  # method == "brent"
        low, high = h_min, h_max

    # Build objective: f(h) = trough_ratio - 0.5, root at critical bandwidth
    def _objective(h: float) -> float:
        return _trough_ratio(x, h, kernel=kernel) - 0.5

    # Verify sign change for brentq
    f_low = _objective(low)
    f_high = _objective(high)

    if f_low * f_high < 0:
        try:
            h_result = brentq(_objective, low, high, xtol=tol, maxiter=max_iter)
            # Verify: result should be unimodal (modes == 1)
            if count_modes(x, h_result, kernel=kernel) == 1:
                return h_result, True
        except (ValueError, RuntimeError):
            pass

    # Fallback: full binary search
    low, high = h_min, h_max
    for _ in range(max_iter):
        mid = (low + high) / 2
        if count_modes(x, mid, kernel=kernel) >= 2:
            low = mid
        else:
            high = mid
        if high - low < tol:
            break
    return (low + high) / 2, True


def find_trough(
    x: np.ndarray,
    h: float,
    grid_points: Optional[int] = None,
    prominence: float = 0.01,
    refine: bool = True,
    kernel: Union[str, Callable] = "gaussian",
) -> Optional[float]:
    """
    Find the trough (lowest point) between the two most prominent KDE modes.

    Parameters
    ----------
    x : np.ndarray
        1D array of input data
    h : float
        Bandwidth at which to evaluate the KDE
    grid_points : int, optional
        Number of evaluation points (default 1000)
    prominence : float, optional
        Minimum prominence as fraction of max density (default 0.01)
    refine : bool, optional
        If True, use quadratic interpolation to refine trough position
    kernel : str or callable, optional
        Kernel function (default "gaussian").

    Returns
    -------
    float or None
        x-coordinate of the trough between the two highest KDE peaks,
        or None if fewer than 2 peaks are detected.
    """
    _validate_input(x)
    if h <= 0:
        return None

    if grid_points is None:
        grid_points = _kde_grid_points(len(x))
    grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, grid_points)
    kde_vals = gaussian_kde(x, grid, h, kernel=kernel)

    peaks = signal.find_peaks(kde_vals, prominence=prominence * np.max(kde_vals))[0]
    if len(peaks) < 2:
        return None

    # Two highest peaks
    peak_heights = kde_vals[peaks]
    top_two = np.argsort(peak_heights)[-2:]
    peak_indices = np.sort(peaks[top_two])

    left, right = peak_indices[0], peak_indices[1]
    min_idx = np.argmin(kde_vals[left : right + 1]) + left

    if not refine:
        return grid[min_idx]

    # Quadratic interpolation for sub-grid precision
    i = min_idx
    if 0 < i < len(grid) - 1:
        x0, x1, x2 = grid[i - 1], grid[i], grid[i + 1]
        y0, y1, y2 = kde_vals[i - 1], kde_vals[i], kde_vals[i + 1]
        denom = (x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1)
        if abs(denom) > 1e-15:
            return x1 - 0.5 * ((x2 - x1) ** 2 * (y1 - y0) - (x1 - x0) ** 2 * (y2 - y1)) / denom

    return float(grid[min_idx])


@dataclass
class Component:
    """Estimated parameters of a single Gaussian component in a bimodal mixture."""

    mean: float
    std: float
    weight: float


@dataclass
class BimodalDecomposition:
    """Complete decomposition of a bimodal distribution into two components."""

    critical_bandwidth: float
    component1: Component
    component2: Component
    separation_point: float
    dip_ratio: float


def detect_components(
    x: np.ndarray,
    h_factor: float = 0.85,
    grid_points: Optional[int] = None,
    kernel: Union[str, Callable] = "gaussian",
) -> BimodalDecomposition:
    """
    Decompose a bimodal distribution into two component Gaussians.

    Splits data at the KDE trough between the two highest peaks at a
    sub-critical bandwidth, then computes sample statistics for each side.

    Parameters
    ----------
    x : np.ndarray
        1D array of input data
    h_factor : float, optional
        Multiplier on critical bandwidth for analysis (default 0.85).
        Lower = more bimodal (clearer trough), higher = closer to transition.
    grid_points : int, optional
        KDE grid resolution (default 1000)
    kernel : str or callable, optional
        Kernel function (default "gaussian").

    Returns
    -------
    BimodalDecomposition
        Structured decomposition with component parameters.

    Raises
    ------
    ValueError
        If fewer than 2 KDE peaks are detected at the analysis bandwidth.
    """
    _validate_input(x)

    h_crit, ok = critical_bandwidth(x, kernel=kernel)
    if not ok:
        import warnings

        warnings.warn(
            "Critical bandwidth search did not fully converge; proceeding with best estimate."
        )

    h_analysis = h_crit * h_factor

    if grid_points is None:
        grid_points = _kde_grid_points(len(x))

    # Build KDE and find peaks
    grid = np.linspace(x.min() - 3 * h_analysis, x.max() + 3 * h_analysis, grid_points)
    kde_vals = gaussian_kde(x, grid, h_analysis, kernel=kernel)
    peaks = signal.find_peaks(kde_vals, prominence=0.01 * np.max(kde_vals))[0]

    if len(peaks) < 2:
        raise ValueError(
            f"Data does not appear bimodal: only {len(peaks)} KDE peak(s) "
            f"detected at h={h_analysis:.4f} (h_crit={h_crit:.4f}). "
            "The distribution may be unimodal or very weakly bimodal."
        )

    # Find the two highest peaks and the trough between them
    peak_heights = kde_vals[peaks]
    top_two = np.argsort(peak_heights)[-2:]
    peak_indices = np.sort(peaks[top_two])
    left, right = peak_indices[0], peak_indices[1]
    min_idx = np.argmin(kde_vals[left : right + 1]) + left
    trough_x = float(grid[min_idx])

    valley_val = float(np.min(kde_vals[left : right + 1]))
    min_peak = float(min(kde_vals[left], kde_vals[right]))
    dip_ratio = valley_val / min_peak if min_peak > 0 else 1.0

    # Split data at the trough and compute component statistics
    x_left = x[x <= trough_x]
    x_right = x[x > trough_x]

    if len(x_left) == 0 or len(x_right) == 0:
        raise ValueError(
            "Trough-based split produced an empty component. "
            "The data may be unimodal or the trough is at the data boundary."
        )

    n_total = len(x)
    comp1 = Component(
        mean=float(np.mean(x_left)),
        std=float(np.std(x_left, ddof=1)),
        weight=len(x_left) / n_total,
    )
    comp2 = Component(
        mean=float(np.mean(x_right)),
        std=float(np.std(x_right, ddof=1)),
        weight=len(x_right) / n_total,
    )

    # Ensure left = lower mean, right = higher mean
    if comp2.mean < comp1.mean:
        comp1, comp2 = comp2, comp1

    return BimodalDecomposition(
        critical_bandwidth=h_crit,
        component1=comp1,
        component2=comp2,
        separation_point=trough_x,
        dip_ratio=dip_ratio,
    )
