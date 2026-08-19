import requests
from flask_apscheduler import APScheduler

scheduler = APScheduler()

AUTOMATED_OPERATOR_FEEDS = [
    {"name": "TajAir", "url": "https://api.example.com/tajair/fleet.json"},
    {"name": "Pinnacle Air", "url": "https://api.example.com/pinnacle/fleet.json"}
]

def init_scheduler(app, db, Aircraft):
    app.config['SCHEDULER_API_ENABLED'] = True
    scheduler.init_app(app)

    @scheduler.task('interval', id='auto_fetch_feeds', hours=6)
    def auto_fetch_operator_feeds():
        with app.app_context():
            print("Starting scheduled operator feed sync...")
            for feed in AUTOMATED_OPERATOR_FEEDS:
                try:
                    response = requests.get(feed['url'], timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # Process feed items here
                        print(f"Successfully auto-synced feed for {feed['name']}")
                except Exception as e:
                    print(f"Failed to auto-sync {feed['name']}: {str(e)}")

    scheduler.start()
