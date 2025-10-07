from flask import Blueprint, jsonify
from datetime import datetime

bp = Blueprint('health', __name__)

@bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /health',
            'geocode': 'GET /api/geocode?city=<city_name>',
            'weather': 'GET /api/weather?city=<city> OR ?latitude=<lat>&longitude=<lon>',
            'suggest': 'POST /api/suggest-quick',
            'itinerary': 'POST /api/itinerary'
        }
    }), 200