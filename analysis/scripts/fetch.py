import os
import requests
import json
from urllib.parse import urlencode

# ==========================================
# 1. DIRECTORY SETUP
# ==========================================

def create_directories():
    """Builds the nested directory structure for the 15-variable model."""
    cities = ['SP data', 'Chicago data']
    subfolders = [
        'boundaries',      # Primary spatial units
        'morphology',      # M1-M7: Streets, blocks, parcels, intersections
        'built_form',      # B1-B3: Building footprints, heights
        'functional',      # U1-U3: Land use, activity, population
        'transit',         # U4: Stations and stops
        'sidewalks'        # A1-A12: Pedestrian realm layers
    ]
    for city in cities:
        for sub in subfolders:
            os.makedirs(os.path.join(city, sub), exist_ok=True)

# ==========================================
# 2. DATA FETCHING FUNCTIONS
# ==========================================

def fetch_socrata(domain, dataset_id, filepath, limit=100000):
    """Fetches GeoJSON from Socrata portals (Chicago Data Portal, Cook County)."""
    url = f"https://{domain}/resource/{dataset_id}.geojson?$limit={limit}"
    print(f"Fetching Socrata data: {filepath}...")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f)
    except Exception as e:
        print(f"  [!] Failed to fetch {filepath}: {e}")

def fetch_wfs(layer_name, filepath, max_features=100000):
    """Fetches GeoJSON from GeoSampa Geoserver WFS."""
    base_url = "http://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geosampa/wfs"
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': f'geosampa:{layer_name}',
        'outputFormat': 'application/json',
        'maxFeatures': max_features
    }
    print(f"Fetching GeoSampa WFS: {filepath}...")
    try:
        response = requests.get(base_url, params=params, timeout=300)
        response.raise_for_status()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f)
    except Exception as e:
        print(f"  [!] Failed to fetch {filepath}: {e}")

def fetch_arcgis_rest(service_url, filepath):
    """Fetches data from ArcGIS REST endpoints (e.g., CMAP)."""
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'outSR': '4326'
    }
    url = f"{service_url}/query?{urlencode(params)}"
    print(f"Fetching ArcGIS REST data: {filepath}...")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f)
    except Exception as e:
        print(f"  [!] Failed to fetch {filepath}: {e}")

def fetch_us_census(state, county, filepath):
    """Fetches Chicago block group population from the U.S. Census API (ACS 5-Year)."""
    # Variables: B01003_001E (Total Population)
    url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME,B01003_001E&for=block%20group:*&in=state:{state}%20county:{county}"
    print(f"Fetching US Census data: {filepath}...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f)
    except Exception as e:
        print(f"  [!] Failed to fetch {filepath}: {e}")


# ==========================================
# 3. PIPELINE EXECUTION
# ==========================================

def main():
    create_directories()

    # --- CHICAGO DATA PORTAL & EXTERNAL (CMAP/Cook County) ---
    chicago_socrata = [
        # Boundaries
        ("data.cityofchicago.org", "igwz-8jzy", "Chicago data/boundaries/community_areas.geojson"),

        # Morphology (M1-M7)
        ("data.cityofchicago.org", "6imu-meau", "Chicago data/morphology/street_centerlines.geojson"),
        ("datacatalog.cookcountyil.gov", "c49d-89sn", "Chicago data/morphology/cook_county_parcels.geojson"), # Cook County Parcels

        # Built Form (B1-B3)
        ("data.cityofchicago.org", "hz9b-7nh8", "Chicago data/built_form/building_footprints.geojson"),

        # Functional Structure (U1-U5)
        ("data.cityofchicago.org", "uupf-x98q", "Chicago data/functional/active_businesses.geojson"),
        ("data.cityofchicago.org", "7cve-jgbp", "Chicago data/functional/zoning_districts.geojson"),

        # Transit
        ("data.cityofchicago.org", "8pix-ypme", "Chicago data/transit/cta_l_stops.geojson"),
        ("data.cityofchicago.org", "bynn-gwxy", "Chicago data/transit/cta_bus_stops.geojson")
    ]

    for domain, ds_id, path in chicago_socrata:
        fetch_socrata(domain, ds_id, path)

    # Chicago External APIs
    # CMAP Land Use (2018 is standard on their open data portal right now)
    cmap_land_use_url = "https://services3.arcgis.com/bWPjFyqg6BhzT2n2/arcgis/rest/services/Land_Use_Inventory_2018/FeatureServer/0"
    fetch_arcgis_rest(cmap_land_use_url, "Chicago data/functional/cmap_land_use.geojson")

    # Cook County Population (FIPS: State 17, County 031)
    fetch_us_census("17", "031", "Chicago data/functional/acs_population.json")

    # --- SAO PAULO GEOSAMPA (WFS) ---
    sp_wfs = [
        # Boundaries
        ("layer_distrito", "SP data/boundaries/distritos.geojson"),
        ("layer_subprefeitura", "SP data/boundaries/subprefeituras.geojson"),

        # Morphology (M1-M7)
        ("v_logradouro", "SP data/morphology/street_centerlines.geojson"),
        ("v_quadra", "SP data/morphology/quadras.geojson"),
        ("v_lote", "SP data/morphology/lotes_parcels.geojson"),
        ("v_classificacao_viaria", "SP data/morphology/road_classification.geojson"),

        # Built Form (B1-B3)
        ("v_edificacao", "SP data/built_form/building_footprints.geojson"),

        # Functional Structure (U1-U3)
        ("v_zoneamento", "SP data/functional/zoning.geojson"),
        ("v_cadastro_imobiliario", "SP data/functional/property_cadastre_landuse.geojson"), # Proxy for IPTU land use

        # Transit (U4)
        ("v_metro_estacao", "SP data/transit/metro_stations.geojson"),
        ("v_cptm_estacao", "SP data/transit/cptm_rail_stations.geojson"),
        ("v_parada_onibus", "SP data/transit/bus_stops.geojson"),

        # Sidewalks (A1-A12)
        ("v_calcada", "SP data/sidewalks/calcadas_inventory.geojson")
    ]

    for layer, path in sp_wfs:
        fetch_wfs(layer, path)

    print("\nData acquisition complete. Note: Some massive datasets (Parcels, Buildings) may hit API pagination limits.")

if __name__ == "__main__":
    main()
