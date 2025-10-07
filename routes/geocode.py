from flask import Blueprint, request, jsonify
import requests
from config import GEOCODING_API

bp = Blueprint('geocode', __name__)

@bp.route('/api/geocode', methods=['GET'])
def geocode():
    try:
        city_raw = request.args.get('city')
        if city_raw:
            city = city_raw.encode('latin-1').decode('utf-8')
        else:
            city = None
        language = request.args.get('language', 'ja')
        country = request.args.get('country', 'jp')

        if not city:
            return jsonify({
                'error': True,
                'reason': 'Missing required parameter: city'
            }), 400

        params = {
            'name': city,
            'count': 5,
            'language': language,
            'format': 'json'
        }

        if country:
            params['country'] = country

        response = requests.get(GEOCODING_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'results' not in data or len(data['results']) == 0:
            params.pop('country', None)
            response = requests.get(GEOCODING_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        if 'results' not in data or len(data['results']) == 0:
            return jsonify({
                'error': True,
                'reason': f'No location found for: {city}'
            }), 404

        top_result = data['results'][0]

        result = {
            'success': True,
            'location': {
                'id': top_result.get('id'),
                'name': top_result.get('name'),
                'latitude': top_result.get('latitude'),
                'longitude': top_result.get('longitude'),
                'elevation': top_result.get('elevation'),
                'timezone': top_result.get('timezone'),
                'country': top_result.get('country'),
                'country_code': top_result.get('country_code'),
                'admin1': top_result.get('admin1'),
                'admin2': top_result.get('admin2'),
                'population': top_result.get('population'),
                'postcodes': top_result.get('postcodes', [])
            },
            'all_matches': [
                {
                    'name': loc.get('name'),
                    'latitude': loc.get('latitude'),
                    'longitude': loc.get('longitude'),
                    'admin1': loc.get('admin1'),
                    'country': loc.get('country')
                }
                for loc in data['results']
            ]
        }

        return jsonify(result), 200

    except requests.exceptions.Timeout:
        return jsonify({
            'error': True,
            'reason': 'Geocoding API request timed out'
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': True,
            'reason': f'Geocoding API error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'reason': f'Internal server error: {str(e)}'
        }), 500