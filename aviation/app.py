from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

def format_price(price):
    """Safely formats raw numbers or preserves existing currency strings."""
    if price is None or price == "":
        return "Inquire for Price"
    if isinstance(price, (int, float)):
        return f"${price:,.0f}"
    
    val_str = str(price).strip()
    if val_str.isdigit():
        return f"${int(val_str):,.0f}"
    
    # Already formatted string (e.g. "$6,500,000", "₹14,90,00,000", "Inquire")
    return val_str

@app.route('/debug')
def debug():
    """Diagnostic route to inspect raw inventory data loaded by the server."""
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    if os.path.exists(inventory_path):
        with open(inventory_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"file_found": True, "count": len(data), "items": data})
    return jsonify({"file_found": False, "count": 0, "items": []})

@app.route('/')
def home():
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    raw_inventory = []

    # Extract filter options from URL parameters
    req_range = request.args.get('range_profile', 'all')
    req_seats = request.args.get('seating', 'all')
    req_type = request.args.get('type', 'all')

    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, 'r', encoding='utf-8') as f:
                raw_inventory = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading inventory.json: {e}")

    processed_inventory = []
    
    for item in raw_inventory:
        name = item.get("name", "Unknown Aircraft")
        
        # Infer manufacturer from name if key is missing (e.g. "2023 Diamond DA62" -> "Diamond")
        manufacturer = item.get("manufacturer")
        if not manufacturer:
            parts = name.split()
            if parts and parts[0].isdigit() and len(parts) > 1:
                manufacturer = parts[1]
            elif parts:
                manufacturer = parts[0]
            else:
                manufacturer = "Private Asset"

        craft_range = item.get("range", 0) or 0
        craft_seats = item.get("seats", 0) or 0
        craft_type = str(item.get("type", "Jet")).title()

        # --- Interactive Filter Logic ---
        # 1. Range Filter
        if req_range == 'city' and craft_range >= 1200:
            continue
        elif req_range == 'country' and not (1200 <= craft_range <= 3500):
            continue
        elif req_range == 'inter' and craft_range < 3500:
            continue

        # 2. Seating Capacity Filter
        if req_seats == 'light' and craft_seats > 6:
            continue
        elif req_seats == 'mid' and not (7 <= craft_seats <= 12):
            continue
        elif req_seats == 'heavy' and craft_seats < 13:
            continue

        # 3. Propulsion/Type Filter
        if req_type != 'all' and req_type.lower() not in craft_type.lower():
            continue

        processed_inventory.append({
            "id": item.get("id", 0),
            "name": name,
            "manufacturer": manufacturer,
            "type": craft_type,
            "range": craft_range,
            "seats": craft_seats,
            "price": format_price(item.get("price")),
            "image": item.get("image", "/static/icon-512.png"),
            "promo_property": item.get("promo_property")
        })

    return render_template(
        'index.html',
        aircrafts=processed_inventory,
        inventory=processed_inventory,
        jets=processed_inventory,
        req_range=req_range,
        req_seats=req_seats,
        req_type=req_type
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
