import os
import json
import urllib.request
import re
from bs4 import BeautifulSoup
from google import genai

print("🚀 Starting scraper execution...", flush=True)

# 1. Initialize Gemini Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY environment variable not found or empty.", flush=True)
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
TARGET_URL = "https://www.planedekhoindia.com/aircraft-for-sale-in-india"

def get_active_model(client):
    """Queries the API key to find supported Gemini models automatically."""
    print("🔍 Auto-detecting available models for your API key...", flush=True)
    try:
        available_models = list(client.models.list())
        for model in available_models:
            model_id = model.name.split('/')[-1]
            # Prioritize fast text models
            if "flash" in model_id:
                print(f"✅ Auto-selected model: {model_id}", flush=True)
                return model_id
        if available_models:
            fallback = available_models[0].name.split('/')[-1]
            print(f"✅ Auto-selected fallback model: {fallback}", flush=True)
            return fallback
    except Exception as e:
        print(f"⚠️ Could not query model list: {e}", flush=True)
    
    # Standard fallback
    return "gemini-2.5-flash"

def fetch_page_text(url):
    try:
        print(f"🔎 Requesting: {url}", flush=True)
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            print(f"📄 Downloaded page text: {len(text)} characters.", flush=True)
            return text[:10000]
    except Exception as e:
        print(f"⚠️ Error fetching {url}: {e}", flush=True)
        return None

def extract_jets_with_gemini(raw_text, model_name):
    prompt = f"""
    You are an aviation data parser. Extract aircraft listings from the text into a valid JSON array.
    Each item MUST follow this structure:
    {{
        "name": "Aircraft Model Name",
        "type": "light, mid, heavy, turboprop, or helicopter",
        "range": 2500,
        "seats": 10,
        "price": "Formatted price string",
        "image": "/static/icon-512.png"
    }}
    Rules: Respond strictly with ONLY a JSON array inside ```json ``` block.

    RAW TEXT:
    {raw_text}
    """
    try:
        print(f"🤖 Sending data to Gemini AI using [{model_name}]...", flush=True)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
        match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
        json_str = match.group(1) if match else response.text
        parsed = json.loads(json_str)
        print(f"📊 Gemini extracted {len(parsed)} aircraft.", flush=True)
        return parsed
    except Exception as e:
        print(f"❌ Gemini parsing error: {e}", flush=True)
        return []

def run_scraper():
    inventory_file = 'inventory.json'
    existing_inventory = []
    
    if os.path.exists(inventory_file):
        with open(inventory_file, 'r', encoding='utf-8') as f:
            try:
                existing_inventory = json.load(f)
            except Exception:
                existing_inventory = []

    # Get the supported model dynamically
    active_model = get_active_model(client)

    raw_text = fetch_page_text(TARGET_URL)
    if not raw_text:
        print("❌ Could not pull raw text from website.", flush=True)
        return

    new_jets = extract_jets_with_gemini(raw_text, active_model)
    if not new_jets:
        print("ℹ️ No aircraft parsed from text.", flush=True)
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

    if added_count > 0:
        with open(inventory_file, 'w', encoding='utf-8') as f:
            json.dump(existing_inventory, f, indent=4)
        print(f"✅ Auto-update complete! Added {added_count} new aircraft.", flush=True)
    else:
        print("ℹ️ All parsed aircraft are already present in inventory.json.", flush=True)

if __name__ == '__main__':
    run_scraper()
