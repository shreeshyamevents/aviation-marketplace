import os
import re
import csv
import json
import uuid
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ace-aviation-super-secret-key-2026')

# --- DATABASE CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'ace_aviation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- CLOUDINARY CONFIGURATION ---
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

HAS_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

if HAS_CLOUDINARY:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )

# --- LOCAL FILE UPLOAD FALLBACK ---
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max size: 16MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- FLASK-LOGIN CONFIGURATION ---
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='operator')  # 'operator' or 'client'
    aircrafts = db.relationship('Aircraft', backref='owner', lazy=True)

class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'charter', 'sale', 'both'
    price_per_hour = db.Column(db.Float, nullable=True)
    sell_price = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_manual = db.Column(db.Boolean, default=True)

    # Technical Airframe Specs
    total_time_hours = db.Column(db.String(50), default="0")
    total_landings = db.Column(db.String(50), default="0")
    serial_number = db.Column(db.String(50), default="SN-PENDING")
    registration = db.Column(db.String(50), default="VT-PENDING")
    airframe_condition = db.Column(db.String(50), default="Verified Operational")
    engine_model = db.Column(db.String(100), default="Standard Turbine")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- SELF-HEALING DATABASE INITIALIZATION ---
with app.app_context():
    try:
        db.create_all()
    except Exception:
        db.drop_all()
        db.create_all()

# --- BACKGROUND AUTOMATED SCHEDULER & SCRAPER ---
app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler()
scheduler.init_app(app)

AUTOMATED_OPERATOR_FEEDS = [
    {"name": "TajAir", "url": "https://api.example.com/tajair/fleet.json"},
    {"name": "Pinnacle Air", "url": "https://api.example.com/pinnacle/fleet.json"}
]

def run_operator_feed_sync():
    """Core scraping and ingestion function."""
    synced_count = 0
    with app.app_context():
        print("Starting scheduled operator feed sync...")
        for feed in AUTOMATED_OPERATOR_FEEDS:
            try:
                response = requests.get(feed['url'], timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        data = [data]

                    for row in data:
                        price_hr = float(row.get('price_per_hour')) if row.get('price_per_hour') else None
                        sell_p = float(row.get('sell_price')) if row.get('sell_price') else None

                        aircraft = Aircraft(
                            title=row.get('title', 'Scraped Aircraft Asset'),
                            category=row.get('category', 'Private Jets'),
                            type=row.get('type', 'charter'),
                            price_per_hour=price_hr,
                            sell_price=sell_p,
                            location=row.get('location', 'India'),
                            operator_name=feed['name'],
                            image=row.get('image_url') or "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                            description=row.get('description', 'Automated feed import.'),
                            registration=row.get('registration', 'VT-PENDING'),
                            total_time_hours=str(row.get('total_time_hours', '0')),
                            is_manual=False
                        )
                        db.session.add(aircraft)
                        synced_count += 1

                    db.session.commit()
                    print(f"Successfully auto-synced {synced_count} listings for {feed['name']}")
            except Exception as e:
                db.session.rollback()
                print(f"Failed to auto-sync {feed['name']}: {str(e)}")
    return synced_count

@scheduler.task('interval', id='auto_fetch_feeds', hours=6)
def auto_fetch_operator_feeds():
    run_operator_feed_sync()

scheduler.start()

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

# Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company = request.form.get('company_name')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))

        hashed_pw = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_pw, company_name=company)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        
        flash('Invalid corporate email or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Single Aircraft Form Submission
@app.route('/add-aircraft', methods=['GET', 'POST'])
@login_required
def add_aircraft():
    if request.method == 'POST':
        deal_type = request.form.get('type', 'charter')
        price_per_hour = float(request.form.get('price_per_hour')) if request.form.get('price_per_hour') else None
        sell_price = float(request.form.get('sell_price')) if request.form.get('sell_price') else None

        image_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"
        if 'aircraft_image' in request.files:
            file = request.files['aircraft_image']
            if file and file.filename != '' and allowed_file(file.filename):
                if HAS_CLOUDINARY:
                    upload_result = cloudinary.uploader.upload(file)
                    image_url = upload_result.get('secure_url', image_url)
                else:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    image_url = f"/static/uploads/{unique_filename}"

        new_aircraft = Aircraft(
            user_id=current_user.id,
            title=request.form.get('title'),
            category=request.form.get('category'),
            type=deal_type,
            price_per_hour=price_per_hour,
            sell_price=sell_price,
            location=request.form.get('location'),
            operator_name=request.form.get('operator_name', current_user.company_name),
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

# Admin Bulk CSV/JSON Feed Import
@app.route('/admin/import-feed', methods=['GET', 'POST'])
@login_required
def import_feed():
    if request.method == 'POST':
        if 'feed_file' not in request.files:
            flash('No file selected for upload.', 'danger')
            return redirect(request.url)
            
        file = request.files['feed_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        filename = file.filename.lower()
        processed_count = 0

        try:
            if filename.endswith('.csv'):
                stream = file.stream.read().decode("utf-8").splitlines()
                reader = csv.DictReader(stream)
                
                for row in reader:
                    price_hr = float(row.get('price_per_hour')) if row.get('price_per_hour') else None
                    sell_p = float(row.get('sell_price')) if row.get('sell_price') else None

                    aircraft = Aircraft(
                        user_id=current_user.id,
                        title=row.get('title', 'Unknown Aircraft'),
                        category=row.get('category', 'Private Jets'),
                        type=row.get('type', 'charter'),
                        price_per_hour=price_hr,
                        sell_price=sell_p,
                        location=row.get('location', 'Unspecified Base'),
                        operator_name=row.get('operator_name', current_user.company_name),
                        image=row.get('image_url') or "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                        description=row.get('description', 'Operator bulk imported listing.'),
                        total_time_hours=str(row.get('total_time_hours', '0')),
                        registration=row.get('registration', 'VT-PENDING'),
                        is_manual=False
                    )
                    db.session.add(aircraft)
                    processed_count += 1

            elif filename.endswith('.json'):
                data = json.load(file.stream)
                if isinstance(data, dict):
                    data = [data]
                    
                for row in data:
                    price_hr = float(row.get('price_per_hour')) if row.get('price_per_hour') else None
                    sell_p = float(row.get('sell_price')) if row.get('sell_price') else None

                    aircraft = Aircraft(
                        user_id=current_user.id,
                        title=row.get('title', 'Unknown Aircraft'),
                        category=row.get('category', 'Private Jets'),
                        type=row.get('type', 'charter'),
                        price_per_hour=price_hr,
                        sell_price=sell_p,
                        location=row.get('location', 'Unspecified Base'),
                        operator_name=row.get('operator_name', current_user.company_name),
                        image=row.get('image_url') or "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                        description=row.get('description', 'Operator bulk imported listing.'),
                        total_time_hours=str(row.get('total_time_hours', '0')),
                        registration=row.get('registration', 'VT-PENDING'),
                        is_manual=False
                    )
                    db.session.add(aircraft)
                    processed_count += 1

            else:
                flash('Invalid format! Please upload a .csv or .json file.', 'danger')
                return redirect(request.url)

            db.session.commit()
            flash(f'Success! Imported {processed_count} aircraft listings into the database.', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing feed: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('import_feed.html')

# Manual On-Demand Scraper Trigger
@app.route('/admin/sync-now')
@login_required
def trigger_sync_now():
    count = run_operator_feed_sync()
    flash(f"Scraper executed! Synced {count} listings from active operator feeds.", "success")
    return redirect(url_for('home'))

# Message Filter Route
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
