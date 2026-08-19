from app import app, db, Aircraft

def seed():
    with app.app_context():
        # Clear existing tables
        db.drop_all()
        db.create_all()

        initial_aircraft = [
            Aircraft(
                title="2018 Gulfstream G650ER",
                category="Private Jets",
                type="charter",
                price_per_hour=85000.0,
                location="New Delhi (DEL)",
                operator_name="Skyways Aviation",
                image="https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80",
                description="Ultra-long-range business jet equipped with Honeywell Primus Epic avionics.",
                total_time_hours="1850",
                total_landings="620",
                serial_number="6321",
                registration="VT-SS1",
                engine_model="Rolls-Royce BR725A1-12",
                is_manual=False
            ),
            Aircraft(
                title="2021 Bombardier Global 7500",
                category="Private Jets",
                type="charter",
                price_per_hour=95000.0,
                location="Mumbai (BOM)",
                operator_name="ACE Flight Operations",
                image="https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=80",
                description="Flagship business jet offering four true living spaces and smooth flex-wing tech.",
                total_time_hours="920",
                total_landings="310",
                serial_number="7004",
                registration="VT-ACE",
                engine_model="GE Passport 20",
                is_manual=False
            ),
            Aircraft(
                title="2019 Sikorsky S-92",
                category="Helicopters",
                type="charter",
                price_per_hour=45000.0,
                location="Bengaluru (BLR)",
                operator_name="Rotary Charter Ltd",
                image="https://images.unsplash.com/photo-1519074069444-1ba4edd16be1?auto=format&fit=crop&w=800&q=80",
                description="Heavy twin-engine executive transport helicopter equipped with active vibration control.",
                total_time_hours="1240",
                total_landings="1850",
                serial_number="920311",
                registration="VT-ROT",
                engine_model="GE CT7-8A",
                is_manual=False
            )
        ]

        db.session.add_all(initial_aircraft)
        db.session.commit()
        print("Database seeded successfully with initial aircraft listings!")

if __name__ == '__main__':
    seed()
