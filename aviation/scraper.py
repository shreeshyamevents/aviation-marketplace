# Array of targets to scrape in a single run
TARGET_URLS = [
    "https://www.planedekhoindia.com/aircraft-for-sale-in-india",
    "https://www.aeroclassifieds.com/",
    "https://aureaaviation.com/aircraft-sales-purchase"
]

def main():
    inventory_file = 'inventory.json'
    existing_inventory = load_existing_inventory(inventory_file)
    
    all_new_jets = []
    
    # Loop through each marketplace
    for url in TARGET_URLS:
        print(f"🌐 Scraping: {url}")
        raw_text = fetch_page_text_with_browser(url)
        if raw_text:
            jets = extract_jets_with_gemini(raw_text)
            all_new_jets.extend(jets)
            
    # Deduplicate and save to inventory.json
    save_updated_inventory(existing_inventory, all_new_jets)
