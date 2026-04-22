from flask import Flask, render_template
import json
import os
from PIL import Image

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
        {'name': 'Arma 2', 'categories': ['machados', 'garras', 'varinhas', 'foices', 'lancas', 'arcos', 'martelos', 'espadas']},
        {'name': 'Armadura', 'categories': ['armaduras', 'roupoes']},
        {'name': 'Arma 1', 'categories': ['machados', 'garras', 'varinhas', 'foices', 'lancas', 'arcos', 'martelos', 'espadas']},
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
                    items_map[asset] = item
            except Exception:
                continue

    # Calculate max width/height per slot from the actual image files
    slot_sizes = {}
    for slot in slots:
        max_w = 0
        max_h = 0
        # iterate through all items in grouped categories
        for cat, items in slot_items[slot['name']].items():
            for item in items:
                try:
                    asset = item.get('assets', {}).get('assetFile') if isinstance(item, dict) else None
                    if not asset:
                        continue
                    # asset paths in JSON are like 'assets/items/itda102.bmp'
                    rel = asset
                    if rel.startswith('assets/'):
                        rel = rel[len('assets/'):]
                    if rel.startswith('/'):
                        rel = rel.lstrip('/')
                    img_path = os.path.join(app.static_folder, rel)
                    if not os.path.isfile(img_path):
                        continue
                    with Image.open(img_path) as im:
                        w, h = im.size
                        if w > max_w:
                            max_w = w
                        if h > max_h:
                            max_h = h
                except Exception:
                    continue
        if max_w == 0:
            max_w = 100
        if max_h == 0:
            max_h = 100
        slot_sizes[slot['name']] = {'w': max_w, 'h': max_h}

    return render_template('index.html', slots=slots, slot_items=slot_items, slot_sizes=slot_sizes, items_map=items_map)

if __name__ == '__main__':
    app.run(debug=True)