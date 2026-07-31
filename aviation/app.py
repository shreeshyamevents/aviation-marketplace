from flask import Flask, render_template, request, redirect, flash, url_for
import json
import os

app = Flask(__name__)
app.secret_key = "ace_aviation_brokerage_midnight_gold_key"

def load_inventory():
    """Reads the inventory.json text ledger dynamically from disk"""
    inventory_path = os.path.join(app.root_path, 'inventory.json')
    try:
        with open(inventory_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading inventory file: {e}")
        return []

@app.route("/")
def home_catalog():
    # Load data dynamically from the json file on every request
    aircraft_database = load_inventory()
    
    req_range = request.args.get('range_profile', 'all')
    req_seats = request.args.get('seating', 'all')
    req_type = request.args.get('type', 'all')

    matched_results = []

    for craft in aircraft_database:
        # 1. Travel Distance Profile Matrix Check
        range_match = False
        if req_range == 'all':
            range_match = True
        elif req_range == 'city' and craft['range'] < 1200:
            range_match = True
        elif req_range == 'country' and (1200 <= craft['range'] <= 3500):
            range_match = True
        elif req_range == 'inter' and craft['range'] > 3500:
            range_match = True

        # 2. Seating Capacity Matrix Check
        seating_match = False
        if req_seats == 'all':
            seating_match = True
        elif req_seats == 'light' and craft['seats'] <= 6:
            seating_match = True
        elif req_seats == 'mid' and (7 <= craft['seats'] <= 12):
            seating_match = True
        elif req_seats == 'heavy' and craft['seats'] > 12:
            seating_match = True

        # 3. Structural Classification Check
        type_match = (req_type == 'all' or craft['type'] == req_type)

        if range_match and seating_match and type_match:
            matched_results.append(craft)

    return render_template(
        "index.html", 
        aircrafts=matched_results, 
        req_range=req_range, 
        req_seats=req_seats, 
        req_type=req_type
    )

@app.route("/aircraft/<int:craft_id>")
def aircraft_view(craft_id):
    aircraft_database = load_inventory()
    craft = next((item for item in aircraft_database if item["id"] == craft_id), None)
    if not craft:
        return "Airframe Matrix Key Non-Existent", 404
    return render_template("detail.html", craft=craft)

@app.route("/submit-inquiry", methods=["POST"])
def capture_inquiry():
    customer_email = request.form.get("customer_email")
    craft_id = int(request.form.get("craft_id"))
    
    aircraft_database = load_inventory()
    craft = next((item for item in aircraft_database if item["id"] == craft_id), None)
    
    if craft and customer_email:
        # Inquiry saved confirmation message anchor
        flash("Dossier request logged successfully. System tracking profile dispatched.", "success")
            
    return redirect(url_for('aircraft_view', craft_id=craft_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)