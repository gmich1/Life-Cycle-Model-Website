"""
solver.py — Numerical methods and backward induction.
Direct translation of life_cycle.m (spline functions from Fortran via MATLAB).
Vectorized with NumPy for performance.
"""
import numpy as np
from model import build_params, build_grids, build_survival_probs, build_income


# ---------------------------------------------------------------------------
# Spline functions (exact translation of f_spline.m and f_sc_splint.m)
# ---------------------------------------------------------------------------

def f_spline(x, y, n, gam):
    """Compute cubic spline second derivatives.
    Translation of f_spline.m.
    Left BC: specified first derivative yp1 = x[0]^(-gam).
    Right BC: natural (y2[n-1] = 0).
    """
    y2 = np.zeros(n, dtype=np.float64)
    u = np.zeros(n, dtype=np.float64)

    yp1 = x[0] ** (-gam)
    y2[0] = -0.5
    u[0] = (3.0 / (x[1] - x[0])) * ((y[1] - y[0]) / (x[1] - x[0]) - yp1)

    for i in range(1, n - 1):
        sig = (x[i] - x[i - 1]) / (x[i + 1] - x[i - 1])
        p = sig * y2[i - 1] + 2.0
        y2[i] = (sig - 1.0) / p
        u[i] = (6.0 * ((y[i + 1] - y[i]) / (x[i + 1] - x[i])
                        - (y[i] - y[i - 1]) / (x[i] - x[i - 1]))
                / (x[i + 1] - x[i - 1]) - sig * u[i - 1]) / p

    y2[n - 1] = 0.0
    for k in range(n - 2, -1, -1):
        y2[k] = y2[k] * y2[k + 1] + u[k]

    return y2


def f_sc_splint_vec(xa, ya, y2a, n, x_arr):
    """Vectorized spline evaluation at array of x values.
    Uses np.searchsorted instead of binary search.
    Equivalent to calling f_sc_splint for each element.
    """
    x_arr = np.asarray(x_arr, dtype=np.float64).ravel()
    # Find intervals via searchsorted
    khi = np.searchsorted(xa, x_arr, side='right')
    khi = np.clip(khi, 1, n - 1)
    klo = khi - 1

    h = xa[khi] - xa[klo]
    a = (xa[khi] - x_arr) / h
    b = (x_arr - xa[klo]) / h
    y = (a * ya[klo] + b * ya[khi]
         + ((a**3 - a) * y2a[klo] + (b**3 - b) * y2a[khi]) * h**2 / 6.0)

    # Clamp to [ya[0], ya[n-1]]
    y = np.clip(y, ya[0], ya[n - 1])
    return y


def f_ntoil(value, grid, n):
    """Find grid index for uniform grid (in log space).
    Translation of f_ntoil.m. Returns 0-based index.
    """
    if value >= grid[n - 1]:
        return n - 2
    elif value < grid[0]:
        return 0
    else:
        ind = int((value - grid[0]) / (grid[1] - grid[0]))
        return min(ind, n - 2)


def f_ntoil_vec(values, grid, n):
    """Vectorized version of f_ntoil."""
    values = np.asarray(values, dtype=np.float64)
    step = grid[1] - grid[0]
    ind = np.floor((values - grid[0]) / step).astype(np.int64)
    ind = np.clip(ind, 0, n - 2)
    return ind


# ---------------------------------------------------------------------------
# Backward induction (vectorized)
# ---------------------------------------------------------------------------

