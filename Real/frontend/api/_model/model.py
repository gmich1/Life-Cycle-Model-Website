"""
model.py — Core model parameters, grids, and income process.
Direct translation of life_cycle.m lines 1–258.
Gomes (2020) / Cocco-Gomes-Maenhout (2005) life-cycle portfolio choice model.
"""
import numpy as np

INT_FIELDS = ['tb', 'tr', 'td', 'na', 'ncash', 'nc', 'n', 'nsim']

def build_params(userInputs):
    """All scalar parameters from life_cycle.m lines 9–35."""
    p = {}
    p.update(userInputs)

    for key in INT_FIELDS: # cheeky casting to integer
        p[key] = int(p[key])

    # p['tb'] = 20          # starting age
    # p['tr'] = 66          # retirement age
    # p['td'] = 100         # maximum age
    p['tn'] = p['td'] - p['tb'] + 1  # 81 periods

    # p['na'] = 51          # portfolio allocation grid size
    # p['ncash'] = 51       # cash-on-hand grid size
    # p['n'] = 5            # Gauss-Hermite quadrature nodes
    # p['nc'] = 21          # consumption search grid size

    # p['maxcash'] = 200.0
    # p['mincash'] = 0.25
    # p['aa'] = -2.170042 + 2.700381
    # p['b1'] = 0.16818
    # p['b2'] = -0.0323371 / 10
    # p['b3'] = 0.0019704 / 100
    # p['ret_fac'] = 0.68212
    # p['smay'] = 0.1       # std dev transitory income shocks
    # p['smav'] = 0.1       # std dev permanent income shocks
    # p['corr_v'] = 0.0     # correlation permanent income / returns
    # p['corr_y'] = 0.0     # correlation transitory income / returns
    # p['rho'] = 10.0       # relative risk aversion (RRA)
    # p['delta'] = 0.97     # subjective discount factor
    # p['psi'] = 0.5        # elasticity of intertemporal substitution (EIS)
    # p['r'] = 1.015        # gross risk-free rate
    # p['mu'] = 0.04        # equity premium
    # p['sigr'] = 0.2       # std dev of stock returns

    # Derived preference parameters
    p['theta'] = (1.0 - p['rho']) / (1.0 - 1.0 / p['psi'])
    p['psi_1'] = 1.0 - 1.0 / p['psi']   # = -1.0 for psi=0.5
    p['psi_2'] = 1.0 / p['psi_1']        # = -1.0 for psi=0.5

    # p['nsim'] = 10000     # number of simulation paths

    return p


def build_survival_probs():
    """Conditional survival probabilities from life_cycle.m lines 103–182.
    Returns array of shape (80,) — survprob[t] for t=0..79 (periods 1..80 in MATLAB).
    """
    sp = np.array([
        0.99845, 0.99839, 0.99833, 0.9983,  0.99827,
        0.99826, 0.99824, 0.9982,  0.99813, 0.99804,
        0.99795, 0.99785, 0.99776, 0.99766, 0.99755,
        0.99743, 0.9973,  0.99718, 0.99707, 0.99696,
        0.99685, 0.99672, 0.99656, 0.99635, 0.9961,
        0.99579, 0.99543, 0.99504, 0.99463, 0.9942,
        0.9937,  0.99311, 0.99245, 0.99172, 0.99091,
        0.99005, 0.98911, 0.98803, 0.9868,  0.98545,
        0.98409, 0.9827,  0.98123, 0.97961, 0.97786,
        0.97603, 0.97414, 0.97207, 0.9697,  0.96699,
        0.96393, 0.96055, 0.9569,  0.9531,  0.94921,
        0.94508, 0.94057, 0.9357,  0.93031, 0.92424,
        0.91717, 0.90922, 0.90089, 0.89282, 0.88503,
        0.87622, 0.86576, 0.8544,  0.8423,  0.82942,
        0.8154,  0.80002, 0.78404, 0.76842, 0.75382,
        0.73996, 0.72464, 0.71057, 0.6961,  0.6809,
    ], dtype=np.float64)
    return sp


