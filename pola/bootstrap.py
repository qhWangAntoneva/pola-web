"""
Bootstrap confidence interval estimation for critical bandwidth.

Provides resampling-based inference for the critical bandwidth parameter,
returning confidence intervals and standard errors.
"""

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from pola.bandwidth import _validate_input, critical_bandwidth


@dataclass
class BootstrapResult:
    """
    Result of a bootstrap critical bandwidth analysis.

    Attributes
    ----------
    h_crit : float
        Critical bandwidth on the original (non-resampled) data.
    ci_lower : float
        Lower bound of the (1 - alpha) percentile confidence interval.
    ci_upper : float
        Upper bound of the (1 - alpha) percentile confidence interval.
    standard_error : float
        Bootstrap standard error (std of resampled h_crit distribution).
    distribution : np.ndarray
        Array of all n_resamples bootstrap h_crit values.
    n_resamples : int
        Number of bootstrap resamples performed.
    confidence_level : float
        The confidence level used (1 - alpha).
    """

    h_crit: float
    ci_lower: float
    ci_upper: float
    standard_error: float
    distribution: np.ndarray
    n_resamples: int
    confidence_level: float


def bootstrap_critical_bandwidth(
    x: np.ndarray,
    n_resamples: int = 999,
    alpha: float = 0.05,
    random_state: Optional[int] = None,
    **kwargs: Any,
) -> BootstrapResult:
    """
    Bootstrap confidence interval for the critical bandwidth.

    Resamples the input data with replacement, computes h_crit for each
    resample, and returns a percentile confidence interval and standard error.

    Parameters
    ----------
    x : np.ndarray
        1D array of input data.
    n_resamples : int, optional
        Number of bootstrap resamples (default 999).
    alpha : float, optional
        Significance level for the confidence interval (default 0.05 -> 95% CI).
    random_state : int, optional
        Random seed for reproducible resampling.
    **kwargs
        Additional keyword arguments passed through to critical_bandwidth().
        See critical_bandwidth() documentation for supported options
        (h_min, h_max, tol, max_iter, method, kernel).

    Returns
    -------
    BootstrapResult
        Structured result with h_crit, CI bounds, standard error, and
        the full bootstrap distribution.

    Notes
    -----
    The confidence interval is computed using the percentile method:
    lower and upper percentiles of the bootstrap distribution at
    (alpha/2) and (1 - alpha/2).

    A small number of resamples may fail to converge (h_crit is still
    returned as a float). These failed results are included in the
    bootstrap distribution.
    """
    _validate_input(x)

    rng = np.random.default_rng(random_state)

    # Critical bandwidth on original data
    h_crit_original, _ = critical_bandwidth(x, **kwargs)

    n = len(x)
    boot_samples: np.ndarray = np.empty(n_resamples)

    for i in range(n_resamples):
        resample = rng.choice(x, size=n, replace=True)
        h_crit_boot, _ = critical_bandwidth(resample, **kwargs)
        boot_samples[i] = h_crit_boot

    # Percentile CI
    p_low = 100 * alpha / 2
    p_high = 100 * (1 - alpha / 2)
    ci_lower, ci_upper = np.percentile(boot_samples, [p_low, p_high])

    # Standard error
    standard_error = float(np.std(boot_samples, ddof=1))

    return BootstrapResult(
        h_crit=h_crit_original,
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        standard_error=standard_error,
        distribution=boot_samples,
        n_resamples=n_resamples,
        confidence_level=1 - alpha,
    )
