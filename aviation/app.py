import os
import re
import uuid
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CLOUDINARY CONFIGURATION ---
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

HAS_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

if HAS_CLOUDINARY:
    cloudinary.config(
        cloud_name = CLOUDINARY_CLOUD_NAME,
        api_key = CLOUDINARY_API_KEY,
        api_secret = CLOUDINARY_API_SECRET
    )

# --- LOCAL UPLOAD FALLBACK CONFIG ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ADD AIRCRAFT ROUTE ---
@app.route('/add-aircraft', methods=['GET', 'POST'])
def add_aircraft():
    if request.method == 'POST':
        deal_type = request.form.get('type', 'charter')
        price_per_hour = float(request.form.get('price_per_hour')) if request.form.get('price_per_hour') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None

        # Fallback default image
        image_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"

        # Handle uploaded file
        if 'aircraft_image' in request.files:
            file = request.files['aircraft_image']
            if file and file.filename != '' and allowed_file(file.filename):
                if HAS_CLOUDINARY:
                    # Upload directly to Cloudinary cloud storage
                    upload_result = cloudinary.uploader.upload(file)
                    image_url = upload_result.get('secure_url', image_url)
                else:
                    # Save locally for development testing
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
