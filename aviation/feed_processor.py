import csv
import json
from app import app, db, Aircraft

def process_csv_feed(file_path):
    """Processes operator inventory from a CSV file."""
    with app.app_context():
        with open(file_path, mode='r', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            count = 0
            for row in reader:
                aircraft = Aircraft(
                    title=row.get('title'),
                    category=row.get('category', 'Private Jets'),
                    type=row.get('type', 'charter'),
                    price_per_hour=float(row['price_per_hour']) if row.get('price_per_hour') else None,
                    sell_price=float(row['sell_price']) if row.get('sell_price') else None,
                    location=row.get('location', 'India'),
                    operator_name=row.get('operator_name', 'Verified NSOP Operator'),
                    image=row.get('image_url', 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf'),
                    description=row.get('description', ''),
                    total_time_hours=row.get('total_time_hours', '0'),
                    registration=row.get('registration', 'VT-PENDING'),
                    is_manual=False
                )
                db.session.add(aircraft)
                count += 1
            db.session.commit()
            print(f"Successfully processed {count} operator listings from CSV.")

if __name__ == '__main__':
    # Test with sample feed
    # process_csv_feed('sample_inventory.csv')
    pass
