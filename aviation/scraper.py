import json
import os

INVENTORY_FILE = 'inventory.json'

DEFAULT_IMAGES = {
    "Private Jets": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
    "Turboprops": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=80",
    "Helicopters": "https://images.unsplash.com/photo-1519074069444-1ba4edd16be1?auto=format&fit=crop&w=800&q=80"
}

BAD_IMAGE_KEYWORDS = ['city', 'drone', 'street', 'shibuya', 'neon', 'traffic', 'tokyo']

def validate_image_url(url, category):
    """Replaces invalid or random non-aviation images with verified fallbacks."""
    if not url:
        return DEFAULT_IMAGES.get(category, DEFAULT_IMAGES["Private Jets"])
    url_lower = url.lower()
    if any(keyword in url_lower for keyword in BAD_IMAGE_KEYWORDS):
        return DEFAULT_IMAGES.get(category, DEFAULT_IMAGES["Private Jets"])
    return url

def run_scraper():
    # 1. Load existing inventory to preserve manual listings
    existing_items = []
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                existing_items = json.load(f)
        except json.JSONDecodeError:
            existing_items = []

    # Filter out manual listings to keep them safe
    manual_listings = [item for item in existing_items if item.get('is_manual') is True]

    # 2. Process / Scrape incoming aircraft data
    scraped_data = [
        {
            "id": 101,
            "title": "2018 Gulfstream G650ER",
            "category": "Private Jets",
            "type": "charter",
            "price_per_hour": 85000,
            "location": "New Delhi (DEL)",
            "operator_name": "Skyways Aviation",
            "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
            "description": "Ultra-long-range business jet equipped with Honeywell Primus Epic avionics.",
            "is_manual": False,
            "airframe_specs": {
                "total_time_hours": "1850",
                "total_landings": "620",
                "serial_number": "6321",
                "registration": "VT-SS1",
                "airframe_condition": "Excellent",
                "next_c_check": "2027-11"
            },
            "engine_specs": {
                "engine_model": "Rolls-Royce BR725A1-12",
                "engine_1_tt": 1850,
                "engine_2_tt": 1850,
                "apu_model": "Honeywell RE220"
            },
            "inspection_logs": [
                {"date": "2026-05-12", "type": "A-Check", "status": "Passed", "inspector": "DGCA Certified MRO"}
            ]
        }
    ]

    # 3. Clean images and format incoming scraped data
    cleaned_scraped = []
    for item in scraped_data:
        item['image'] = validate_image_url(item.get('image'), item.get('category'))
        item['is_manual'] = False
        cleaned_scraped.append(item)

    # 4. Merge manual listings with scraped listings
    manual_ids = {item['id'] for item in manual_listings}
    final_inventory = manual_listings + [item for item in cleaned_scraped if item['id'] not in manual_ids]

    # 5. Save back to inventory.json
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_inventory, f, indent=4)
        
    print(f"Inventory updated. Preserved {len(manual_listings)} manual listings. Total items: {len(final_inventory)}")

if __name__ == "__main__":
    run_scraper()
