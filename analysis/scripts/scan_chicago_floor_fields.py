"""Scan local Chicago building, cadastral and workbook sources for floor/story fields; write non-null and positive counts to a JSON path given as argv[1]."""
import glob, json, re, sys
import pandas as pd, pyarrow.parquet as pq, pyogrio

PAT = re.compile(r"stor|floor|level|pavim|andar|pav\b|num_fl|height|elev", re.I)
C = "analysis/data/Chicago/"
out = []

def summarize(name, df, cols):
    for c in cols:
        s = df[c]
        num = pd.to_numeric(s, errors="coerce")
        vc = s.dropna().astype(str).value_counts().head(8).to_dict()
        out.append(dict(source=name, field=c, rows=len(s), non_null=int(s.notna().sum()),
                        positive_numeric=int((num > 0).sum()), top_values=vc))

# Parquet sources (Cook, DuPage, benchmarking, Overture)
for d in sorted(glob.glob(C + "chicago_cadastral_2026_09_18/*/")) + [C + "overture_2026_08_19/building/"]:
    files = sorted(glob.glob(d + "*.parquet"))
    if not files: continue
    cols = pq.read_schema(files[0]).names
    hit = [c for c in cols if PAT.search(c)]
    extra = [c for c in ("year", "tax_year", "class") if c in cols]
    print(d, "fields matching:", hit, file=sys.stderr)
    if not hit: out.append(dict(source=d, field=None, all_columns=cols)); continue
    df = pd.concat(pq.read_table(f, columns=hit + extra).to_pandas() for f in files)
    summarize(d, df, hit)
    if "year" in df and hit:
        for c in hit:
            out.append(dict(source=d, field=c, by_year=df.groupby("year")[c].apply(lambda s: int(pd.to_numeric(s, errors='coerce').gt(0).sum())).to_dict()))

# Large GeoJSON: read only matching attribute columns, no geometry
for f in [C + "Building_Footprints_20260915.geojson", C + "Building_Permits_20260915.geojson"]:
    cols = pyogrio.read_info(f)["fields"].tolist()
    hit = [c for c in cols if PAT.search(c)]
    print(f, "fields matching:", hit, file=sys.stderr)
    if hit:
        df = pyogrio.read_dataframe(f, columns=hit, read_geometry=False)
        summarize(f, df, hit)
    else:
        out.append(dict(source=f, field=None, all_columns=cols))

# Workbook text extracts and XLSX headers
recs = [json.loads(l) for l in open(C + "chicago_workbooks_2026_09_19/chicago_detail_records.jsonl")]
keys = sorted({k for r in recs for k in (r.get("fields") or r).keys()})
out.append(dict(source="workbook_jsonl", matching_keys=[k for k in keys if PAT.search(k)], n_keys=len(keys)))
for x in sorted(glob.glob(C + "manual_acquisition_2026_09_21/incoming/*.xlsx")):
    for sheet, df in pd.read_excel(x, sheet_name=None, header=None, nrows=15).items():
        cells = {str(v) for v in df.values.ravel() if isinstance(v, str) and PAT.search(v)}
        out.append(dict(source=x.split("/")[-1], sheet=sheet, matching_header_cells=sorted(cells)))

json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