def build_grids(params):
    """Build all grids from life_cycle.m lines 87–219.
    Returns dict with: grid, weig, gcash, lgcash, ga, gret, riskret, nweig1.
    """
    p = params
    g = {}

    # Gauss-Hermite quadrature nodes and weights (5-point)
    # life_cycle.m lines 89–99
    g['grid'] = np.array([
        -2.85697001387280,
        -1.35562617997427,
         0.00000000000000,
         1.35562617997426,
         2.85697001387280,
    ], dtype=np.float64)

    g['weig'] = np.array([
        0.01125741132772,
        0.22207592200561,
        0.53333333333333,
        0.22207592200561,
        0.01125741132772,
    ], dtype=np.float64)

    # Gross return on risky asset for each quadrature node
    # life_cycle.m lines 194–196: gret(i) = r + mu + grid(i)*sigr
    g['gret'] = p['r'] + p['mu'] + g['grid'] * p['sigr']

    # Triple weight product: nweig1[i6,i7,i8] = weig[i6]*weig[i7]*weig[i8]
    # life_cycle.m lines 198–204
    n = p['n']
    g['nweig1'] = (g['weig'][:, None, None]
                   * g['weig'][None, :, None]
                   * g['weig'][None, None, :])

    # Portfolio allocation grid: ga[i] = (na-1-i)/(na-1), from 1.0 down to 0.0
    # life_cycle.m lines 211–213: ga(i1) = (na-i1)/(na-1)
    na = p['na']
    g['ga'] = np.array([(na - 1 - i) / (na - 1.0) for i in range(na)], dtype=np.float64)

    # Portfolio return for each (allocation, return-shock) pair
    # life_cycle.m lines 215–219: riskret(i5,i8) = r*(1-ga(i5)) + gret(i8)*ga(i5)
    g['riskret'] = (p['r'] * (1.0 - g['ga'][:, None])
                    + g['gret'][None, :] * g['ga'][:, None])

    # Cash-on-hand grid (log-spaced)
    # life_cycle.m lines 221–230
    l_maxcash = np.log(p['maxcash'])
    l_mincash = np.log(p['mincash'])
    ncash = p['ncash']
    stepcash = (l_maxcash - l_mincash) / (ncash - 1.0)

    g['lgcash'] = np.array([l_mincash + i * stepcash for i in range(ncash)], dtype=np.float64)
    g['gcash'] = np.exp(g['lgcash'])

    return g


def build_income(params, grids):
    """Build income process arrays from life_cycle.m lines 232–258.
    Returns dict with: yh, yp, f_y, gy, gyp.
    """
    p = params
    g = grids
    inc = {}
    n = p['n']
    tb = p['tb']
    tr = p['tr']
    tn = p['tn']
    grid = g['grid']

    # Transitory income shocks: yh[i7, i1] = exp(grid2[i7] * smay)
    # life_cycle.m lines 233–236
    # grid2 = grid[i1]*corr_y + grid[:] * sqrt(1 - corr_y^2)
    corr_y = p['corr_y']
    yh = np.zeros((n, n), dtype=np.float64)
    for i1 in range(n):
        grid2 = grid[i1] * corr_y + grid * np.sqrt(1.0 - corr_y**2)
        yh[:, i1] = np.exp(grid2 * p['smay'])

    # Permanent income shocks: yp[i, i1] = grid2[i] * smav
    # life_cycle.m lines 238–241
    corr_v = p['corr_v']
    yp = np.zeros((n, n), dtype=np.float64)
    for i1 in range(n):
        grid2 = grid[i1] * corr_v + grid * np.sqrt(1.0 - corr_v**2)
        yp[:, i1] = grid2 * p['smav']

    # Deterministic income profile: f_y[i] = exp(aa + b1*age + b2*age^2 + b3*age^3)
    # life_cycle.m lines 243–245: for i1=tb:tr → f_y(i1-tb+1)
    n_work = tr - tb + 1   # 47 values (ages 20 to 66)
    f_y = np.zeros(n_work, dtype=np.float64)
    for i in range(n_work):
        age = tb + i        # age = 20, 21, ..., 66
        f_y[i] = np.exp(p['aa'] + p['b1'] * age + p['b2'] * age**2 + p['b3'] * age**3)

    # Income growth rate: gy[i] = f_y[i+1]/f_y[i] - 1
    # life_cycle.m lines 247–248: for i1=tb:tr-1
    n_growth = tr - tb      # 46 values
    gy = np.zeros(n_growth, dtype=np.float64)
    for i in range(n_growth):
        gy[i] = f_y[i + 1] / f_y[i] - 1.0

    # Permanent income growth factor: gyp[i6, i2, t]
    # life_cycle.m lines 249–258
    # Working periods (t=0..tr-tb-1, i.e., 0..45): gyp[:,i2,t] = exp(gy[t] + yp[:,i2])
    # Retirement periods (t=tr-tb..tn-2, i.e., 46..79): gyp = exp(0) = 1.0
    gyp = np.ones((n, n, tn - 1), dtype=np.float64)
    for t in range(n_growth):  # t = 0..45 (working periods)
        for i2 in range(n):
            gyp[:, i2, t] = np.exp(gy[t] * np.ones(n) + yp[:, i2])
    # Retirement periods already 1.0 from initialization

    inc['yh'] = yh
    inc['yp'] = yp
    inc['f_y'] = f_y
    inc['gy'] = gy
    inc['gyp'] = gyp

    return inc
