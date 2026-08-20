from app import app, db, User, Aircraft
from werkzeug.security import generate_password_hash

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create Primary Admin User
        admin_email = "acebusiness0726@gmail.com"
        admin_password = generate_password_hash("Shyam261121")
        
        admin_user = User(
            email=admin_email,
            password_hash=admin_password,
            company_name="ACE Aviation Corporate",
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()

        # Add Sample Aircraft Assets assigned to Admin
        sample_aircraft = [
            Aircraft(
                user_id=admin_user.id,
                title="2022 Gulfstream G700",
                category="Private Jets",
                type="both",
                price_per_hour=850000.0,
                sell_price=450000000.0,
                location="New Delhi (DEL)",
                operator_name="ACE Executive",
                image="https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                description="Ultra long-range flagship jet with bespoke cabin luxury.",
                registration="VT-ACE",
                total_time_hours="450",
                is_manual=True
            ),
            Aircraft(
                user_id=admin_user.id,
                title="2019 Bombardier Global 6000",
                category="Private Jets",
                type="charter",
                price_per_hour=720000.0,
                location="Mumbai (BOM)",
                operator_name="Skyways Aviation",
                image="https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=80",
                description="High-altitude capability with seating for up to 14 passengers.",
                registration="VT-SKY",
                total_time_hours="1200",
                is_manual=True
            )
        ]

        db.session.add_all(sample_aircraft)
        db.session.commit()
        print("Database successfully seeded with Admin account and starter aircraft listings!")

if __name__ == '__main__':
    seed_database()