def solve_model(inputDict):
    """Run the full backward induction.
    Returns params, grids, survprob, income, C, A, V.
    """
    params = build_params(inputDict)
    grids = build_grids(params)
    survprob = build_survival_probs()
    income = build_income(params, grids)

    p = params
    g = grids
    tn = p['tn']
    ncash = p['ncash']
    na = p['na']
    nc = p['nc']
    n = p['n']

    gcash = g['gcash']
    ga = g['ga']
    riskret = g['riskret']
    weig = g['weig']
    nweig1 = g['nweig1']
    gyp = income['gyp']
    yh = income['yh']

    delta = p['delta']
    rho = p['rho']
    psi_1 = p['psi_1']
    psi_2 = p['psi_2']
    theta = p['theta']
    ret_fac = p['ret_fac']

    # Initialize arrays
    C = np.zeros((ncash, tn), dtype=np.float64)
    V = np.zeros((ncash, tn), dtype=np.float64)
    A = np.ones((ncash, tn), dtype=np.float64)

    # -------------------------------------------------------------------
    # Terminal period (t = tn-1, 0-based index 80)
    # -------------------------------------------------------------------
    C[:, tn - 1] = gcash.copy()
    A[:, tn - 1] = 0.0
    V[:, tn - 1] = gcash * ((1.0 - delta) ** (p['psi'] / (p['psi'] - 1.0)))

    secd = f_spline(gcash, V[:, tn - 1], ncash, 1.0)

    # -------------------------------------------------------------------
    # Retirement periods: t = tn-2 downto tr-tb (0-based: 79 down to 46)
    # Only 1 loop over return shocks (n=5), no income shocks
    # -------------------------------------------------------------------
    t_retire_end = p['tr'] - p['tb']  # 46

    for t in range(tn - 2, t_retire_end - 1, -1):
        print(f"  Retirement period t={t} (age {t + p['tb']})")
        for i3 in range(ncash):
            # Determine consumption search bounds
            if i3 == 0:
                maxc = C[0, t + 1]
                minc = maxc / 2.0
            else:
                minc = C[i3 - 1, t]
                if i3 < 9:
                    maxc = minc + (gcash[i3] - gcash[i3 - 1])
                else:
                    mpc = max((C[i3 - 1, t] - C[i3 - 9, t])
                              / (gcash[i3 - 1] - gcash[i3 - 9]), 0.1)
                    maxc = minc + mpc * (gcash[i3] - gcash[i3 - 1])

            stepc = (maxc - minc) / (nc - 1.0)
            gc = minc + np.arange(nc, dtype=np.float64) * stepc  # (nc,)

            # Vectorized over (i4, i5, i8)
            # sav[i4] = gcash[i3] - gc[i4], shape (nc,)
            sav = gcash[i3] - gc  # (nc,)

            # cash_1[i5, i8, i4] = riskret[i5, i8] * sav[i4] + ret_fac
            # shape: (na, n, nc)
            cash_1 = (riskret[:, :, None] * sav[None, None, :]
                      + ret_fac)
            cash_1 = np.clip(cash_1, gcash[0], gcash[-1])

            # Batch spline evaluation: shape (na, n, nc)
            int_V = f_sc_splint_vec(gcash, V[:, t + 1], secd, ncash,
                                    cash_1.ravel()).reshape(na, n, nc)

            # auxVV[i5, i4] = sum_i8 weig[i8] * survprob[t] * int_V[i5,i8,i4]^(1-rho)
            auxVV = np.sum(weig[None, :, None] * survprob[t]
                           * (int_V ** (1.0 - rho)), axis=1)  # (na, nc)

            # u[i4] = (1-delta) * gc[i4]^psi_1, shape (nc,)
            u = (1.0 - delta) * (gc ** psi_1)

            # auxV[i5, i4] = (u[i4] + delta * auxVV[i5,i4]^(1/theta))^psi_2
            auxV = (u[None, :] + delta * (auxVV ** (1.0 / theta))) ** psi_2

            # Find maximum (column-major flatten to match MATLAB reshape)
            vec_V = auxV.flatten(order='F')
            pt = np.argmax(vec_V)
            V[i3, t] = vec_V[pt]

            aux2 = pt // na
            C[i3, t] = gc[aux2]
            A[i3, t] = ga[pt - na * aux2]

        secd = f_spline(gcash, V[:, t], ncash, 1.0)

    # -------------------------------------------------------------------
    # Working periods: t = tr-tb-1 downto 0 (0-based: 45 down to 0)
    # Triple loop over (i6, i8, i7) → n^3 = 125 shock combos
    # -------------------------------------------------------------------
    for t in range(p['tr'] - p['tb'] - 1, -1, -1):
        print(f"  Working period t={t} (age {t + p['tb']})")
        gyp_t = gyp[:, :, t]  # (n, n) = gyp[i6, i8]
        for i3 in range(ncash):
            # Determine consumption search bounds
            if i3 == 0:
                minc = gcash[0] / 5.0
                maxc = 0.999 * gcash[0]
            else:
                minc = C[i3 - 1, t]
                if i3 < 9:
                    maxc = minc + (gcash[i3] - gcash[i3 - 1])
                else:
                    mpc = max((C[i3 - 1, t] - C[i3 - 9, t])
                              / (gcash[i3 - 1] - gcash[i3 - 9]), 0.1)
                    maxc = minc + mpc * (gcash[i3] - gcash[i3 - 1])

            stepc = (maxc - minc) / (nc - 1.0)
            gc = minc + np.arange(nc, dtype=np.float64) * stepc

            sav = gcash[i3] - gc  # (nc,)

            # cash_1[i5, i6, i8, i7, i4] = riskret[i5,i8]*sav[i4]/gyp[i6,i8] + yh[i7,i8]
            # Shapes: riskret (na,n), sav (nc,), gyp_t (n,n), yh (n,n)
            # Build: (na, n, n, n, nc)
            # = riskret[i5,i8] * sav[i4] / gyp_t[i6,i8] + yh[i7,i8]
            #
            # riskret[i5,i8]: (na,1,n,1,1) → broadcast
            # sav[i4]: (1,1,1,1,nc) → broadcast
            # gyp_t[i6,i8]: (1,n,n,1,1) → broadcast
            # yh[i7,i8]: (1,1,n,n,1) → broadcast

            term1 = (riskret[:, None, :, None, None]
                     * sav[None, None, None, None, :]
                     / gyp_t[None, :, :, None, None])
            term2 = yh[None, None, :, :, None]  # yh[i7, i8] → dim 2=i8, dim 3=i7

            # Wait — MATLAB loop order is i6, i8, i7 and
            # yh(i7, i8): transitory income for node i7 given return node i8
            # gyp(i6, i8, t): permanent income growth for perm node i6, return node i8
            # riskret(i5, i8): portfolio return for alloc i5, return node i8
            # So the dimensions are:
            #   dim 0: i5 (na)
            #   dim 1: i6 (n) — permanent income growth
            #   dim 2: i8 (n) — return shock
            #   dim 3: i7 (n) — transitory income
            #   dim 4: i4 (nc) — consumption grid

            # Correction: yh[i7, i8] where i7 is first index, i8 is second
            # In our build_income, yh[i7, i1] where i1 is the conditioning return node
            # So yh[:, i8] gives transitory values for return node i8
            # Need yh[i7, i8] at dim 3=i7, dim 2=i8
            # → yh.T[i8, i7] or just yh[i7, i8] with proper broadcasting

            cash_1 = (riskret[:, None, :, None, None]       # (na, 1, n, 1, 1) [i5, -, i8, -, -]
                       * sav[None, None, None, None, :]     # (1, 1, 1, 1, nc)  [-, -, -, -, i4]
                       / gyp_t[None, :, :, None, None]      # (1, n, n, 1, 1)   [-, i6, i8, -, -]
                       + yh[None, None, :, :, None])         # (1, 1, n, n, 1)   [-, -, i8, i7, -]

            # Wait, yh is (n, n) indexed as yh[i7, i8].
            # yh[None, None, :, :, None] has shape (1,1,n,n,1)
            # At dim 2 we have the first index of yh = i7
            # At dim 3 we have the second index of yh = i8
            # But dim 2 should be i8 (return shock) and dim 3 should be i7 (transitory)
            # So we need yh transposed: yh.T[i8, i7]
            # yh.T[None, None, :, :, None] → dim 2 = i8, dim 3 = i7 ✓

            cash_1 = (riskret[:, None, :, None, None]
                       * sav[None, None, None, None, :]
                       / gyp_t[None, :, :, None, None]
                       + yh.T[None, None, :, :, None])

            cash_1 = np.clip(cash_1, gcash[0], gcash[-1])

            # Batch spline: (na * n * n * n * nc) evaluations
            shape = cash_1.shape
            int_V = f_sc_splint_vec(gcash, V[:, t + 1], secd, ncash,
                                    cash_1.ravel()).reshape(shape)

            # Weights: nweig1[i6, i7, i8] → broadcast to (1, n, n, n, 1)
            # gyp_t[i6, i8] → broadcast to (1, n, n, 1, 1)
            # Aggregation:
            # auxVV[i5, i4] = sum_{i6,i8,i7} nweig1[i6,i7,i8] * survprob[t]
            #                 * (int_V[i5,i6,i8,i7,i4] * gyp_t[i6,i8])^(1-rho)

            # nweig1 is (n, n, n) indexed as [i6, i7, i8]
            # We need it at dims (1, i6, i8, i7, 1)
            # nweig1[i6, i7, i8] → transpose to get [i6, i8, i7] at dims 1,2,3
            nw = nweig1.transpose(0, 2, 1)  # (n, n, n) now [i6, i8, i7]
            nw_bc = nw[None, :, :, :, None]  # (1, n, n, n, 1)

            gyp_bc = gyp_t[None, :, :, None, None]  # (1, n, n, 1, 1) [-, i6, i8, -, -]

            integrand = nw_bc * survprob[t] * ((int_V * gyp_bc) ** (1.0 - rho))
            auxVV = integrand.sum(axis=(1, 2, 3))  # sum over i6, i8, i7 → (na, nc)

            u = (1.0 - delta) * (gc ** psi_1)  # (nc,)
            auxV = (u[None, :] + delta * (auxVV ** (1.0 / theta))) ** psi_2

            vec_V = auxV.flatten(order='F')
            pt = np.argmax(vec_V)
            V[i3, t] = vec_V[pt]

            aux2 = pt // na
            C[i3, t] = gc[aux2]
            A[i3, t] = ga[pt - na * aux2]

        secd = f_spline(gcash, V[:, t], ncash, 1.0)

    return params, grids, survprob, income, C, A, V


