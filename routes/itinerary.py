from flask import Blueprint, request, jsonify
import requests
import json
import re
import traceback
from datetime import datetime, timedelta
from config import GEOCODING_API, WEATHER_API, WEATHER_CONDITIONS, GEMINI_API_KEY
from utils import call_gemini_streaming

bp = Blueprint('itinerary', __name__)

@bp.route('/api/itinerary', methods=['POST'])
def create_itinerary():
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
        
        location = data.get('location')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        target_date = data.get('date')
        duration_days = data.get('duration_days', 1)
        preferences = data.get('preferences', [])
        user_query = data.get('user_query', '')
        language = data.get('language', 'ja').lower()
        
        if language not in ['ja', 'en']:
            language = 'ja'
        
        try:
            duration_days = int(duration_days)
            if duration_days < 1:
                duration_days = 1
            elif duration_days > 7:
                duration_days = 7
        except (ValueError, TypeError):
            duration_days = 1
        
        if not location and (not latitude or not longitude):
            error_msg = {
                'ja': 'location または (latitude と longitude) が必要です',
                'en': 'Either location OR (latitude AND longitude) is required'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language],
                'received_data': {
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude
                }
            }), 400
        
        if not latitude or not longitude:
            geocode_params = {
                'name': location,
                'count': 1,
                'language': language,
                'country': 'jp'
            }
            
            try:
                geo_response = requests.get(GEOCODING_API, params=geocode_params, timeout=10)
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                
                if 'results' not in geo_data or len(geo_data['results']) == 0:
                    error_msg = {
                        'ja': f'場所が見つかりません: {location}。Tokyo、Osaka、Kyotoなどの英語の都市名を試してください',
                        'en': f'Could not find location: {location}. Try using city names like Tokyo, Osaka, or Kyoto'
                    }
                    return jsonify({
                        'error': True,
                        'reason': error_msg[language]
                    }), 404
                
                result = geo_data['results'][0]
                latitude = result['latitude']
                longitude = result['longitude']
                location_name = result['name']
                admin1 = result.get('admin1', '')
                
            except requests.exceptions.RequestException as e:
                error_msg = {
                    'ja': f'ジオコーディングに失敗しました: {str(e)}',
                    'en': f'Geocoding failed: {str(e)}'
                }
                return jsonify({
                    'error': True,
                    'reason': error_msg[language]
                }), 500
        else:
            location_name = location if location else f"Location ({latitude}, {longitude})"
            admin1 = ''
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if target_date:
            try:
                start_dt = datetime.strptime(target_date, '%Y-%m-%d')
                days_ahead = (start_dt.date() - today.date()).days
                
                if days_ahead < 0:
                    error_msg = {
                        'ja': f'過去の日付は計画できません。日付 {target_date} は過去です。',
                        'en': f'Cannot plan for past dates. Date {target_date} is in the past.'
                    }
                    return jsonify({
                        'error': True,
                        'reason': error_msg[language],
                        'today': today.strftime('%Y-%m-%d')
                    }), 400
                
                if days_ahead > 7:
                    error_msg = {
                        'ja': f'天気予報は7日先までしか利用できません。',
                        'en': f'Weather forecast only available up to 7 days ahead.'
                    }
                    return jsonify({
                        'error': True,
                        'reason': error_msg[language],
                        'requested_date': target_date,
                        'max_date': (today + timedelta(days=7)).strftime('%Y-%m-%d')
                    }), 400
                    
            except ValueError as e:
                error_msg = {
                    'ja': f'無効な日付形式: {target_date}。YYYY-MM-DD形式を使用してください（例：2025-10-12）',
                    'en': f'Invalid date format: {target_date}. Use YYYY-MM-DD format (e.g., 2025-10-12)'
                }
                return jsonify({
                    'error': True,
                    'reason': error_msg[language]
                }), 400
        else:
            start_dt = today
            target_date = start_dt.strftime('%Y-%m-%d')
        
        end_dt = start_dt + timedelta(days=duration_days - 1)
        end_date = end_dt.strftime('%Y-%m-%d')
        
        weather_params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': 'temperature_2m,precipitation,weathercode,windspeed_10m,relativehumidity_2m',
            'current_weather': 'true',
            'timezone': 'Asia/Tokyo',
            'start_date': target_date,
            'end_date': end_date
        }
        
        try:
            weather_response = requests.get(WEATHER_API, params=weather_params, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        except requests.exceptions.RequestException as e:
            error_msg = {
                'ja': f'天気APIに失敗しました: {str(e)}',
                'en': f'Weather API failed: {str(e)}'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language]
            }), 500
        
        hourly = weather_data.get('hourly', {})
        times = hourly.get('time', [])
        temps = hourly.get('temperature_2m', [])
        precip = hourly.get('precipitation', [])
        codes = hourly.get('weathercode', [])
        
        if not times or len(times) == 0:
            error_msg = {
                'ja': 'リクエストされた日付範囲の天気データが利用できません',
                'en': 'No weather data available for the requested date range'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language]
            }), 500
        
        daily_weather = {}
        for i in range(len(times)):
            date_key = times[i].split('T')[0]
            if date_key not in daily_weather:
                daily_weather[date_key] = []
            daily_weather[date_key].append({
                'time': times[i],
                'temperature': temps[i],
                'precipitation': precip[i],
                'weathercode': codes[i],
                'condition': WEATHER_CONDITIONS.get(codes[i], 'Unknown')
            })
        
        daily_summaries = []
        for date_key in sorted(daily_weather.keys()):
            hours = daily_weather[date_key]
            
            morning = next((h for h in hours if '09:00' in h['time']), hours[0] if hours else None)
            afternoon = next((h for h in hours if '14:00' in h['time']), hours[len(hours)//2] if hours else None)
            evening = next((h for h in hours if '18:00' in h['time']), hours[-1] if hours else None)
            
            if morning and afternoon and evening:
                daily_summaries.append({
                    'date': date_key,
                    'morning': {
                        'condition': morning['condition'],
                        'temperature': morning['temperature'],
                        'precipitation': morning['precipitation']
                    },
                    'afternoon': {
                        'condition': afternoon['condition'],
                        'temperature': afternoon['temperature'],
                        'precipitation': afternoon['precipitation']
                    },
                    'evening': {
                        'condition': evening['condition'],
                        'temperature': evening['temperature'],
                        'precipitation': evening['precipitation']
                    }
                })
        
        if not daily_summaries:
            error_msg = {
                'ja': '旅程計画のための天気データを解析できませんでした',
                'en': 'Could not parse weather data for itinerary planning'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language]
            }), 500
        
        weather_summary = "\n".join([
            f"Day {i+1} ({ds['date']}): "
            f"Morning {ds['morning']['condition']} {ds['morning']['temperature']:.1f}°C, "
            f"Afternoon {ds['afternoon']['condition']} {ds['afternoon']['temperature']:.1f}°C, "
            f"Evening {ds['evening']['condition']} {ds['evening']['temperature']:.1f}°C"
            for i, ds in enumerate(daily_summaries)
        ])
        
        day_names_ja = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']
        day_names_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if language == 'ja':
            prompt = f"""あなたは{location_name}の音楽専門の地元ガイドです。{location_name}での詳細な旅程を作成してください。

重要な場所の制約:
- すべての活動は{location_name}または5km圏内にある必要があります
- {location_name}にある実在の会場名と実在の住所を使用してください
- 他の都市の会場は含めないでください

場所の詳細:
- 都市: {location_name}
- 都道府県: {admin1}
- 期間: {target_date}から{duration_days}日間

ユーザーコンテキスト:
- 好み: {', '.join(preferences) if preferences else 'なし'}
- クエリ: {user_query}

## {location_name}の天気予報:
{weather_summary}

{location_name}の会場のみを使用したリアルな予定を作成してください:
- 雨の時は屋内の活動を予定
- 良い天気の時は屋外の活動を予定
- {location_name}のレストランで食事を含める
- 移動時間は最大15〜30分
- 各活動は1〜3時間

有効なJSONのみを返してください（マークダウンなし）。日本語フィールドは日本語で、英語フィールドは英語で記入してください:

{{
  "itinerary": [
    {{
      "day": 1,
      "date": "{target_date}",
      "day_name": "{day_names_ja[start_dt.weekday()]}",
      "day_name_en": "{day_names_en[start_dt.weekday()]}",
      "weather_overview": {{
        "condition": "Overall weather in English",
        "condition_ja": "全体的な天気を日本語で",
        "temp_range": "XX-XX°C",
        "advice": "Weather advice in English",
        "advice_ja": "天気のアドバイスを日本語で"
      }},
      "schedule": [
        {{
          "time_slot": "HH:MM - HH:MM",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "activity": "{location_name}での活動（日本語で具体的に）",
          "activity_en": "Activity in {location_name} (English, specific)",
          "type": "food|venue|shopping|cafe|practice|transit",
          "location": "{location_name}にある場所の名前（日本語）",
          "location_en": "Location name in {location_name} (English)",
          "address": "{location_name}の完全な住所（区を含む）",
          "description": "{location_name}のこの場所についての詳細な説明を日本語で2〜3文。",
          "description_en": "Detailed description of this place in {location_name} in English, 2-3 sentences.",
          "weather_at_time": {{
            "condition": "Weather condition",
            "condition_ja": "天気状態",
            "temperature": XX.X,
            "precipitation": X.X
          }},
          "reason": "なぜこの時間にこの活動を予定したか（天気を考慮）",
          "reason_en": "Why scheduled at this time (weather considered)",
          "cost": "¥X,XXX-X,XXX または Free",
          "tips": "実用的なヒント（予約方法、混雑回避など）",
          "tips_en": "Practical tips in English (reservations, avoiding crowds, etc.)",
          "link": "https://example.com or null",
          "estimated_duration": "XX分",
          "estimated_duration_en": "XX minutes"
        }}
      ],
      "daily_summary": {{
        "ja": "{location_name}でのこの日の活動全体のまとめを日本語で2〜3文",
        "en": "Overall summary of day's activities in {location_name} in English, 2-3 sentences"
      }},
      "total_cost_estimate": "¥XX,XXX-XX,XXX",
      "total_duration": "XX時間"
    }}
  ]
}}

{duration_days}日分を含めてください。各日は{location_name}での4〜6の活動を含みます。"""
        
        else:
            prompt = f"""You are a local music guide for {location_name}, Japan. Create a detailed itinerary for {location_name}.

CRITICAL LOCATION REQUIREMENTS:
- ALL activities must be in {location_name} or within 5km radius
- Use REAL venue names with REAL addresses in {location_name}
- DO NOT include venues from other cities

Location Details:
- City: {location_name}
- Prefecture: {admin1}
- Duration: {duration_days} days starting {target_date}

User Context:
- Preferences: {', '.join(preferences) if preferences else 'None'}
- Query: {user_query}

## Weather Forecast for {location_name}:
{weather_summary}

Create a realistic schedule using ONLY venues in {location_name}:
- Schedule indoor activities during rain
- Schedule outdoor activities during good weather
- Include meals at restaurants in {location_name}
- Travel time between locations: 15-30 minutes max
- Each activity: 1-3 hours

Return ONLY valid JSON (no markdown). Fill Japanese fields in Japanese and English fields in English:

{{
  "itinerary": [
    {{
      "day": 1,
      "date": "{target_date}",
      "day_name": "{day_names_ja[start_dt.weekday()]}",
      "day_name_en": "{day_names_en[start_dt.weekday()]}",
      "weather_overview": {{
        "condition": "Overall weather condition in English",
        "condition_ja": "天気の概要を日本語で",
        "temp_range": "XX-XX°C",
        "advice": "Weather-based activity advice in English",
        "advice_ja": "天気に基づくアドバイスを日本語で"
      }},
      "schedule": [
        {{
          "time_slot": "HH:MM - HH:MM",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "activity": "{location_name}での活動を日本語で",
          "activity_en": "Activity in {location_name} (English, specific)",
          "type": "food|venue|shopping|cafe|practice|transit",
          "location": "{location_name}の場所名を日本語で",
          "location_en": "Location name in {location_name} in English",
          "address": "Complete address in {location_name} with ward/district",
          "description": "{location_name}のこの場所の説明を日本語で2〜3文",
          "description_en": "Detailed 2-3 sentence description of this place in {location_name} in English",
          "weather_at_time": {{
            "condition": "Weather condition at this time",
            "condition_ja": "この時間の天気",
            "temperature": XX.X,
            "precipitation": X.X
          }},
          "reason": "この時間に予定した理由を日本語で",
          "reason_en": "Why scheduled at this time in English (weather considered)",
          "cost": "¥X,XXX-X,XXX or Free",
          "tips": "実用的なヒントを日本語で",
          "tips_en": "Practical tips in English (reservations, crowds, etc.)",
          "link": "https://example.com or null",
          "estimated_duration": "XX分",
          "estimated_duration_en": "XX minutes"
        }}
      ],
      "daily_summary": {{
        "ja": "この日のまとめを日本語で2〜3文",
        "en": "Overall summary of day's activities in {location_name} in English, 2-3 sentences"
      }},
      "total_cost_estimate": "¥XX,XXX-XX,XXX",
      "total_duration": "XX時間"
    }}
  ]
}}

Include {duration_days} day(s), each with 4-6 activities in {location_name}."""
        
        try:
            itinerary_response = call_gemini_streaming(prompt)
        except Exception as e:
            error_msg = {
                'ja': f'LLM生成に失敗しました: {str(e)}',
                'en': f'LLM generation failed: {str(e)}'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language]
            }), 500
        
        try:
            itinerary_text = itinerary_response.strip()
            
            if itinerary_text.startswith('```'):
                parts = itinerary_text.split('```')
                if len(parts) >= 3:
                    itinerary_text = parts[1]
                    if itinerary_text.startswith('json'):
                        itinerary_text = itinerary_text[4:].strip()
            
            if not itinerary_text.startswith('{'):
                json_match = re.search(r'\{.*\}', itinerary_text, re.DOTALL)
                if json_match:
                    itinerary_text = json_match.group(0)
            
            itinerary_json = json.loads(itinerary_text)
            
            if 'itinerary' not in itinerary_json:
                error_msg = {
                    'ja': '無効な応答: "itinerary"フィールドがありません',
                    'en': 'Invalid response: missing "itinerary" field'
                }
                return jsonify({
                    'error': True,
                    'reason': error_msg[language],
                    'raw_response_preview': itinerary_response[:1000]
                }), 500
            
            if not isinstance(itinerary_json['itinerary'], list) or len(itinerary_json['itinerary']) == 0:
                error_msg = {
                    'ja': '無効な応答: itineraryが空またはリストではありません',
                    'en': 'Invalid response: itinerary is empty or not a list'
                }
                return jsonify({
                    'error': True,
                    'reason': error_msg[language],
                    'raw_response_preview': itinerary_response[:1000]
                }), 500
            
        except json.JSONDecodeError as e:
            error_msg = {
                'ja': f'LLM応答をJSONとして解析できませんでした: {str(e)}',
                'en': f'Failed to parse LLM response as JSON: {str(e)}'
            }
            return jsonify({
                'error': True,
                'reason': error_msg[language],
                'parse_error_position': e.pos if hasattr(e, 'pos') else 'unknown',
                'raw_response_preview': itinerary_response[:2000]
            }), 500
        
        result = {
            'success': True,
            'query': {
                'location': location_name,
                'prefecture': admin1,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'start_date': target_date,
                'end_date': end_date,
                'duration_days': duration_days,
                'preferences': preferences,
                'user_query': user_query,
                'language': language
            },
            'weather_summary': daily_summaries,
            'itinerary': itinerary_json['itinerary'],
            'llm_provider': 'gemini'
        }
        
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        error_msg = {
            'ja': 'APIリクエストがタイムアウトしました。duration_daysを減らすかリクエストを簡素化してください。',
            'en': 'API request timed out. Try reducing duration_days or simplifying the request.'
        }
        return jsonify({
            'error': True,
            'reason': error_msg.get(language, error_msg['en'])
        }), 504
    except Exception as e:
        error_msg = {
            'ja': f'内部サーバーエラー: {str(e)}',
            'en': f'Internal server error: {str(e)}'
        }
        return jsonify({
            'error': True,
            'reason': error_msg.get(language, error_msg['en']),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500