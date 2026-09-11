import numpy as np
import pandas as pd

def fit_transform_scalars(df: pd.DataFrame, config: dict):
    """Apply log transforms and robust scaling, returning params and standardized df."""
    out_df = pd.DataFrame(index=df.index)
    params = {}
    
    tol = config['scaling']['fallback_to_sd_tolerance']
    
    for fam, f_config in config['families'].items():
        if f_config['type'] != 'scalar':
            continue
            
        t_type = f_config['transform']
        for col in f_config['columns']:
            # 1. Transform
            x = df[col].astype(float)
            if t_type == 'log':
                x_t = np.log(x)
            elif t_type == 'log1p':
                x_t = np.log1p(x)
            elif t_type == 'identity':
                x_t = x
            else:
                raise ValueError(f"Unknown transform {t_type}")
                
            # 2. Fit Scaling
            med = x_t.median()
            iqr = x_t.quantile(0.75) - x_t.quantile(0.25)
            
            used_sd = False
            scale = iqr
            
            effective_zero = tol * max(1.0, np.abs(x_t).max())
            
            if iqr <= effective_zero:
                used_sd = True
                scale = x_t.std(ddof=0)
                if scale <= effective_zero:
                    raise ValueError(f"Feature {col} is constant even after SD fallback.")
                    
            params[col] = {
                'transform': t_type,
                'median': med,
                'iqr': iqr,
                'sd_ddof0': x_t.std(ddof=0),
                'selected_scale': scale,
                'used_sd_fallback': used_sd
            }
            
            out_df[col] = (x_t - med) / scale
            
    return out_df, params

def transform_composition(df: pd.DataFrame, config: dict):
    """Normalize and sqrt transform composition features."""
    out_df = pd.DataFrame(index=df.index)
    
    for fam, f_config in config['families'].items():
        if f_config['type'] != 'composition':
            continue
            
        cols = f_config['columns']
        mat = df[cols].values
        
        sums = mat.sum(axis=1)
        if not np.allclose(sums, 1.0, atol=1e-8):
            raise ValueError(f"Composition {fam} does not sum to 1 within 1e-8")
            
        # Renormalize to exact 1 just in case, per plan "numerical residuals... may be renormalized"
        mat = mat / sums[:, np.newaxis]
        
        if (mat < 0).any():
            raise ValueError(f"Composition {fam} has negative values")
            
        sqrt_mat = np.sqrt(mat)
        
        for i, col in enumerate(cols):
            out_df[col] = sqrt_mat[:, i]
            
    return out_df
