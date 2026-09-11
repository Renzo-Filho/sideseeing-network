import numpy as np
import pandas as pd

def compute_distances(scalar_df: pd.DataFrame, comp_df: pd.DataFrame, config: dict):
    """Compute pairwise family distances, calibration, and overall distance."""
    n = len(scalar_df)
    dist_matrices = {}
    calibrations = {}
    
    for fam, f_config in config['families'].items():
        cols = f_config['columns']
        mat = np.zeros((n, n))
        
        if f_config['type'] == 'scalar':
            data = scalar_df[cols].values
            k = len(cols)
            for i in range(n):
                for j in range(n):
                    mat[i, j] = np.sum((data[i] - data[j])**2) / k
        elif f_config['type'] == 'composition':
            data = comp_df[cols].values
            for i in range(n):
                for j in range(n):
                    mat[i, j] = 0.5 * np.sum((data[i] - data[j])**2)
                    
        dist_matrices[fam] = mat
        
        # Calibration (median of strictly positive distances)
        pos_dists = mat[np.triu_indices(n, k=1)]
        pos_dists = pos_dists[pos_dists > 0]
        if len(pos_dists) == 0:
            raise ValueError(f"No positive distances for family {fam}")
            
        b_f = np.median(pos_dists)
        if b_f <= 1e-12:
            raise ValueError(f"Numerically negligible calibration for {fam}")
            
        calibrations[fam] = b_f
        
    # Overall distance
    total_dist = np.zeros((n, n))
    contributions = {fam: np.zeros((n, n)) for fam in config['families']}
    
    for fam, f_config in config['families'].items():
        w_f = f_config['weight'] / 13.0  # Equal weight default
        c_mat = w_f * dist_matrices[fam] / calibrations[fam]
        contributions[fam] = c_mat
        total_dist += c_mat
        
    total_dist = np.sqrt(total_dist)
    
    return total_dist, dist_matrices, calibrations, contributions
