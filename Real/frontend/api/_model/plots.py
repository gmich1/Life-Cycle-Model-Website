"""
plots.py — Render the two life-cycle figures with matplotlib.

These reproduce the graphs shown in algorithm_simple.html, but are generated
from the *user's* submitted parameters on every run (instead of being frozen
notebook snapshots). Each figure is returned as a base64 PNG data URI that the
frontend can drop straight into an <img src=...>.

Uses the headless "Agg" backend so it works in a serverless function with no
display.
"""
import io
import base64

import numpy as np
import matplotlib
matplotlib.use("Agg")  # must be set before importing pyplot
import matplotlib.pyplot as plt  # noqa: E402

# Imperial-themed colours, matching the rest of the site.
_C_CONS = "#C0392B"   # consumption (red)
_C_WEALTH = "#003E74"  # wealth (imperial blue)
_C_INCOME = "#2E7D32"  # income (green)
_C_STOCK = "#0091D4"   # stock share (light blue)


def _fig_to_uri(fig):
    """Serialise a Matplotlib figure to a base64 PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def make_charts(params, grids, sim, A):
    """Build both figures and return {'lifecycle': uri, 'policy': uri}."""
    tb = int(params["tb"])
    td = int(params["td"])
    ages = np.arange(tb, td + 1)
    gcash = grids["gcash"]

    # ---- Chart 1: consumption / wealth / income + stock share over life ----
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ages, sim["meanC"], color=_C_CONS, lw=2, label="Consumption")
    ax.plot(ages, sim["meanW"], color=_C_WEALTH, lw=2, ls="--", label="Wealth")
    ax.plot(ages, sim["meanY"], color=_C_INCOME, lw=2, ls=":", label="Income")
    ax.set_xlabel("Age")
    ax.set_ylabel("Multiples of permanent income")
    ax.set_xlim(tb, td)

    # Stock share lives on 0..1, so give it its own right-hand axis.
    ax2 = ax.twinx()
    ax2.plot(ages, sim["meanalpha"], color=_C_STOCK, lw=2, label="Stock share (right axis)")
    ax2.set_ylabel("Share in stocks")
    ax2.set_ylim(0, 1.05)

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, loc="upper left", fontsize=8)
    ax.set_title("How consumption, wealth, income, and stock share evolve over a lifetime",
                 fontsize=10)
    lifecycle_uri = _fig_to_uri(fig)

    # ---- Chart 2: optimal stock share vs cash-on-hand at a few ages ----
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for age, colour in zip((25, 45, 65), (_C_STOCK, _C_WEALTH, "#7C1D6F")):
        t = age - tb
        if 0 <= t < A.shape[1]:
            ax.plot(gcash, A[:, t], lw=2, color=colour, label=f"Age {age}")
    ax.set_xlim(0, 30)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Cash-on-hand (multiples of permanent income)")
    ax.set_ylabel("Share in stocks")
    ax.set_title("At every age, the stock share falls as your savings grow", fontsize=10)
    ax.legend(fontsize=8)
    policy_uri = _fig_to_uri(fig)

    return {"lifecycle": lifecycle_uri, "policy": policy_uri}
