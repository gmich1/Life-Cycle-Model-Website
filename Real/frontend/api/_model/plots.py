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

from solver import BAND_SIGMAS  # noqa: E402  (single source of truth)


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


def _band_note():
    """Caption describing the shaded band, driven by BAND_SIGMAS."""
    n = BAND_SIGMAS
    unit = "standard deviation" + ("" if n == 1 else "s")
    return f"Shaded = within {n:g} {unit} of the mean (clamped to feasible values)"


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

    # ---- Figure 2: life-cycle profiles (with +/-1 SD bands) ----
    ages = np.arange(tb, td + 1)
    bands = sim["bands"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Panel 1: consumption / wealth / income (levels)
    ax = axes[0]
    for key, color, style, lab in (("C", "red", "-", "Consumption"),
                                   ("W", "blue", "--", "Wealth"),
                                   ("Y", "black", ":", "Income")):
        ax.fill_between(ages, bands[key]["lo"], bands[key]["hi"],
                        color=color, alpha=0.15, linewidth=0)
        ax.plot(ages, sim["mean" + key], color=color, linestyle=style,
                linewidth=2, label=lab)
    ax.set_title("Life-Cycle Profiles (normalized)")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    # Panel 2: average stock share
    ax = axes[1]
    ax.fill_between(ages, bands["alpha"]["lo"], bands["alpha"]["hi"],
                    color="blue", alpha=0.15, linewidth=0)
    ax.plot(ages, sim["meanalpha"], color="blue", linewidth=2)
    ax.set_title("Average Stock Share")
    ax.set_xlabel("Age")
    ax.set_ylabel("Share in stocks")
    ax.set_xlim(tb, td)
    ax.set_ylim(0, 1.1)

    # Panel 3: scaled by age-20 income
    ax = axes[2]
    for key, color, style, lab in (("Cs", "red", "-", "Consumption"),
                                   ("Ws", "blue", "--", "Wealth"),
                                   ("Ys", "black", ":", "Income")):
        ax.fill_between(ages, bands[key]["lo"], bands[key]["hi"],
                        color=color, alpha=0.15, linewidth=0)
        ax.plot(ages, sim["mean" + key], color=color, linestyle=style,
                linewidth=2, label=lab)
    ax.set_title("Scaled by Age-20 Income")
    ax.set_xlabel("Age")
    ax.legend()
    ax.set_xlim(tb, td)

    fig.text(0.5, -0.01, _band_note(), ha="center", va="top",
             fontsize=9, style="italic")
    fig.tight_layout()
    lifecycle_uri = _fig_to_uri(fig)

    # ---- Figure 3: portfolio composition (stocks & bonds, each banded) ----
    # Unstacked so each holding can carry its own +/-1 SD band.
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.fill_between(ages, bands["S"]["lo"], bands["S"]["hi"],
                    color="#003E74", alpha=0.15, linewidth=0)
    ax.plot(ages, np.asarray(sim["meanS"]), color="#003E74",
            linewidth=2, label="Stocks")

    ax.fill_between(ages, bands["B"]["lo"], bands["B"]["hi"],
                    color="#9ecae1", alpha=0.30, linewidth=0)
    ax.plot(ages, np.asarray(sim["meanB"]), color="#9ecae1",
            linewidth=2, label="Bonds")

    ax.set_title("Portfolio Composition: Stocks vs Bonds")
    ax.set_xlabel("Age")
    ax.set_ylabel("Amount held (normalized by income)")
    ax.legend(loc="upper left")
    ax.set_xlim(tb, td)
    ax.set_ylim(bottom=0)
    ax.text(0.99, 0.02, _band_note(), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, style="italic")
    fig.tight_layout()
    composition_uri = _fig_to_uri(fig)

    return {
        "lifecycle": lifecycle_uri,
        "policy": policy_uri,
        "composition": composition_uri,
    }
