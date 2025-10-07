from flask import Blueprint, request, jsonify
import requests
from config import GEOCODING_API, WEATHER_API, WEATHER_CONDITIONS

bp = Blueprint('weather', __name__)

@bp.route('/api/weather', methods=['GET'])
def weather():
    try:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        city = request.args.get('city')
        timezone = request.args.get('timezone', 'Asia/Tokyo')

        if city and (not latitude or not longitude):
            geocode_params = {
                'name': city,
                'count': 1,
                'language': 'ja',
                'country': 'jp'
            }
            geo_response = requests.get(GEOCODING_API, params=geocode_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if 'results' not in geo_data or len(geo_data['results']) == 0:
                return jsonify({
                    'error': True,
                    'reason': f'Could not geocode city: {city}'
                }), 404

            latitude = geo_data['results'][0]['latitude']
            longitude = geo_data['results'][0]['longitude']
            city_name = geo_data['results'][0]['name']
        elif not latitude or not longitude:
            return jsonify({
                'error': True,
                'reason': 'Missing required parameters: city OR (latitude AND longitude)'
            }), 400
        else:
            city_name = f"Location ({latitude}, {longitude})"

        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': 'temperature_2m,precipitation,weathercode,windspeed_10m,relativehumidity_2m',
            'current_weather': 'true',
            'timezone': timezone,
            'forecast_days': 1
        }

        response = requests.get(WEATHER_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get('current_weather', {})
        current_condition = WEATHER_CONDITIONS.get(
            current.get('weathercode', 0),
            'Unknown'
        )

        hourly = data.get('hourly', {})
        hourly_forecast = []

        if hourly:
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            precip = hourly.get('precipitation', [])
            codes = hourly.get('weathercode', [])
            wind = hourly.get('windspeed_10m', [])
            humidity = hourly.get('relativehumidity_2m', [])

            for i in range(min(24, len(times))):
                hourly_forecast.append({
                    'time': times[i],
                    'temperature': temps[i],
                    'precipitation': precip[i],
                    'weathercode': codes[i],
                    'condition': WEATHER_CONDITIONS.get(codes[i], 'Unknown'),
                    'windspeed': wind[i],
                    'humidity': humidity[i]
                })

        result = {
            'success': True,
            'location': {
                'name': city_name,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timezone': timezone
            },
            'current': {
                'time': current.get('time'),
                'temperature': current.get('temperature'),
                'windspeed': current.get('windspeed'),
                'winddirection': current.get('winddirection'),
                'weathercode': current.get('weathercode'),
                'condition': current_condition
            },
            'hourly_forecast': hourly_forecast,
            'units': {
                'temperature': '°C',
                'precipitation': 'mm',
                'windspeed': 'km/h',
                'humidity': '%'
            }
        }

        return jsonify(result), 200

    except requests.exceptions.Timeout:
        return jsonify({
            'error': True,
            'reason': 'Weather API request timed out'
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': True,
            'reason': f'Weather API error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'reason': f'Internal server error: {str(e)}'
        }), 500