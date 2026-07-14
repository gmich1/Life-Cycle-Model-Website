"""
plots.py — Render the algorithm-details figures with matplotlib.

Reproduces the two composite figures from the notebook (policy_functions and
lifecycle_profiles), but generated from the *user's* submitted parameters on
every run instead of being frozen notebook snapshots. Each figure is returned
as a base64 PNG data URI the frontend can drop into an <img src=...>.

The notebook overlays a red dashed MATLAB reference line; that reference only
exists for the default parameters, so here we plot the Python result alone.

Uses the headless "Agg" backend so it works in a serverless function.
"""
import io
import base64

import numpy as np
import matplotlib
matplotlib.use("Agg")  # must be set before importing pyplot
import matplotlib.pyplot as plt  # noqa: E402


def _fig_to_uri(fig):
    """Serialise a Matplotlib figure to a base64 PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _policy_ages(tb, td):
    """Young / mid / near-retirement ages to show, kept inside [tb, td]."""
    ages = [a for a in (25, 45, 65) if tb <= a <= td]
    if not ages:
        ages = sorted({tb, (tb + td) // 2, max(tb, td - 1)})
    return ages


def make_charts(params, grids, sim, C, A):
    """Build both figures and return {'lifecycle': uri, 'policy': uri}."""
    tb = int(params["tb"])
    td = int(params["td"])
    tn = A.shape[1]
    gcash = grids["gcash"]

    # ---- Figure 1: policy functions (consumption + stock share vs cash) ----
    ages_to_plot = _policy_ages(tb, td)
    ncol = len(ages_to_plot)
    fig, axes = plt.subplots(2, ncol, figsize=(5 * ncol, 9), squeeze=False)
    for col, age in enumerate(ages_to_plot):
        t = min(age - tb, tn - 1)  # 0-based period, clamped into range

        ax = axes[0, col]
        ax.plot(gcash, C[:, t], "b-", linewidth=2, label="Python")
        ax.set_title(f"Consumption at Age {age}")
        ax.set_xlabel("Cash-on-hand")
        ax.set_ylabel("Consumption")
        ax.legend()
        ax.set_xlim(0, 30)

        ax = axes[1, col]
        ax.plot(gcash, A[:, t], "b-", linewidth=2, label="Python")
        ax.set_title(f"Stock Share at Age {age}")
        ax.set_xlabel("Cash-on-hand")
        ax.set_ylabel("Share in stocks")
        ax.legend()
        ax.set_xlim(0, 30)
        ax.set_ylim(-0.05, 1.1)
    fig.tight_layout()
    policy_uri = _fig_to_uri(fig)

    # ---- Figure 2: life-cycle profiles ----
    ages = np.arange(tb, td + 1)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    ax = axes[0]
    ax.plot(ages, sim["meanC"], "r-", linewidth=2, label="Consumption")
    ax.plot(ages, sim["meanW"], "b--", linewidth=2, label="Wealth")
    ax.plot(ages, sim["meanY"], "k:", linewidth=2, label="Income")
    ax.set_title("Life-Cycle Profiles (normalized)")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    ax = axes[1]
    ax.plot(ages, sim["meanalpha"], "b-", linewidth=2)
    ax.set_title("Average Stock Share")
    ax.set_xlabel("Age")
    ax.set_ylabel("Share in stocks")
    ax.set_xlim(tb, td)
    ax.set_ylim(0, 1.1)

    ax = axes[2]
    ax.plot(ages, sim["meanCs"], "r-", linewidth=2, label="Consumption")
    ax.plot(ages, sim["meanWs"], "b--", linewidth=2, label="Wealth")
    ax.plot(ages, sim["meanYs"], "k:", linewidth=2, label="Income")
    ax.set_title("Scaled by Age-20 Income")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    fig.tight_layout()
    lifecycle_uri = _fig_to_uri(fig)

    return {"lifecycle": lifecycle_uri, "policy": policy_uri}
