import json

def scrape_aircraft_data():
    # Example structure your scraper should save into inventory.json
    scraped_aircraft = [
        {
            "id": 101,
            "title": "2018 Gulfstream G650ER",
            "type": "aircraft",
            "category": "Private Jet",
            "price_per_day": 85000,
            "location": "New Delhi (DEL)",
            "vendor_name": "Skyways Aviation",
            "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf",
            "description": "Ultra-long-range business jet equipped with Honeywell Primus Epic avionics.",
            "airframe_specs": {
                "total_time_hours": 1850,
                "total_landings": 620,
                "serial_number": "6321",
                "registration": "VT-SS1",
                "airframe_condition": "Excellent (10/10)",
                "next_c_check": "2027-11"
            },
            "engine_specs": {
                "engine_model": "Rolls-Royce BR725A1-12",
                "engine_1_tt": 1850,
                "engine_2_tt": 1850,
                "apu_model": "Honeywell RE220"
            },
            "inspection_logs": [
                {"date": "2025-10-12", "type": "A-Check", "status": "Passed", "inspector": "DGCA Certified MRO"},
                {"date": "2024-05-20", "type": "Annual Inspection", "status": "Passed", "inspector": "Avionics Tech"}
            ]
        }
    ]

    with open('inventory.json', 'w', encoding='utf-8') as f:
        json.dump(scraped_aircraft, f, indent=4)

if __name__ == "__main__":
    scrape_aircraft_data()
