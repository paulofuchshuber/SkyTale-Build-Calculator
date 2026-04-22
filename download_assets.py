import json
import os
import requests
from urllib.parse import urljoin

base_url = "https://skytale.com.br/"
json_file = 'items.json'

def find_assets(obj):
    assets = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'assetFile':
                assets.append(value)
            else:
                assets.extend(find_assets(value))
    elif isinstance(obj, list):
        for item in obj:
            assets.extend(find_assets(item))
    return assets

# Load JSON
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find all assetFile paths
assets = find_assets(data)
unique_assets = list(set(assets))  # Remove duplicates if any

print(f"Found {len(unique_assets)} unique assets to download.")

# Download each asset

# Define um User-Agent de navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

for asset in unique_assets:
    url = urljoin(base_url, asset)
    # Remove the leading 'assets/' from asset path for local storage
    if asset.startswith('assets/'):
        local_relative_path = asset[len('assets/'):]
    else:
        local_relative_path = asset
    local_path = os.path.join('assets', local_relative_path)
    # Create directories if needed
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    # Check if file already exists
    if os.path.exists(local_path):
        #print(f"Skipped (already exists): {asset}")
        continue
    try:
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {asset}")
        else:
            print(f"Failed to download {asset}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading {asset}: {e}")

print("Download process completed.")