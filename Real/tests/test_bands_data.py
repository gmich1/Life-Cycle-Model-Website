import os
import sys

import numpy as np

# Import the model package that lives inside the Vercel function dir.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate, BAND_SIGMAS  # noqa: E402

# Small grids so the solve is fast; behaviour is identical to full size.
SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

EXPECTED = {"C", "W", "Y", "alpha", "S", "B", "Cs", "Ws", "Ys"}


def main():
    assert BAND_SIGMAS == 1.0, BAND_SIGMAS

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    tn = params["tn"]

    assert "bands" in sim, "sim must include a 'bands' key"
    assert set(sim["bands"]) == EXPECTED, sorted(sim["bands"])

    means = {
        "C": sim["meanC"], "W": sim["meanW"], "Y": sim["meanY"],
        "alpha": sim["meanalpha"], "S": sim["meanS"], "B": sim["meanB"],
        "Cs": sim["meanCs"], "Ws": sim["meanWs"], "Ys": sim["meanYs"],
    }

    for key, band in sim["bands"].items():
        lo, hi, m = band["lo"], band["hi"], means[key]
        assert lo.shape == (tn,) and hi.shape == (tn,), (key, lo.shape, hi.shape)
        assert np.all(lo >= -1e-9), f"negative lo for {key}"      # clamped at 0
        assert np.all(lo <= m + 1e-9), f"lo>mean for {key}"
        assert np.all(hi >= m - 1e-9), f"hi<mean for {key}"

    # Stock share band stays within [0, 1].
    a = sim["bands"]["alpha"]
    assert np.all(a["hi"] <= 1.0 + 1e-9), "alpha hi>1"
    assert np.all(a["lo"] >= -1e-9), "alpha lo<0"

    # Symmetric mean +/- k*sd, then lower edge clamped at 0, implies
    #   lo == max(0, 2*mean - hi)
    # for every series whose hi is NOT capped (all but alpha). This verifies
    # the symmetry and the clamp without needing the per-path std.
    for key in ("C", "W", "Y", "S", "B", "Cs", "Ws", "Ys"):
        lo, hi, m = sim["bands"][key]["lo"], sim["bands"][key]["hi"], means[key]
        expected_lo = np.maximum(2.0 * m - hi, 0.0)
        assert np.allclose(lo, expected_lo, atol=1e-9), f"clamp/symmetry mismatch for {key}"

    # The results-table JSON (built like run.py) must exclude bands.
    table = {k: v.tolist() for k, v in sim.items() if k != "bands"}
    assert "bands" not in table
    assert "meanC" in table and "meanalpha" in table

    print("Task 1 tests passed")


if __name__ == "__main__":
    main()
