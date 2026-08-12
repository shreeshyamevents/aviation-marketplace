from flask import Flask, render_template
import json
import os

app = Flask(__name__)

@app.route('/')
def home():
    inventory = []
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    
    # 1. Safely load inventory without crashing on bad JSON syntax
    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, 'r', encoding='utf-8') as f:
                raw_inventory = json.load(f)
                
                # 2. Ensure every item has default values for required keys
                for item in raw_inventory:
                    if isinstance(item, dict):
                        inventory.append({
                            "id": item.get("id", 0),
                            "name": item.get("name", "Unknown Aircraft"),
                            "type": item.get("type", "jet"),
                            "range": item.get("range", 0),
                            "seats": item.get("seats", 0),
                            "price": item.get("price", "Contact for Price"),
                            "image": item.get("image", "/static/icon-512.png")
                        })
        except Exception as e:
            print(f"⚠️ Failed to parse inventory.json: {e}")
            inventory = []

    return render_template('index.html', inventory=inventory)

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    # Binds to Render's dynamic PORT variable (defaults to 5000 locally)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
