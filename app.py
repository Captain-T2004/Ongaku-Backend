from flask import Flask
from flask_cors import CORS
from routes import health, geocode, weather, suggest, itinerary

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "max_age": 3600
    }
})

app.config['TIMEOUT'] = 120

app.register_blueprint(health.bp)
app.register_blueprint(geocode.bp)
app.register_blueprint(weather.bp)
app.register_blueprint(suggest.bp)
app.register_blueprint(itinerary.bp)

if __name__ == '__main__':
    print("=" * 70)
    print("🎵 Music-Weather Voice Assistant Backend API")
    print("=" * 70)
    print(f"Server starting at: http://localhost:5000")
    print(f"\nAvailable Endpoints:")
    print(f"  • GET  /health                  - Health check")
    print(f"  • GET  /api/geocode             - City to coordinates")
    print(f"  • GET  /api/weather             - Weather data")
    print(f"  • POST /api/suggest-quick       - AI music suggestions")
    print(f"  • POST /api/itinerary           - Day-by-day itinerary")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)