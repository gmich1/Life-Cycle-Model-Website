import base64
import os
import sys

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api", "_model")
sys.path.insert(0, MODEL_DIR)

from solver import solve_model, simulate  # noqa: E402
from plots import make_charts, _band_note  # noqa: E402

SMALL = dict(
    tb=20, tr=66, td=100, rho=10.0, delta=0.97, psi=0.5, r=1.015, mu=0.04,
    sigr=0.2, smay=0.1, smav=0.1, corr_v=0.0, corr_y=0.0, ret_fac=0.68212,
    aa=0.530339, b1=0.16818, b2=-0.00323371, b3=1.9704e-5,
    ncash=15, na=15, nc=11, n=5, maxcash=200.0, mincash=0.25, nsim=400,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _is_png(uri):
    assert uri.startswith("data:image/png;base64,"), uri[:40]
    raw = base64.b64decode(uri.split(",", 1)[1])
    return raw[:8] == PNG_MAGIC


def main():
    # The coverage note is derived from the constant, not hard-coded.
    assert _band_note() == "Shaded = central 95% of simulated households", _band_note()

    params, grids, survprob, income, C, A, V = solve_model(SMALL)
    sim = simulate(params, grids, survprob, income, C, A)
    charts = make_charts(params, grids, sim, C, A)

    assert set(charts) == {"lifecycle", "policy", "composition"}, sorted(charts)
    for key in charts:
        assert _is_png(charts[key]), key

    print("Task 2 tests passed")


if __name__ == "__main__":
    main()
