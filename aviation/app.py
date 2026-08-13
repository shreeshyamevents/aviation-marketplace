from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

def format_price(price):
    """Safely formats any price (int or str) into a clean display string."""
    if isinstance(price, (int, float)):
        return f"${price:,.0f}"
    return str(price) if price else "Inquire for Price"

@app.route('/debug')
def debug():
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    if os.path.exists(inventory_path):
        with open(inventory_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"file_found": True, "count": len(data), "items": data})
    return jsonify({"file_found": False, "count": 0, "items": []})

@app.route('/')
def home():
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    inventory = []

    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
                for item in raw_data:
                    # Extracts manufacturer from name if missing (e.g. "2023 Diamond DA62" -> "Diamond")
                    name = item.get("name", "Unknown Aircraft")
                    manufacturer = item.get("manufacturer")
                    if not manufacturer:
                        parts = name.split()
                        # Skip year if present
                        manufacturer = parts[1] if parts[0].isdigit() and len(parts) > 1 else parts[0]

                    inventory.append({
                        "id": item.get("id", 0),
                        "name": name,
                        "manufacturer": manufacturer,
                        "type": str(item.get("type", "Jet")).title(),
                        "range": item.get("range", 0),
                        "seats": item.get("seats", 0),
                        "price": format_price(item.get("price")),
                        "image": item.get("image", "/static/icon-512.png"),
                        "promo_property": item.get("promo_property")
                    })
        except Exception as e:
            print(f"⚠️ Error processing inventory: {e}")

    # Pass inventory under all common variable names to match index.html
    return render_template('index.html', inventory=inventory, jets=inventory, aircraft=inventory)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
