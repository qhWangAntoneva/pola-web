"""
Matplotlib visualization generators for Pyodide environment.

Returns PNG base64 data URLs instead of canvas element IDs, compatible with
Pyodide v0.27.0's matplotlib-pyodide which uses the Agg-WASM backend
(FigureCanvasAggWasm has no html5_canvas_element attribute).

Each function returns a data:image/png;base64,... URL for direct use in <img> tags.
"""

import io
import base64


def ensure_backend():
    """
    Configure matplotlib for Pyodide's HTML5 canvas backend.
    Safe to call multiple times (no-op after first call).
    Note: in Pyodide v0.27.0, this backend redirects to the Agg-WASM backend,
    which renders via savefig (not html5_canvas_element).
    """
    import matplotlib

    if matplotlib.get_backend() != "module://matplotlib_pyodide.html5_canvas_backend":
        matplotlib.use("module://matplotlib_pyodide.html5_canvas_backend")


def _fig_to_data_url(fig, dpi=100):
    """Convert a matplotlib figure to a PNG base64 data URL."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    png_b64 = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{png_b64}"


def kde_plot(data_list, h, kernel="gaussian", n_points=1000):
    """
    Generate KDE plot and return as PNG data URL.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    h : float
        Bandwidth.
    kernel : str, optional
        Kernel function.
    n_points : int, optional
        KDE grid resolution.

    Returns
    -------
    str
        PNG data URL for direct use in <img> tag.
        Format: ``data:image/png;base64,...``
    """
    ensure_backend()
    import matplotlib.pyplot as plt
    import numpy as np

    from pola import bandwidth as bw

    x = np.array(data_list, dtype=float)
    grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, n_points)
    kde = bw.gaussian_kde(x, grid, h, kernel=kernel)

    fig, ax = plt.subplots(figsize=(9, 5))
    n_bins = max(10, min(50, len(x) // 5))
    ax.hist(x, bins=n_bins, density=True, alpha=0.3, color="gray", edgecolor="none")
    ax.plot(grid, kde, "b-", lw=2.5, label=f"KDE (h={h:.4f})")
    ax.set_xlabel("x")
    ax.set_ylabel("Density")
    ax.set_title("Kernel Density Estimate")
    ax.legend()
    fig.tight_layout()

    url = _fig_to_data_url(fig)
    plt.close(fig)
    return url


def components_plot(data_list, h_crit, h_factor=0.85, kernel="gaussian", n_points=1000):
    """
    Generate component decomposition plot, return as PNG data URL.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    h_crit : float
        Critical bandwidth.
    h_factor : float, optional
        Multiplier on h_crit for analysis bandwidth.
    kernel : str, optional
        Kernel function.
    n_points : int, optional
        KDE grid resolution.

    Returns
    -------
    str or None
        PNG data URL, or None if data is not bimodal.
    """
    ensure_backend()
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import stats as scipy_stats

    from pola import bandwidth as bw

    x = np.array(data_list, dtype=float)
    h = h_crit * h_factor

    try:
        decomp = bw.detect_components(x, h_factor=h_factor, kernel=kernel)
    except ValueError:
        return None

    grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, n_points)
    kde = bw.gaussian_kde(x, grid, h, kernel=kernel)

    fig, ax = plt.subplots(figsize=(9, 5))
    n_bins = max(10, min(50, len(x) // 5))
    ax.hist(x, bins=n_bins, density=True, alpha=0.25, color="gray", edgecolor="none")

    ax.plot(grid, kde, "b-", lw=2.5, label="KDE")

    # Component Gaussians
    colors = ["#e67e22", "#27ae60"]
    for i, (comp, color) in enumerate(
        zip([decomp.component1, decomp.component2], colors), 1
    ):
        pdf = comp.weight * scipy_stats.norm.pdf(grid, comp.mean, comp.std)
        ax.plot(
            grid,
            pdf,
            color=color,
            ls="--",
            lw=2,
            label=f"Comp{i}: μ={comp.mean:.3f}, σ={comp.std:.3f}, w={comp.weight:.2f}",
        )

    # Trough line
    ax.axvline(
        decomp.separation_point,
        color="red",
        ls=":",
        lw=2,
        alpha=0.7,
        label=f"Trough={decomp.separation_point:.3f}",
    )

    ax.set_xlabel("x")
    ax.set_ylabel("Density")
    ax.set_title("Bimodal Component Decomposition")
    ax.legend(fontsize=9)
    fig.tight_layout()

    url = _fig_to_data_url(fig)
    plt.close(fig)
    return url


def bandwidth_sweep_plot(data_list, h_crit, kernel="gaussian", n_points=1000):
    """
    Generate 2x2 bandwidth sweep plot, return as PNG data URL.

    Shows KDE at four bandwidths: too small, Silverman, critical, too large.

    Parameters
    ----------
    data_list : list[float]
        Input data points.
    h_crit : float
        Critical bandwidth.
    kernel : str, optional
        Kernel function.
    n_points : int, optional
        KDE grid resolution.

    Returns
    -------
    str
        PNG data URL for direct use in <img> tag.
    """
    ensure_backend()
    import matplotlib.pyplot as plt
    import numpy as np

    from pola import bandwidth as bw

    x = np.array(data_list, dtype=float)
    h_silver = float(bw.silverman_bandwidth(x))

    bandwidths = [
        (h_crit * 0.3, f"h = {h_crit * 0.3:.4f}\n(too small)"),
        (h_silver, f"h = {h_silver:.4f}\n(Silverman)"),
        (h_crit, f"h = {h_crit:.4f}\n(critical)"),
        (h_crit * 3, f"h = {h_crit * 3:.4f}\n(too large)"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, (h, label) in zip(axes.flat, bandwidths):
        grid = np.linspace(x.min() - 3 * h, x.max() + 3 * h, n_points)
        kde = bw.gaussian_kde(x, grid, h, kernel=kernel)

        n_bins = max(10, min(50, len(x) // 5))
        ax.hist(x, bins=n_bins, density=True, alpha=0.3, color="gray", edgecolor="none")
        ax.plot(grid, kde, "b-", lw=2)
        ax.set_title(label, fontsize=10)

    fig.tight_layout()

    url = _fig_to_data_url(fig)
    plt.close(fig)
    return url
