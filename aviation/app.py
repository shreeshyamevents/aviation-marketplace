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
    # Detects standard 10-digit numbers, spaces, hyphens, and country codes
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
        if type_filter == 'rent' and item.get('type') not in ['rent', 'both']:
            continue
        elif type_filter == 'sell' and item.get('type') not in ['sell', 'both']:
            continue

        if search_query:
            title_match = search_query in item.get('title', '').lower()
            cat_match = search_query in item.get('category', '').lower()
            loc_match = search_query in item.get('location', '').lower()
            if not (title_match or cat_match or loc_match):
                continue

        filtered_items.append(item)

    categories = ["Private Jets", "Turboprops", "Helicopters", "Sound & Audio", "Lighting & Effects", "Power & Genset"]

    return render_template('index.html', 
                           items=filtered_items, 
                           categories=categories, 
                           selected_category=category_filter, 
                           selected_type=type_filter, 
                           search_query=search_query)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    inventory = load_inventory()
    item = next((i for i in inventory if i.get('id') == item_id), None)
    if not item:
        return "Asset Item Not Found", 404
    return render_template('detail.html', item=item)

@app.route('/inspect-airframe/<int:asset_id>')
def inspect_airframe(asset_id):
    inventory = load_inventory()
    aircraft = next((item for item in inventory if item.get('id') == asset_id), None)
    
    if not aircraft:
        return "Airframe Asset Not Found", 404
        
    return render_template('inspect_airframe.html', aircraft=aircraft)

@app.route('/add-equipment', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        inventory = load_inventory()
        
        deal_type = request.form.get('type', 'rent')
        price_per_day = float(request.form.get('price_per_day')) if request.form.get('price_per_day') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None
        security_deposit = float(request.form.get('security_deposit', 0)) if request.form.get('security_deposit') else 0

        image_url = request.form.get('image', '').strip()
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"

        new_item = {
            "id": len(inventory) + 1,
            "title": request.form.get('title'),
            "category": request.form.get('category'),
            "type": deal_type,
            "price_per_day": price_per_day,
            "sell_price": sell_price,
            "security_deposit": security_deposit,
            "location": request.form.get('location'),
            "vendor_name": request.form.get('vendor_name', 'SS Verified Vendor'),
            "rating": 5.0,
            "image": image_url,
            "description": request.form.get('description'),
            "airframe_specs": {
                "total_time_hours": request.form.get('total_time_hours', 'N/A'),
                "total_landings": request.form.get('total_landings', 'N/A'),
                "serial_number": request.form.get('serial_number', 'SN-PENDING'),
                "registration": request.form.get('registration', 'VT-PENDING'),
                "airframe_condition": "Original Verified",
                "next_c_check": "Pending Schedule"
            },
            "engine_specs": {
                "engine_model": "Standard Turbofan / Turbine",
                "engine_1_tt": 0,
                "engine_2_tt": 0,
                "apu_model": "Standard APU"
            },
            "inspection_logs": [
                {"date": "2026-08-01", "type": "Onboarding Inspection", "status": "Passed", "inspector": "SS Airframe Tech"}
            ]
        }

        inventory.append(new_item)
        save_inventory(inventory)
        return redirect(url_for('home'))

    categories = ["Private Jets", "Turboprops", "Helicopters", "Sound & Audio", "Lighting & Effects", "Power & Genset"]
    return render_template('add_equipment.html', categories=categories)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json or {}
    raw_message = data.get('message', '')
    
    filtered_msg, was_blocked = filter_phone_numbers(raw_message)
    
    if was_blocked:
        return jsonify({
            "status": "warning",
            "message": "Sharing phone numbers is disabled to maintain escrow warranty on SS Rental.",
            "sanitized_content": filtered_msg
        })
    
    return jsonify({
        "status": "success",
        "sanitized_content": filtered_msg
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
