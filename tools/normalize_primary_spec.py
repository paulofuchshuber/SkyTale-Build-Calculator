import json
import os

ALL_CLASSES = "Mechanician Fighter Pikeman Archer Knight Atalanta Priestess Magician"

ITEMS_PATH = os.path.join(os.path.dirname(__file__), "..", "items.json")

with open(ITEMS_PATH, encoding="utf-8") as f:
    data = json.load(f)

updated = 0
for category in data.values():
    for item in category:
        spec = item.get("spec")
        if isinstance(spec, dict):
            spec["primaryClass"] = ALL_CLASSES
            updated += 1

with open(ITEMS_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Concluido: {updated} itens atualizados com primaryClass = \"{ALL_CLASSES}\".")
