import os
import json
import urllib.request
import re
from bs4 import BeautifulSoup
from google import genai

# 1. Initialize Gemini Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY environment variable not found or empty.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Target website to scrape
TARGET_URL = "https://www.planedekhoindia.com/aircraft-for-sale-in-india"

def fetch_page_text(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            return text[:8000]
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

def extract_jets_with_gemini(raw_text):
    prompt = f"""
    You are an aviation data parser. Extract aircraft listings from the following text into a valid JSON array.
    
    Each item in the array MUST have the following structure:
    {{
        "name": "Aircraft Full Name / Model",
        "type": "light, mid, heavy, or helicopter",
        "range": 2500,
        "seats": 10,
        "price": "Formatted price string",
        "image": "Image URL if present, or fallback string '/static/icon-512.png'"
    }}

    Rules:
    - Respond strictly with ONLY a JSON array inside ```json ``` codeblock.
    - Do not invent fake aircraft if none are listed.

    RAW TEXT:
    {raw_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
        json_str = match.group(1) if match else response.text
        
        return json.loads(json_str)
    except Exception as e:
        print(f"❌ Gemini parsing error: {e}")
        return []

def main():
    inventory_file = 'inventory.json'
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
        exit(1)

    print("🤖 Processing text through Gemini AI Engine...")
    new_jets = extract_jets_with_gemini(raw_text)
    
    if not new_jets:
        print("ℹ️ No new jets parsed or list was empty.")
        return

    max_id = max([item.get('id', 0) for item in existing_inventory], default=0)
    existing_names = {item.get('name', '').lower() for item in existing_inventory}
    added_count = 0

    for jet in new_jets:
        if jet.get('name', '').lower() not in existing_names:
            max_id += 1
            jet['id'] = max_id
            existing_inventory.append(jet)
            existing_names.add(jet.get('name', '').lower())
            added_count += 1

    with open(inventory_file, 'w', encoding='utf-8') as f:
        json.dump(existing_inventory, f, indent=4)

    print(f"✅ Auto-update complete! Added {added_count} new aircraft to {inventory_file}.")

if __name__ == '__main__':
    main()
