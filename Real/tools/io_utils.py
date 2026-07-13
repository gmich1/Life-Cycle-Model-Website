"""
io_utils.py — Parse MATLAB .txt output files into structured dicts.
"""
import os
import numpy as np


def parse_year_file(filepath):
    """Parse a yearXX.txt file.
    Format: 3 blocks of ncash=51 rows, 2 columns each.
      Block 1: A(i,t), gcash(i)   — portfolio allocation
      Block 2: C(i,t), gcash(i)   — consumption
      Block 3: V(i,t), gcash(i)   — value function
    Returns dict with keys: 'A', 'C', 'V', 'gcash'.
    """
    data = np.loadtxt(filepath, dtype=np.float64)
    ncash = 51
    assert data.shape == (3 * ncash, 2), (
        f"Expected {3*ncash} rows x 2 cols, got {data.shape} in {filepath}")

    return {
        'A': data[:ncash, 0],
        'C': data[ncash:2*ncash, 0],
        'V': data[2*ncash:3*ncash, 0],
        'gcash': data[:ncash, 1],
    }


def parse_cwy_file(filepath):
    """Parse CWY.txt → 81 rows × 4 columns (meanC, meanW, meanY, meanGPY)."""
    data = np.loadtxt(filepath, dtype=np.float64)
    assert data.shape[1] == 4, f"Expected 4 columns, got {data.shape[1]}"
    return {
        'meanC': data[:, 0],
        'meanW': data[:, 1],
        'meanY': data[:, 2],
        'meanGPY': data[:, 3],
    }


def parse_cwys_file(filepath):
    """Parse CWYs.txt → 81 rows × 3 columns (meanCs, meanWs, meanYs)."""
    data = np.loadtxt(filepath, dtype=np.float64)
    assert data.shape[1] == 3, f"Expected 3 columns, got {data.shape[1]}"
    return {
        'meanCs': data[:, 0],
        'meanWs': data[:, 1],
        'meanYs': data[:, 2],
    }


def parse_sb_file(filepath):
    """Parse SB.txt → 81 rows × 3 columns (meanS, meanB, meanalpha)."""
    data = np.loadtxt(filepath, dtype=np.float64)
    assert data.shape[1] == 3, f"Expected 3 columns, got {data.shape[1]}"
    return {
        'meanS': data[:, 0],
        'meanB': data[:, 1],
        'meanalpha': data[:, 2],
    }


def load_all_matlab_outputs(data_dir):
    """Load all MATLAB outputs from data_dir (which contains Life_Cycle_Matlab/).
    Returns nested dict:
      {'years': {1: {'A':..,'C':..,'V':..,'gcash':..}, ..., 80: {...}},
       'CWY': {...}, 'CWYs': {...}, 'SB': {...}}
    """
    matlab_dir = os.path.join(data_dir, 'Life_Cycle_Matlab')
    if not os.path.isdir(matlab_dir):
        matlab_dir = data_dir

    result = {'years': {}}

    # Year files
    for t in range(1, 81):
        fname = f'year{t:02d}.txt'
        fpath = os.path.join(matlab_dir, fname)
        if os.path.exists(fpath):
            result['years'][t] = parse_year_file(fpath)

    # Simulation files
    cwy_path = os.path.join(matlab_dir, 'CWY.txt')
    if os.path.exists(cwy_path):
        result['CWY'] = parse_cwy_file(cwy_path)

    cwys_path = os.path.join(matlab_dir, 'CWYs.txt')
    if os.path.exists(cwys_path):
        result['CWYs'] = parse_cwys_file(cwys_path)

    sb_path = os.path.join(matlab_dir, 'SB.txt')
    if os.path.exists(sb_path):
        result['SB'] = parse_sb_file(sb_path)

    return result
