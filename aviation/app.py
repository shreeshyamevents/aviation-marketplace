from flask import Flask, render_template
import json
import os

app = Flask(__name__)

@app.route('/')
def home():
    # Construct an absolute path to inventory.json in the same folder as app.py
    inventory_path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    inventory = []

    if os.path.exists(inventory_path):
        try:
            with open(inventory_path, 'r', encoding='utf-8') as f:
                inventory = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading inventory file: {e}")
            inventory = []

    return render_template('index.html', inventory=inventory)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
