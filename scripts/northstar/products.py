"""Product catalog generation (BACKLOG.md 2.3, DATASET.md §9)."""
import random
from typing import Any

from northstar.config import GeneratorConfig
from northstar.ids import product_id

# category -> (unit_price range, name adjectives, name nouns)
CATEGORIES: dict[str, dict[str, Any]] = {
    "headphones": {
        "price_range": (29.0, 249.0),
        "adjectives": ["Wireless", "Noise-Cancelling", "Studio", "Sport", "Bass+"],
        "nouns": ["Headphones", "Earbuds", "Over-Ear Set", "In-Ear Buds"],
    },
    "keyboards": {
        "price_range": (19.0, 179.0),
        "adjectives": ["Mechanical", "Compact", "Wireless", "Backlit", "Low-Profile"],
        "nouns": ["Keyboard", "Keypad", "TKL Keyboard"],
    },
    "mice": {
        "price_range": (9.0, 99.0),
        "adjectives": ["Wireless", "Ergonomic", "Gaming", "Silent", "Compact"],
        "nouns": ["Mouse", "Trackball Mouse", "Vertical Mouse"],
    },
    "chargers": {
        "price_range": (12.0, 79.0),
        "adjectives": ["Fast", "USB-C", "Wireless", "Dual-Port", "Compact"],
        "nouns": ["Charger", "Power Bank", "Charging Dock"],
    },
    "smart_home": {
        "price_range": (24.0, 199.0),
        "adjectives": ["Smart", "Voice-Controlled", "Compact", "Connected"],
        "nouns": ["Plug", "Hub", "Speaker", "Light Strip", "Sensor"],
    },
    "accessories": {
        "price_range": (7.0, 59.0),
        "adjectives": ["Slim", "Protective", "Adjustable", "Travel"],
        "nouns": ["Sleeve", "Stand", "Cable Organizer", "Laptop Sleeve"],
    },
}

BRANDS = ["Northline", "Vertex", "Pulsewave", "Kindra", "Anchorpoint", "Orbitel"]


def generate_products(rng: random.Random, config: GeneratorConfig) -> list[dict[str, Any]]:
    categories = list(CATEGORIES.keys())
    products = []
    seen_names: set[str] = set()

    for i in range(1, config.product_count + 1):
        category = categories[(i - 1) % len(categories)]
        spec = CATEGORIES[category]
        low, high = spec["price_range"]

        # Avoid duplicate display names within a small catalog.
        for _ in range(20):
            name = f"{rng.choice(spec['adjectives'])} {rng.choice(spec['nouns'])}"
            if name not in seen_names:
                seen_names.add(name)
                break
        else:
            name = f"{name} {i}"

        unit_price = round(rng.uniform(low, high), 2)
        margin = rng.uniform(0.35, 0.55)
        unit_cost = round(unit_price * (1 - margin), 2)

        products.append(
            {
                "product_id": product_id(i),
                "product_name": name,
                "category": category,
                "brand": rng.choice(BRANDS),
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "active": rng.random() > 0.05,
            }
        )

    assert len({p["product_id"] for p in products}) == len(products), "product_id must be unique"
    return products
