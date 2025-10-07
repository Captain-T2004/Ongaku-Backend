from flask import Blueprint, request, jsonify
import requests
import json
from config import GEOCODING_API, WEATHER_API, WEATHER_CONDITIONS, GEMINI_API_KEY
from utils import call_gemini_streaming

bp = Blueprint('suggest', __name__)

@bp.route('/api/suggest-quick', methods=['POST'])
def suggest_quick():
    try:
        if not GEMINI_API_KEY:
            return jsonify({
                'error': True,
                'reason': 'Gemini API key not configured. Set GEMINI_API_KEY environment variable.'
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': True,
                'reason': 'Request body must be JSON'
            }), 400
        
        user_query = data.get('user_query', '')
        location = data.get('location')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        preferences = data.get('preferences', [])
        target_date = data.get('date')
        
        if not location and (not latitude or not longitude):
            return jsonify({
                'error': True,
                'reason': 'Either location OR (latitude AND longitude) is required'
            }), 400
        
        if not latitude or not longitude:
            geocode_params = {
                'name': location,
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
                    'reason': f'Could not geocode location: {location}'
                }), 404
            
            latitude = geo_data['results'][0]['latitude']
            longitude = geo_data['results'][0]['longitude']
            location_name = geo_data['results'][0]['name']
        else:
            location_name = location if location else f"Location ({latitude}, {longitude})"
        
        weather_params = {
            'latitude': latitude,
            'longitude': longitude,
            'current_weather': 'true',
            'timezone': 'Asia/Tokyo'
        }
        
        if target_date:
            weather_params['start_date'] = target_date
            weather_params['end_date'] = target_date
        else:
            weather_params['forecast_days'] = 1
        
        weather_response = requests.get(WEATHER_API, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        current = weather_data.get('current_weather', {})
        condition = WEATHER_CONDITIONS.get(current.get('weathercode', 0), 'Unknown')
        temperature = current.get('temperature', 'N/A')
        
        prompt = f"""You are a music-focused local guide for Japan. Generate EXACTLY 5 diverse music activity suggestions.

Location: {location_name}
Weather: {condition}, {temperature}°C
User Preferences: {', '.join(preferences) if preferences else 'None'}
User Query: {user_query}

Provide 5 activities with a good mix:
- 2 venues (live music clubs, concert halls)
- 1 shopping (record stores)
- 1 playlist/streaming activity
- 1 cafe or practice activity

Include real venues: Tower Records, Blue Note Tokyo, Billboard Live, Disk Union, Shibuya WWW, etc.

Return ONLY valid JSON (no markdown):

{{
  "suggestions": [
    {{
      "id": "sug_1",
      "title": "活動タイトル（日本語）",
      "title_en": "Activity Title (English)",
      "type": "venue|shopping|playlist|food|cafe|practice",
      "description": "詳細な説明を日本語で2-3文で記載。具体的な魅力や特徴を含める。",
      "description_en": "Detailed 2-3 sentence description in English including specific appeal and features.",
      "venue": "Venue name or null",
      "address": "Full address or null",
      "weather_match": "Why this activity suits the current weather conditions",
      "link": "https://example.com or null",
      "estimated_cost": "¥X,XXX-X,XXX or Free",
      "duration": "X-X hours",
      "best_time": "morning|afternoon|evening|anytime"
    }}
  ]
}}

CRITICAL: Return EXACTLY 5 suggestions with detailed, engaging descriptions."""

        suggestions = call_gemini_streaming(prompt)
        
        try:
            suggestions_text = suggestions.strip()
            
            if suggestions_text.startswith('```'):
                parts = suggestions_text.split('```')
                if len(parts) >= 3:
                    suggestions_text = parts[1]
                    if suggestions_text.startswith('json'):
                        suggestions_text = suggestions_text[4:].strip()
            
            suggestions_json = json.loads(suggestions_text)
            
            if 'suggestions' not in suggestions_json:
                return jsonify({
                    'error': True,
                    'reason': 'Invalid response: missing "suggestions" field',
                    'raw_response': suggestions[:1000]
                }), 500
            
            if len(suggestions_json['suggestions']) > 5:
                suggestions_json['suggestions'] = suggestions_json['suggestions'][:5]
            elif len(suggestions_json['suggestions']) < 5:
                return jsonify({
                    'error': True,
                    'reason': f'Only {len(suggestions_json["suggestions"])} suggestions generated',
                    'partial_data': suggestions_json
                }), 500
            
        except json.JSONDecodeError as e:
            return jsonify({
                'error': True,
                'reason': f'Failed to parse response: {str(e)}',
                'raw_response': suggestions[:2000]
            }), 500
        
        result = {
            'success': True,
            'query': {
                'location': location_name,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'date': target_date if target_date else 'today',
                'weather': condition,
                'temperature': temperature,
                'user_query': user_query,
                'preferences': preferences
            },
            'suggestions': suggestions_json['suggestions'],
            'llm_provider': 'gemini'
        }
        
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': True,
            'reason': 'API request timed out'
        }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': True,
            'reason': f'External API error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'reason': f'Internal server error: {str(e)}'
        }), 500