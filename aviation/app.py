from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import re

app = Flask(__name__)

def load_inventory():
    path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_inventory(data):
    path = os.path.join(os.path.dirname(__file__), 'inventory.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def filter_phone_numbers(text):
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\d{10}|\d{5}[-.\s]\d{5}|\d{3}[-.\s]\d{3}[-.\s]\d{4})'
    if re.search(phone_pattern, text):
        cleaned_text = re.sub(phone_pattern, '[PHONE NUMBER RESTRICTED]', text)
        return cleaned_text, True
    return text, False

@app.route('/')
def home():
    inventory = load_inventory()
    
    category_filter = request.args.get('category', 'all')
    type_filter = request.args.get('type', 'all')
    search_query = request.args.get('search', '').strip().lower()
    
    filtered_items = []
    for item in inventory:
        if category_filter != 'all' and item.get('category', '').lower() != category_filter.lower():
            continue
        if type_filter == 'charter' and item.get('type') not in ['charter', 'both']:
            continue
        elif type_filter == 'sale' and item.get('type') not in ['sale', 'both']:
            continue

        if search_query:
            title_match = search_query in item.get('title', '').lower()
            cat_match = search_query in item.get('category', '').lower()
            loc_match = search_query in item.get('location', '').lower()
            if not (title_match or cat_match or loc_match):
                continue

        filtered_items.append(item)

    categories = ["Private Jets", "Turboprops", "Helicopters", "Cargo Aircraft", "Avionics & Engines"]

    return render_template('index.html', 
                           items=filtered_items, 
                           categories=categories, 
                           selected_category=category_filter, 
                           selected_type=type_filter, 
                           search_query=search_query)

@app.route('/aircraft/<int:item_id>')
def aircraft_detail(item_id):
    inventory = load_inventory()
    item = next((i for i in inventory if i.get('id') == item_id), None)
    if not item:
        return "Aircraft Asset Not Found", 404
    return render_template('detail.html', item=item)

@app.route('/inspect-airframe/<int:asset_id>')
def inspect_airframe(asset_id):
    inventory = load_inventory()
    aircraft = next((item for item in inventory if item.get('id') == asset_id), None)
    
    if not aircraft:
        return "Airframe Asset Not Found", 404
        
    return render_template('inspect_airframe.html', aircraft=aircraft)

@app.route('/add-aircraft', methods=['GET', 'POST'])
def add_aircraft():
    if request.method == 'POST':
        inventory = load_inventory()
        
        deal_type = request.form.get('type', 'charter')
        price_per_hour = float(request.form.get('price_per_hour')) if request.form.get('price_per_hour') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None

        image_url = request.form.get('image', '').strip()
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"

        new_item = {
            "id": len(inventory) + 1,
            "title": request.form.get('title'),
            "category": request.form.get('category'),
            "type": deal_type,
            "price_per_hour": price_per_hour,
            "sell_price": sell_price,
            "location": request.form.get('location'),
            "operator_name": request.form.get('operator_name', 'ACE Verified Operator'),
            "rating": 5.0,
            "image": image_url,
            "description": request.form.get('description'),
            "airframe_specs": {
                "total_time_hours": request.form.get('total_time_hours', '0'),
                "total_landings": request.form.get('total_landings', '0'),
                "serial_number": request.form.get('serial_number', 'SN-PENDING'),
                "registration": request.form.get('registration', 'VT-PENDING'),
                "airframe_condition": "Verified Operational",
                "next_c_check": "Scheduled"
            },
            "engine_specs": {
                "engine_model": request.form.get('engine_model', 'Standard Turbine'),
                "engine_1_tt": 0,
                "engine_2_tt": 0,
                "apu_model": "Standard APU"
            },
            "inspection_logs": [
                {"date": "2026-08-01", "type": "Airworthiness Certificate Verification", "status": "Passed", "inspector": "ACE Aviation MRO"}
            ]
        }

        inventory.append(new_item)
        save_inventory(inventory)
        return redirect(url_for('home'))

    categories = ["Private Jets", "Turboprops", "Helicopters", "Cargo Aircraft", "Avionics & Engines"]
    return render_template('add_aircraft.html', categories=categories)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json or {}
    raw_message = data.get('message', '')
    
    filtered_msg, was_blocked = filter_phone_numbers(raw_message)
    
    if was_blocked:
        return jsonify({
            "status": "warning",
            "message": "Direct contact numbers are restricted to protect escrow and booking compliance.",
            "sanitized_content": filtered_msg
        })
    
    return jsonify({
        "status": "success",
        "sanitized_content": filtered_msg
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
