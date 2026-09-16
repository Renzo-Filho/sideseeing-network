import urllib.request
import json
import os

def download_chicago_community_areas():
    url = "https://data.cityofchicago.org/api/geospatial/cauq-8yn6?method=export&format=GeoJSON"
    output_path = "../data/CHI/raw/chicago_community_areas.geojson"
    
    print(f"Downloading Chicago Community Areas from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        with open(output_path, 'w') as f:
            json.dump(data, f)
        print(f"Successfully saved to {output_path}")
    except Exception as e:
        print(f"Error downloading data: {e}")

if __name__ == "__main__":
    download_chicago_community_areas()
