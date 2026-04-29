from flask import Flask, render_template
import json
import os
from PIL import Image
from flask import request, jsonify
from utils.aggregate import aggregate_by_assets, apply_rarity_and_spec

app = Flask(__name__, static_folder='assets', static_url_path='/assets')

@app.route('/')
def index():
    with open('items.json', 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    # Organize items by category
    categories = {}
    for cat, items in items_data.items():
        categories[cat] = items
    
    # Define slots and their categories
    slots = [
        {'name': 'Arma', 'categories': ['machados', 'garras', 'varinhas', 'foices', 'lancas', 'arcos', 'martelos', 'espadas']},
        {'name': 'Armadura', 'categories': ['armaduras', 'roupoes']},
        # 'Arma 1' removed per request
        {'name': 'Escudo', 'categories': ['escudos', 'orbitais']},
        {'name': 'Bracelete', 'categories': ['braceletes']},
        {'name': 'Luvas', 'categories': ['luvas']},
        {'name': 'Botas', 'categories': ['botas']},
        {'name': 'Anel 1', 'categories': ['aneis']},
        {'name': 'Anel 2', 'categories': ['aneis']},
        {'name': 'Amuleto', 'categories': ['amuletos']}
    ]
    
    # For each slot, collect items grouped by category
    from collections import OrderedDict
    slot_items = {}
    for slot in slots:
        grouped = OrderedDict()
        for cat in slot['categories']:
            if cat in categories:
                grouped[cat] = categories[cat]
        slot_items[slot['name']] = grouped

    # Build a map of assetFile -> item for quick lookup in the frontend
    items_map = {}
    for cat, items in items_data.items():
        for item in items:
            try:
                asset = item.get('assets', {}).get('assetFile') if isinstance(item, dict) else None
                if asset:
                    # annotate item with its top-level category so frontend/backend can rely on it
                    if isinstance(item, dict):
                        item['_category'] = cat
                    items_map[asset] = item
            except Exception:
                continue

    # Calculate max width/height per slot from the actual image files
    slot_sizes = {}
    for slot in slots:
        max_w = 66
        max_h = 100
        slot_sizes[slot['name']] = {'w': max_w, 'h': max_h}

    return render_template('index.html', slots=slots, slot_items=slot_items, slot_sizes=slot_sizes, items_map=items_map)


@app.route('/aggregate', methods=['POST'])
def aggregate():
    data = request.get_json() or {}
    assets = data.get('assets', [])
    with open('items.json', 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    # flatten items map
    items_map = {}
    for cat, items in items_data.items():
        if isinstance(items, list):
            for item in items:
                asset = item.get('assets', {}).get('assetFile') if isinstance(item, dict) else None
                if asset:
                    if isinstance(item, dict):
                        item['_category'] = cat
                    items_map[asset] = item

    # assets can be list of assetFile strings or objects {asset, rarity, spec}
    selected = []
    for a in assets:
        if isinstance(a, str):
            if a in items_map:
                selected.append(items_map[a])
        elif isinstance(a, dict):
            asset = a.get('asset') or a.get('assets') or a.get('assetFile')
            if not asset or asset not in items_map:
                continue
            base = items_map[asset]
            rarity = a.get('rarity', 'normal')
            spec = a.get('spec') or None
            aging = a.get('aging', 0) or 0
            try:
                aging = int(aging)
            except Exception:
                aging = 0
            selected.append(apply_rarity_and_spec(base, rarity=rarity, spec=spec, aging=aging))

    selected_class = data.get('selected_class') or None
    result = aggregate_by_assets(selected, selected_class=selected_class)
    return jsonify(result)

if __name__ == '__main__':
    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 10000))
    )