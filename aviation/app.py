import os
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure SQLite Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'ace_aviation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'charter' or 'sale'
    price_per_hour = db.Column(db.Float, nullable=True)
    sell_price = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_manual = db.Column(db.Boolean, default=True)

    # Airframe Specs
    total_time_hours = db.Column(db.String(50), default="0")
    total_landings = db.Column(db.String(50), default="0")
    serial_number = db.Column(db.String(50), default="SN-PENDING")
    registration = db.Column(db.String(50), default="VT-PENDING")
    airframe_condition = db.Column(db.String(50), default="Verified Operational")
    
    # Engine Specs
    engine_model = db.Column(db.String(100), default="Standard Turbine")
    
# Initialize DB tables
with app.app_context():
    db.create_all()

# --- HELPER FUNCTIONS ---
def filter_phone_numbers(text):
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\d{10}|\d{5}[-.\s]\d{5}|\d{3}[-.\s]\d{3}[-.\s]\d{4})'
    if re.search(phone_pattern, text):
        cleaned_text = re.sub(phone_pattern, '[PHONE NUMBER RESTRICTED]', text)
        return cleaned_text, True
    return text, False

# --- ROUTES ---
@app.route('/')
def home():
    category_filter = request.args.get('category', 'all')
    type_filter = request.args.get('type', 'all')
    search_query = request.args.get('search', '').strip().lower()

    query = Aircraft.query

    if category_filter != 'all':
        query = query.filter(Aircraft.category.ilike(category_filter))
    
    if type_filter == 'charter':
        query = query.filter(Aircraft.type.in_(['charter', 'both']))
    elif type_filter == 'sale':
        query = query.filter(Aircraft.type.in_(['sale', 'both']))

    items = query.all()

    if search_query:
        items = [
            item for item in items 
            if search_query in item.title.lower() 
            or search_query in item.category.lower() 
            or search_query in item.location.lower()
        ]

    categories = ["Private Jets", "Turboprops", "Helicopters", "Cargo Aircraft", "Avionics & Engines"]

    return render_template('index.html', 
                           items=items, 
                           categories=categories, 
                           selected_category=category_filter, 
                           selected_type=type_filter, 
                           search_query=search_query)

@app.route('/inspect-airframe/<int:asset_id>')
def inspect_airframe(asset_id):
    aircraft = Aircraft.query.get_or_404(asset_id)
    return render_template('inspect_airframe.html', aircraft=aircraft)

@app.route('/add-aircraft', methods=['GET', 'POST'])
def add_aircraft():
    if request.method == 'POST':
        deal_type = request.form.get('type', 'charter')
        price_per_hour = float(request.form.get('price_per_hour')) if request.form.get('price_per_hour') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None

        image_url = request.form.get('image', '').strip()
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"

        new_aircraft = Aircraft(
            title=request.form.get('title'),
            category=request.form.get('category'),
            type=deal_type,
            price_per_hour=price_per_hour,
            sell_price=sell_price,
            location=request.form.get('location'),
            operator_name=request.form.get('operator_name', 'ACE Verified Operator'),
            image=image_url,
            description=request.form.get('description'),
            total_time_hours=request.form.get('total_time_hours', '0'),
            total_landings=request.form.get('total_landings', '0'),
            serial_number=request.form.get('serial_number', 'SN-PENDING'),
            registration=request.form.get('registration', 'VT-PENDING'),
            engine_model=request.form.get('engine_model', 'Standard Turbine'),
            is_manual=True
        )

        db.session.add(new_aircraft)
        db.session.commit()
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
