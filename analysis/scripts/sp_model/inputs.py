import json
import hashlib
import pandas as pd
from pathlib import Path
import sys
import pkg_resources

def hash_file(path: Path) -> str:
    """Return SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def freeze_inputs(config_path: str, base_dir: Path):
    """Load config, validate inputs, and return manifest and data."""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    paths = config['paths']
    primary_path = base_dir / paths['primary_attributes']
    
    # Check paths exist
    for p in paths.values():
        if not (base_dir / p).exists():
            raise FileNotFoundError(f"Required input not found: {p}")
            
    # Read primary attributes
    df = pd.read_csv(primary_path, dtype={'district_id': str})
    
    # 96 unique IDs
    if len(df) != 96 or df['district_id'].nunique() != 96:
        raise ValueError(f"Expected exactly 96 unique districts, found {len(df)}")
        
    # Brás found
    if config['target_district_id'] not in df['district_id'].values:
        raise ValueError(f"Target district {config['target_district_id']} not found in primary attributes.")
        
    # Check 23 primary columns
    expected_cols = []
    families = config['families']
    if len(families) != 13:
        raise ValueError(f"Expected 13 families in config, found {len(families)}")
        
    for fam, f_config in families.items():
        expected_cols.extend(f_config['columns'])
        
    if len(expected_cols) != 23:
        raise ValueError(f"Expected 23 primary columns across families, found {len(expected_cols)}")
        
    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Expected primary column {col} not found in attributes.")
            
    # Check finite primary values
    if df[expected_cols].isna().any().any():
        raise ValueError("Null values found in primary columns.")
        
    # Create hash manifest
    manifest = {
        "config_hash": hash_file(Path(config_path)),
        "inputs": {name: hash_file(base_dir / p) for name, p in paths.items()},
        "environment": {
            "python_version": sys.version,
            "pandas_version": pkg_resources.get_distribution("pandas").version,
        }
    }
    
    return config, df, manifest

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent.parent
    conf, df, manifest = freeze_inputs(base / "config/sp_urban_model_v1.json", base)
    print("N11.01 Freeze Inputs Success")
    print(json.dumps(manifest, indent=2))

