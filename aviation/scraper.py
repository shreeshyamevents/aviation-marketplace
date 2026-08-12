import os
import json
import urllib.request
import re
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. Initialize Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Target website to scrape
TARGET_URL = "https://www.planedekhoindia.com/aircraft-for-sale-in-india"

def fetch_page_text(url):
    """Fetches raw HTML and extracts visible text content."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            # Extract plain text content from page body
            text = soup.get_text(separator=' ', strip=True)
            return text[:8000]  # Limit context size for fast parsing
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

def extract_jets_with_gemini(raw_text):
    """Passes raw web text to Gemini 1.5 Flash for JSON extraction."""
    prompt = f"""
    You are an aviation data parser. Extract aircraft listings from the following text into a valid JSON array.
    
    Each item in the array MUST have the following structure:
    {{
        "name": "Aircraft Full Name / Model",
        "type": "light, mid, heavy, or helicopter",
        "range": Integer value in Nautical Miles (estimate if missing, e.g. 1500 for light, 3500 for mid, 6000 for heavy),
        "seats": Integer value of passenger seating,
        "price": "Formatted price string e.g., $15,000,000 or Call for Price",
        "image": "Image URL if present, or fallback string '/static/icon-512.png'"
    }}

    Rules:
    - Respond strictly with ONLY a JSON array inside ```json ``` codeblock.
    - Do not invent fake aircraft if none are listed in the text.
    - Assign realistic types: light (<= 6 seats), mid (7-12 seats), heavy (> 12 seats).

    RAW TEXT:
    {raw_text}
    """
    
    response = model.generate_content(prompt)
    try:
        # Extract JSON block using regex
        match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = response.text
        
        parsed = json.loads(json_str)
        return parsed
    except Exception as e:
        print(f"❌ Failed to parse Gemini response: {e}\nResponse text was: {response.text}")
        return []

def main():
    inventory_file = 'inventory.json'
    
    # Load current inventory to keep IDs and custom listings
    existing_inventory = []
    if os.path.exists(inventory_file):
        with open(inventory_file, 'r', encoding='utf-8') as f:
            try:
                existing_inventory = json.load(f)
            except Exception:
                existing_inventory = []

    print("🔎 Fetching target website listings...")
    raw_text = fetch_page_text(TARGET_URL)
    
    if not raw_text:
        print("❌ Could not pull content from target website.")
        return

    print("🤖 Processing text through Gemini 1.5 Flash...")
    new_jets = extract_jets_with_gemini(raw_text)
    
    if not new_jets:
        print("ℹ️ No new jets parsed or list was empty.")
        return

    # Find highest existing ID
    max_id = max([item.get('id', 0) for item in existing_inventory], default=0)

    existing_names = {item.get('name', '').lower() for item in existing_inventory}
    added_count = 0

    for jet in new_jets:
        # Avoid duplicate listings
        if jet.get('name', '').lower() not in existing_names:
            max_id += 1
            jet['id'] = max_id
            existing_inventory.append(jet)
            existing_names.add(jet.get('name', '').lower())
            added_count += 1

    # Save updated inventory back to file
    with open(inventory_file, 'w', encoding='utf-8') as f:
        json.dump(existing_inventory, f, indent=4)

    print(f"✅ Auto-update complete! Added {added_count} new aircraft to {inventory_file}.")

if __name__ == '__main__':
    main()
