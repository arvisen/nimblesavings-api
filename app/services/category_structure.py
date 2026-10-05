"""
The full age_stage -> category -> [subcategory] tree.

`subcategory` is the real shoppable unit (the thing with an actual Amazon
browse node / Walmart search term in bestsellers.py's SOURCE_CONFIG).
`category` is a grouping label used for navigation/menus and for building
a combined "Feeding essentials" style checklist page that aggregates
several subcategories together — it's not itself a bestseller source.

Newborn (0-3mo) and Infant (3-12mo) have been merged into one stage,
"Baby & Infant (0-12mo)", since their essentials overlap heavily —
update any existing content/links still pointing at the old two stages.

Preschool and Big Kid's subcategories come from descriptive "daily
essentials" bullets rather than a flat product-type list — the bolded
item names became the subcategory, and your sizing/brand guidance
(e.g. "18-25L capacity", "Thule Enroute 23L") belongs in that
subcategory's curation notes (what makes a good pick), not hardcoded
into the product-matching logic.
"""

CATEGORY_STRUCTURE: dict[str, dict[str, list[str]]] = {
    "Baby & Infant (0-12mo)": {
        "Feeding": [
            "Bibs", "Bottles", "Burp Cloths", "Bottle Drying Rack",
            "Bottle Sterilizer", "Breast Pump", "High Chair", "Cups",
            "Nursing Pillow", "Solid Feeding",
        ],
        "Sleeping": [
            "Baby Monitor", "Bassinet", "Crib", "Crib Mattress",
            "Crib Sheets", "Swaddle", "Blanket",
        ],
        "Diapering": [
            "Changing Pad", "Changing Table", "Cream", "Diaper",
            "Diaper Bag", "Diaper Pail", "Wipes",
        ],
        "Baby Gear": [
            "Car Seat", "Stroller & Wagon", "Car Accessories",
        ],
        "Health & Safety": [
            "Baby Thermometer", "Pacifier", "First Aid", "Teether", "Brush",
        ],
        "Bathing": [
            "Bathtub", "Towels", "Bath Accessories", "Washcloth",
        ],
        "Nursery & Decor": [
            "Storage", "Playmat", "Rugs",
        ],
        "Clothing": [
            "Bodysuit", "Socks", "Hats", "Pants", "Mittens", "Outerwear", "Shoes",
        ],
        "Playing": [
            "Books", "Bouncer", "Toys",
        ],
    },
    "Toddler (1-3yr)": {
        "Feeding": [
            "High Chair", "Cups", "Bottles", "Plates", "Bibs",
        ],
        "Sleep & Nursery": [
            "Blankets", "Sleep Sack", "Blackout Curtains",
            "White Noise Machine", "Convertible Bed",
        ],
        "Bath": [
            "Bath Mat", "Spout Cover", "Body Wash & Lotion",
        ],
        "Health & Safety": [
            "Safety Gates", "Outlet Cover", "Corner Guard",
            "Cabinet Locks", "Thermometer",
        ],
        # Not specified in your list — filled in to match the pattern;
        # change freely.
        "Clothing": [
            "Tops", "Pants", "Outerwear", "Sleepwear",
        ],
        "Shoes": [
            "Everyday Shoes", "Rain Boots", "Winter Boots",
        ],
        "Gear": [
            "Car Seat", "Stroller", "Booster Seat",
        ],
        "Playing": [
            "Books", "Ride-On Toys", "Outdoor Play",
        ],
    },
    "Preschool (3-5yr)": {
        "Daily Packing Essentials": [
            "Backpack", "Water Bottle", "Lunch & Snack Containers", "Change of Clothes",
        ],
        "Clothing & Gear": [
            "Shoes", "Indoor Shoes", "Weather Gear", "Rest Time Items",
        ],
        "Health & Care": [
            "Potty Training Supplies", "Sunscreen & Labeling",
        ],
    },
    "Big Kid (5-12yr)": {
        "Daily Gear & Organization": [
            "Backpack", "Lunch Box", "Water Bottle", "Ice Packs & Utensils",
        ],
        "Core School & Stationery Supplies": [
            "Pencil Pouch", "Writing Tools", "Highlighters & Markers",
            "Binders & Paper", "Basic Math Set", "Student Planner",
        ],
        "Technology": [
            "Laptop or Chromebook", "Laptop Sleeve", "Headphones", "USB Flash Drive",
        ],
        "Clothing & Wardrobe": [
            "Tops & Bottoms", "Layering Pieces", "Gym Shoes",
        ],
        "Personal Care & Locker Extras": [
            "Hand Sanitizer & Tissues", "Combination Lock", "Label Maker",
        ],
    },
}


def get_categories_for_stage(age_stage: str) -> list[str]:
    return list(CATEGORY_STRUCTURE.get(age_stage, {}).keys())


def get_subcategories(age_stage: str, category: str) -> list[str]:
    return CATEGORY_STRUCTURE.get(age_stage, {}).get(category, [])


def get_full_tree() -> dict:
    """For building WordPress nav menus / taxonomy import scripts from."""
    return CATEGORY_STRUCTURE