# ---------------------------------------------------------------------------
# Bellman residual computation
# ---------------------------------------------------------------------------

def compute_bellman_residual(params, grids, survprob, income, C, A, V):
    """Re-evaluate the Bellman RHS at stored optimal policies.

    For each period t and grid point i3, compute:
      bellman_val = { (1-delta)*C[i3,t]^psi_1
                      + delta * [E_t(pi*V_{t+1}(x')^{1-rho})]^{1/theta} }^psi_2

    using the same spline interpolation and Gauss-Hermite quadrature as solve_model().

    Residual: r(i3, t) = V[i3, t] - bellman_val

    For a finite-horizon backward-induction solver, on-grid residuals should be
    ~machine epsilon since V[i3, t] was computed as the max of this same expression.

    Returns:
        residuals: ndarray (ncash, tn-1) — raw residuals (excludes terminal period)
        stats: dict with max_abs, mean_abs, median_abs, p95, p99,
               max_norm (normalized), mean_norm, acceptance_passed
    """
    p = params
    g = grids
    tn = p['tn']
    ncash = p['ncash']
    n = p['n']

    gcash = g['gcash']
    gret = g['gret']
    weig = g['weig']
    nweig1 = g['nweig1']
    gyp = income['gyp']
    yh = income['yh']

    delta = p['delta']
    rho = p['rho']
    psi_1 = p['psi_1']
    psi_2 = p['psi_2']
    theta = p['theta']
    r = p['r']
    ret_fac = p['ret_fac']

    t_retire_start = p['tr'] - p['tb']  # 46

    residuals = np.zeros((ncash, tn - 1), dtype=np.float64)

    for t in range(tn - 2, -1, -1):
        # Build spline of V_{t+1}
        secd = f_spline(gcash, V[:, t + 1], ncash, 1.0)

        c_opt = C[:, t]        # (ncash,)
        alpha_opt = A[:, t]    # (ncash,)
        sav = gcash - c_opt    # (ncash,)

        # Portfolio return for each (grid_point, return_shock)
        # port_ret[i3, i8] = r*(1-alpha) + gret[i8]*alpha
        port_ret = (r * (1.0 - alpha_opt[:, None])
                    + gret[None, :] * alpha_opt[:, None])  # (ncash, n)

        if t >= t_retire_start:
            # --- Retirement: only return shocks ---
            # cash_next[i3, i8] = port_ret[i3,i8] * sav[i3] + ret_fac
            cash_next = port_ret * sav[:, None] + ret_fac  # (ncash, n)
            cash_next = np.clip(cash_next, gcash[0], gcash[-1])

            v_next = f_sc_splint_vec(gcash, V[:, t + 1], secd, ncash,
                                     cash_next.ravel()).reshape(ncash, n)

            # auxVV[i3] = sum_i8 weig[i8] * survprob[t] * v_next[i3,i8]^(1-rho)
            auxVV = np.sum(weig[None, :] * survprob[t]
                           * (v_next ** (1.0 - rho)), axis=1)  # (ncash,)
        else:
            # --- Working: triple shocks (i6, i8, i7) ---
            gyp_t = gyp[:, :, t]  # (n, n) [i6, i8]

            # cash_next[i3, i6, i8, i7] = port_ret[i3,i8]*sav[i3]/gyp[i6,i8] + yh.T[i8,i7]
            cash_next = (port_ret[:, None, :, None]        # (ncash, 1, n, 1)
                         * sav[:, None, None, None]         # (ncash, 1, 1, 1)
                         / gyp_t[None, :, :, None]          # (1, n, n, 1)
                         + yh.T[None, None, :, :])          # (1, 1, n, n)
            # shape: (ncash, n, n, n) = [i3, i6, i8, i7]
            cash_next = np.clip(cash_next, gcash[0], gcash[-1])

            shape = cash_next.shape
            v_next = f_sc_splint_vec(gcash, V[:, t + 1], secd, ncash,
                                     cash_next.ravel()).reshape(shape)

            # nweig1[i6, i7, i8] transposed to [i6, i8, i7]
            nw = nweig1.transpose(0, 2, 1)  # (n, n, n) [i6, i8, i7]

            # integrand[i3, i6, i8, i7]
            integrand = (nw[None, :, :, :] * survprob[t]
                         * ((v_next * gyp_t[None, :, :, None]) ** (1.0 - rho)))
            auxVV = integrand.sum(axis=(1, 2, 3))  # (ncash,)

        # Bellman value
        u = (1.0 - delta) * (c_opt ** psi_1)  # (ncash,)
        bellman_val = (u + delta * (auxVV ** (1.0 / theta))) ** psi_2

        residuals[:, t] = V[:, t] - bellman_val

    # Compute statistics
    abs_res = np.abs(residuals)
    norm_res = abs_res / (1.0 + np.abs(V[:, :tn - 1]))

    ACCEPTANCE_TOL = 1e-10

    stats = {
        'max_abs': float(np.max(abs_res)),
        'mean_abs': float(np.mean(abs_res)),
        'median_abs': float(np.median(abs_res)),
        'p95_abs': float(np.percentile(abs_res, 95)),
        'p99_abs': float(np.percentile(abs_res, 99)),
        'max_norm': float(np.max(norm_res)),
        'mean_norm': float(np.mean(norm_res)),
        'median_norm': float(np.median(norm_res)),
        'p95_norm': float(np.percentile(norm_res, 95)),
        'p99_norm': float(np.percentile(norm_res, 99)),
        'acceptance_tol': ACCEPTANCE_TOL,
        'acceptance_passed': bool(np.max(norm_res) <= ACCEPTANCE_TOL),
    }

    return residuals, stats


