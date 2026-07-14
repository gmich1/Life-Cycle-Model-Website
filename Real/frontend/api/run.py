"""
api/run.py — Vercel Python serverless function.

Receives model parameters from the frontend form, runs the life-cycle model
(backward induction + Monte Carlo simulation), and returns the simulated
series as JSON. Served at /api/run.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Make the vendored model package importable as top-level modules
# (solver.py does `from model import ...`) without editing those files.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_model"))

from solver import solve_model, simulate  # noqa: E402
from plots import make_charts  # noqa: E402

# Parameters the form is expected to send (matches the frontend FIELDS list).
FIELD_NAMES = [
    "tb", "tr", "td", "rho", "delta", "psi", "r", "mu", "sigr", "smay",
    "smav", "corr_v", "corr_y", "ret_fac", "aa", "b1", "b2", "b3", "ncash",
    "na", "nc", "n", "maxcash", "mincash", "nsim",
]


def _validate(inputs):
    """Return an error string if any expected field is missing or non-numeric."""
    if not isinstance(inputs, dict):
        return "Request body must be a JSON object of parameters."
    for name in FIELD_NAMES:
        if name not in inputs:
            return f"{name} is required."
        try:
            value = float(inputs[name])
        except (TypeError, ValueError):
            return f"{name} must be a number."
        if value != value or value in (float("inf"), float("-inf")):
            return f"{name} must be a finite number."
    return None


def _run_model(inputs):
    """Run the model and return the JSON-serializable result payload.

    'sim' feeds the year-by-year table; 'charts' holds the two life-cycle
    figures (base64 PNG data URIs) rendered from these same parameters.
    """
    params, grids, survprob, income, C, A, V = solve_model(inputs)
    sim = simulate(params, grids, survprob, income, C, A)
    charts = make_charts(params, grids, sim, C, A)
    return {
        "sim": {key: value.tolist() for key, value in sim.items()},
        "charts": charts,
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            inputs = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "Invalid JSON in request body."})

        error = _validate(inputs)
        if error:
            return self._send(400, {"error": error})

        try:
            payload = _run_model(inputs)
        except Exception as exc:  # surface any solver failure to the UI banner
            return self._send(500, {"error": f"Model run failed: {exc}"})

        return self._send(200, payload)
