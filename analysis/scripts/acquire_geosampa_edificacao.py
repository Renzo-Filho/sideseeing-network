"""Download GeoSampa `geoportal:edificacao` (municipal photogrammetric building outlines) by WFS pages; resumable."""
import hashlib, json, re, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/data/SP/geosampa_edificacao_2026_10_05"
WFS = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows"
PAGE = 20000
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) sideseeing-network B1 validation"}
BASE = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": "geoportal:edificacao"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hits = requests.get(WFS, params={**BASE, "resultType": "hits"}, headers=UA, timeout=300).text
    total = int(re.search(r'numberMatched="(\d+)"', hits).group(1))
    pages = -(-total // PAGE)
    for k in range(pages):
        f = OUT / f"page_{k:04d}.zip"
        if f.exists() and f.stat().st_size > 0:
            continue
        params = {**BASE, "count": PAGE, "startIndex": k * PAGE, "sortBy": "cd_identificador", "outputFormat": "SHAPE-ZIP",
                  "propertyName": "cd_identificador,qt_area_projecao_beiral,qt_altura_edificacao,tx_escala,dt_criacao,dt_atualizacao,ge_poligono"}
        for attempt in range(5):
            try:
                r = requests.get(WFS, params=params, headers=UA, timeout=600)
                r.raise_for_status()
                assert r.content[:2] == b"PK", "not a zip"
                f.with_suffix(".part").write_bytes(r.content)
                f.with_suffix(".part").replace(f)
                break
            except Exception as e:
                print("retry", k, attempt, e, flush=True)
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f"page {k} failed")
        print("page", k + 1, "of", pages, flush=True)
    manifest = {"source": WFS, "layer": "geoportal:edificacao", "number_matched": total, "page_size": PAGE,
                "fetched": time.strftime("%Y-%m-%d"),
                "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(OUT.glob("page_*.zip"))}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("done", total, "features in", len(manifest["files"]), "pages")


if __name__ == "__main__":
    main()