# ---------------------------------------------------------------------------
# Simulation (life_cycle.m lines 405–498) — vectorized
# ---------------------------------------------------------------------------

def simulate(params, grids, survprob, income, C, A, seed=42):
    """Forward Monte Carlo simulation with antithetic variates."""
    p = params
    g = grids
    tn = p['tn']
    nsim = p['nsim']
    ncash = p['ncash']
    tb = p['tb']
    tr = p['tr']
    r = p['r']
    mu = p['mu']
    sigr = p['sigr']
    smav = p['smav']
    smay = p['smay']
    ret_fac = p['ret_fac']
    gcash = g['gcash']
    lgcash = g['lgcash']
    gy = income['gy']

    rng = np.random.default_rng(seed)
    half = nsim // 2

    # Pre-generate all random draws
    # Permanent income: one per (half-sim, working-period)
    n_work = tr - tb  # 46
    eps_perm = rng.standard_normal((n_work, half))  # period 0..45
    eps_trans = rng.standard_normal((n_work, half))
    eps_ret = rng.standard_normal((tn, half))

    # --- Permanent income and income growth ---
    simPY = np.zeros((tn, nsim), dtype=np.float64)
    simGPY = np.ones((tn, nsim), dtype=np.float64)
    simY = np.ones((tn, nsim), dtype=np.float64)

    # Period 0
    simPY[0, :half] = eps_perm[0] * smav
    simPY[0, half:] = -eps_perm[0] * smav
    # simGPY[0,:] already 1.0
    simY[0, :half] = np.exp(eps_trans[0] * smay)
    simY[0, half:] = np.exp(-eps_trans[0] * smay)

    # Working periods 1..n_work-1
    for i2 in range(1, n_work):
        simPY[i2, :half] = eps_perm[i2] * smav + simPY[i2 - 1, :half]
        simPY[i2, half:] = -eps_perm[i2] * smav + simPY[i2 - 1, :half]
        simGPY[i2, :half] = (np.exp(gy[i2 - 1])
                             * np.exp(simPY[i2, :half])
                             / np.exp(simPY[i2 - 1, :half]))
        simGPY[i2, half:] = (np.exp(gy[i2 - 1])
                             * np.exp(simPY[i2, half:])
                             / np.exp(simPY[i2 - 1, half:]))
        simY[i2, :half] = np.exp(eps_trans[i2] * smay)
        simY[i2, half:] = np.exp(-eps_trans[i2] * smay)

    # Retirement
    for t_idx in range(tr - tb, tn):
        simY[t_idx, :] = ret_fac
        simGPY[t_idx, :] = 1.0

    # Stock returns
    simR = np.zeros((tn, nsim), dtype=np.float64)
    simR[:, :half] = mu + r + sigr * eps_ret
    simR[:, half:] = mu + r - sigr * eps_ret

    # --- Forward simulation (vectorized per period) ---
    simW = np.zeros((tn, nsim), dtype=np.float64)
    simC = np.zeros((tn, nsim), dtype=np.float64)
    simA = np.zeros((tn, nsim), dtype=np.float64)
    simS = np.zeros((tn, nsim), dtype=np.float64)
    simB = np.zeros((tn, nsim), dtype=np.float64)
    simW_Y = np.zeros((tn, nsim), dtype=np.float64)

    for t in range(tn):
        simW_Y[t, :] = simW[t, :] / simY[t, :]
        cash = simW[t, :] + simY[t, :]
        log_cash = np.log(cash)

        # Vectorized grid lookup
        ic1 = f_ntoil_vec(log_cash, lgcash, ncash)
        ic2 = ic1 + 1
        ttc = (cash - gcash[ic1]) / (gcash[ic2] - gcash[ic1])
        ttc = np.clip(ttc, 0.0, 1.0)

        simC[t, :] = (1.0 - ttc) * C[ic1, t] + ttc * C[ic2, t]
        simA[t, :] = (1.0 - ttc) * A[ic1, t] + ttc * A[ic2, t]
        simC[t, :] = np.minimum(simC[t, :], 0.9999 * cash)
        sav = cash - simC[t, :]
        simS[t, :] = simA[t, :] * sav
        simS[t, :] = np.minimum(simS[t, :], sav)
        simB[t, :] = sav - simS[t, :]
        if t < tn - 1:
            simW[t + 1, :] = ((simB[t, :] * r + simS[t, :] * simR[t, :])
                              / simGPY[t + 1, :])

    # --- Compute means ---
    meanC = simC.mean(axis=1)
    meanY = simY.mean(axis=1)
    meanW = simW.mean(axis=1)
    meanS = simS.mean(axis=1)
    meanB = simB.mean(axis=1)
    meanWY = simW_Y.mean(axis=1)
    meanalpha = simA.mean(axis=1)
    meanGPY = simGPY.mean(axis=1)

    cGPY = np.zeros(tn, dtype=np.float64)
    cGPY[0] = 1.0
    for i2 in range(1, tn):
        cGPY[i2] = cGPY[i2 - 1] + (meanGPY[i2] - 1.0)

    meanCs = meanC * cGPY
    meanWs = meanW * cGPY
    meanYs = meanY * cGPY

    return {
        'meanC': meanC, 'meanW': meanW, 'meanY': meanY, 'meanGPY': meanGPY,
        'meanS': meanS, 'meanB': meanB, 'meanalpha': meanalpha,
        'meanCs': meanCs, 'meanWs': meanWs, 'meanYs': meanYs,
        'cGPY': cGPY, 'meanWY': meanWY,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
inputDict = {}

if __name__ == '__main__':
    import time
    print("Solving life-cycle model (vectorized)...")
    t0 = time.time()
    params, grids, survprob, income, C, A, V = solve_model(inputDict)
    t1 = time.time()
    print(f"Backward induction complete in {t1-t0:.1f}s.")
    print(f"  C shape: {C.shape}, A shape: {A.shape}, V shape: {V.shape}")
    print(f"  V[0, 0] = {V[0, 0]:.8f}, V[-1, -1] = {V[-1, -1]:.8f}")

    print("Running simulation...")
    t0 = time.time()
    sim = simulate(params, grids, survprob, income, C, A)
    t1 = time.time()
    print(f"Simulation complete in {t1-t0:.1f}s.")
    print(f"  Mean consumption at age 20: {sim['meanC'][0]:.8f}")
    print(f"  Mean wealth at age 65: {sim['meanW'][45]:.8f}")
