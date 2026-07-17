import os
import sys

import numpy as np

# Import the model package that lives inside the Vercel function dir.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate, BAND_COVERAGE  # noqa: E402

# Small grids so the solve is fast; behaviour is identical to full size.
SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

EXPECTED = {"C", "W", "Y", "alpha", "S", "B", "Cs", "Ws", "Ys"}


def main():
    assert BAND_COVERAGE == 0.95, BAND_COVERAGE

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    tn = params["tn"]

    assert "bands" in sim, "sim must include a 'bands' key"
    assert set(sim["bands"]) == EXPECTED, sorted(sim["bands"])

    for key, band in sim["bands"].items():
        assert band["lo"].shape == (tn,), (key, band["lo"].shape)
        assert band["hi"].shape == (tn,), (key, band["hi"].shape)
        assert np.all(band["lo"] <= band["hi"] + 1e-9), f"lo>hi for {key}"

    # Non-negative quantities never dip below zero.
    for key in ("W", "S", "B"):
        assert np.all(sim["bands"][key]["lo"] >= -1e-9), f"negative lo for {key}"

    # The results-table JSON (built like run.py) must exclude bands.
    table = {k: v.tolist() for k, v in sim.items() if k != "bands"}
    assert "bands" not in table
    assert "meanC" in table and "meanalpha" in table

    print("Task 1 tests passed")


if __name__ == "__main__":
    main()
