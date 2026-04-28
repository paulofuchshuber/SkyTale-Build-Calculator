import json
import pathlib

ITEMS_PATH = pathlib.Path(__file__).parent.parent / "items.json"
MAX_LEVEL = 100


def main():
    with open(ITEMS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    removed_total = 0

    for category, items in data.items():
        before = len(items)
        data[category] = [
            item for item in items
            if item.get("requirements", {}).get("level", 0) <= MAX_LEVEL
        ]
        removed = before - len(data[category])
        if removed:
            print(f"{category}: {removed} item(s) removido(s)")
        removed_total += removed

    with open(ITEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nTotal removido: {removed_total} item(s)")


if __name__ == "__main__":
    main()
