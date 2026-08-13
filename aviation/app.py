from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

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
                inventory = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading inventory file: {e}")

    # Pass 'inventory' under multiple variable names to match index.html
    return render_template('index.html', inventory=inventory, jets=inventory, aircraft=inventory)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
