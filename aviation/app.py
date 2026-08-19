import csv
import json
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

# --- ADMIN BULK IMPORT ROUTE ---
@app.route('/admin/import-feed', methods=['GET', 'POST'])
@login_required
def import_feed():
    # Ensure user has permission (can extend to check role == 'admin' if needed)
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
            # 1. PROCESS CSV FEED
            if filename.endswith('.csv'):
                stream = file.stream.read().decode("utf-8").splitlines()
                reader = csv.DictReader(stream)
                
                for row in reader:
                    price_hr = float(row.get('price_per_hour')) if row.get('price_per_hour') else None
                    sell_p = float(row.get('sell_price')) if row.get('sell_price') else None

                    aircraft = Aircraft(
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
                        is_manual=False,
                        user_id=current_user.id
                    )
                    db.session.add(aircraft)
                    processed_count += 1

            # 2. PROCESS JSON FEED
            elif filename.endswith('.json'):
                data = json.load(file.stream)
                if isinstance(data, dict):
                    data = [data] # Normalize single object to list
                    
                for row in data:
                    price_hr = float(row.get('price_per_hour')) if row.get('price_per_hour') else None
                    sell_p = float(row.get('sell_price')) if row.get('sell_price') else None

                    aircraft = Aircraft(
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
                        is_manual=False,
                        user_id=current_user.id
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
