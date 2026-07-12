"""
app.py — FastAPI web layer for the life-cycle model.
Step 1: receive parameters from the frontend and echo them back.
(Model wiring comes later.)
"""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from solver import solve_model, simulate

app = FastAPI()

# Allow the React dev server (localhost:3000) to call this API.
# Without this, the browser blocks the request with a CORS error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/run")
def run(inputDict: dict):
    t0 = time.time()
    params, grids, survprob, income, C, A, V = solve_model(inputDict)
    t1 = time.time()
    print(f"Backward induction complete in {t1-t0:.1f}s.")
    print(f"  C shape: {C.shape}, A shape: {A.shape}, V shape: {V.shape}")
    print(f"  V[0, 0] = {V[0,0]:.8f}, V[-1, -1] = {V[-1,-1]:.8f}")

    print("Running simulation...")
    t0 = time.time()
    sim = simulate(params, grids, survprob, income, C, A)
    t1 = time.time()
    print(f"Simulation complete in {t1-t0:.1f}s.")
    print(f"  Mean consumption at age 20: {sim['meanC'][0]:.8f}")
    print(f"  Mean wealth at age 65: {sim['meanW'][45]:.8f}")

    # Convert every NumPy array in sim to a plain list so FastAPI can send it as JSON.
    sim_json = {key: value.tolist() for key, value in sim.items()}
    return {"sim": sim_json}
# Running it:
#   cd "C:\Users\George\OneDrive\Documents\Research\Real\backend"
#   .\venv\Scripts\Activate.ps1
#   uvicorn app:app --reload --port 8000