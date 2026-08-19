import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'ace_aviation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File Upload Settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size: 16MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---
@app.route('/add-aircraft', methods=['GET', 'POST'])
def add_aircraft():
    if request.method == 'POST':
        deal_type = request.form.get('type', 'charter')
        price_per_hour = float(request.form.get('price_per_hour')) if request.form.get('price_per_hour') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None

        # Process Image File Upload
        image_url = "/static/uploads/default_aircraft.jpg"
        if 'aircraft_image' in request.files:
            file = request.files['aircraft_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                image_url = f"/static/uploads/{unique_filename}"

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
