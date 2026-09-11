import json
import pandas as pd
import numpy as np
from pathlib import Path
from sp_model.inputs import freeze_inputs
from sp_model.transforms import fit_transform_scalars, transform_composition
from sp_model.distances import compute_distances

def run_model():
    base = Path(__file__).resolve().parent.parent
    config_path = base / "config/sp_urban_model_v1.json"
    
    # N11.01
    config, df, manifest = freeze_inputs(config_path, base)
    df.set_index('district_id', inplace=True)
    district_ids = df.index.tolist()
    
    # N11.03 Transforms
    scalar_df, transform_params = fit_transform_scalars(df, config)
    comp_df = transform_composition(df, config)
    
    # Save intermediates
    out_dir = base / "work" / "runs" / "sp_urban_model_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "transform_params.json", "w") as f:
        json.dump(transform_params, f, indent=2)
        
    # N11.04 & N11.05 Distances & Score
    total_dist, dist_mats, calibrations, contribs = compute_distances(scalar_df, comp_df, config)
    
    dist_df = pd.DataFrame(total_dist, index=district_ids, columns=district_ids)
    
    # N11.06 Ranking for Brás
    bras_id = config['target_district_id']
    bras_idx = district_ids.index(bras_id)
    
    bras_dists = dist_df.loc[bras_id].copy()
    bras_dists = bras_dists.drop(bras_id) # Drop self
    
    # Rank ascending
    ranks = bras_dists.rank(method='min').astype(int) # Competition rank
    
    # Tie breaking with ID
    # Since rank is competition, we can just sort by distance, then ID
    res = pd.DataFrame({'distance': bras_dists, 'rank': ranks})
    res.index.name = 'district_id'
    res = res.reset_index().sort_values(['distance', 'district_id'])
    
    res.to_csv(out_dir / "bras_ranking.csv", index=False)
    
    print("Top 10 most similar to Brás:")
    print(res.head(10))
    
    # Save full distance matrix
    res_dir = base / "results/SP/models/sp_urban_model_v1/tables"
    res_dir.mkdir(parents=True, exist_ok=True)
    dist_df.to_csv(res_dir / "pairwise_distances.csv")
    res.to_csv(res_dir / "bras_ranking.csv", index=False)
    print(f"Results saved to {res_dir}")

if __name__ == "__main__":
    run_model()
