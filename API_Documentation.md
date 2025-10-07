# 🎵 Ongaku - Music Voice Assistant API Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Geocode](#geocode-api)
   - [Weather](#weather-api)
   - [Quick Suggestions](#quick-suggestions-api)
   - [Itinerary Planning](#itinerary-planning-api)
5. [Data Models](#data-models)
6. [Test Examples](#code-examples)

***

## Overview

This Music-Weather Voice Assistant API provides intelligent, weather-aware music activity recommendations for Japan. It combines real-time weather data, AI-powered suggestions, and voice transcription to create personalized music itineraries.

**Key Features:**
- 🌤️ Real-time weather data for Japanese cities (JMA model)
- 🎵 AI-powered - music venue and activity suggestions
- 📅 Multi-day itinerary planning with weather optimization
- 🎤 Japanese audio transcription
- 🌍 Geocoding support for Japanese and English city names
- 🗣️ Bilingual support (Japanese/English)

***

## Authentication

**Current Version:** No authentication required

**Required API Keys (Server-side):**
- `GEMINI_API_KEY` - For AI suggestions and itinerary generation

***

## Error Handling

All endpoints return consistent error responses:

**Error Response Format:**
```json
{
  "error": true,
  "reason": "Detailed error message in English or Japanese"
}
```

**HTTP Status Codes:**

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Missing or invalid parameters |
| 404 | Not Found | Location not found, resource doesn't exist |
| 500 | Internal Server Error | API key issues, server errors |
| 504 | Gateway Timeout | External API timeout |

***

## Endpoints

### Health Check

**Check API status and view available endpoints**

**Endpoint:** `GET /health`

**Request:**
```bash
curl http://$BACKEND_URL/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-08T00:46:00.123456",
  "version": "1.0.0",
  "endpoints": {
    "health": "GET /health",
    "geocode": "GET /api/geocode?city=<city_name>",
    "weather": "GET /api/weather?city=<city>",
    "suggest": "POST /api/suggest-quick",
    "itinerary": "POST /api/itinerary",
    "transcribe": "POST /api/transcribe",
    "transcribe_url": "POST /api/transcribe-url"
  }
}
```

***

### Geocode API

**Convert city names to latitude/longitude coordinates**

**Endpoint:** `GET /api/geocode`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `city` | string | Yes | - | City name (Japanese or English) |
| `language` | string | No | `ja` | Response language (`ja` or `en`) |
| `country` | string | No | `jp` | ISO country code |

**Example Request:**
```bash
curl "http://$BACKEND_URL/api/geocode?city=大阪&language=ja"
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "location": {
    "id": 1853909,
    "name": "大阪市",
    "latitude": 34.6937,
    "longitude": 135.5023,
    "elevation": 24.0,
    "timezone": "Asia/Tokyo",
    "country": "Japan",
    "country_code": "JP",
    "admin1": "Ōsaka",
    "admin2": null,
    "population": 2592413,
    "postcodes": ["530-0001"]
  },
  "all_matches": [
    {
      "name": "大阪市",
      "latitude": 34.6937,
      "longitude": 135.5023,
      "admin1": "Ōsaka",
      "country": "Japan"
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": true,
  "reason": "No location found for: UnknownCity"
}
```

***

### Weather API

**Get current weather and 24-hour forecast for Japanese locations**

**Endpoint:** `GET /api/weather`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `city` | string | Yes* | - | City name |
| `latitude` | float | Yes* | - | Latitude coordinate |
| `longitude` | float | Yes* | - | Longitude coordinate |
| `timezone` | string | No | `Asia/Tokyo` | Timezone |

*Either `city` OR (`latitude` AND `longitude`) required

**Example Request:**
```bash
curl "http://$BACKEND_URL/api/weather?city=Tokyo"
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "location": {
    "name": "Tokyo",
    "latitude": 35.6895,
    "longitude": 139.69171,
    "timezone": "Asia/Tokyo"
  },
  "current": {
    "time": "2025-10-08T00:00",
    "temperature": 22.5,
    "windspeed": 12.3,
    "winddirection": 180,
    "weathercode": 2,
    "condition": "Partly cloudy"
  },
  "hourly_forecast": [
    {
      "time": "2025-10-08T00:00",
      "temperature": 22.5,
      "precipitation": 0.0,
      "weathercode": 2,
      "condition": "Partly cloudy",
      "windspeed": 12.3,
      "humidity": 65
    }
  ],
  "units": {
    "temperature": "°C",
    "precipitation": "mm",
    "windspeed": "km/h",
    "humidity": "%"
  }
}
```

**Weather Codes:**

| Code | Condition |
|------|-----------|
| 0 | Clear sky |
| 1 | Mainly clear |
| 2 | Partly cloudy |
| 3 | Overcast |
| 61 | Slight rain |
| 63 | Moderate rain |
| 65 | Heavy rain |
| 95 | Thunderstorm |

***

### Quick Suggestions API

**Get 5 music activity suggestions quickly (5-10 seconds)**

**Endpoint:** `POST /api/suggest-quick`

**Content-Type:** `application/json`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `location` | string | Yes* | City name |
| `latitude` | float | Yes* | Latitude |
| `longitude` | float | Yes* | Longitude |
| `user_query` | string | No | User's natural language query |
| `preferences` | array | No | Music genres (e.g., ["jazz", "rock"]) |
| `date` | string | No | Date (YYYY-MM-DD), defaults to today |
| `language` | string | No | Response language (`ja` or `en`), default: `ja` |

*Either `location` OR (`latitude` AND `longitude`) required

**Example Request:**
```bash
curl -X POST http://$BACKEND_URL/api/suggest-quick \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Osaka",
    "preferences": ["jazz", "indie"],
    "language": "en"
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "query": {
    "location": "大阪市",
    "prefecture": "Ōsaka",
    "latitude": 34.6937,
    "longitude": 135.5023,
    "date": "today",
    "weather": "Partly cloudy",
    "temperature": 22.5,
    "user_query": "",
    "preferences": ["jazz", "indie"]
  },
  "suggestions": [
    {
      "id": "sug_1",
      "title": "Billboard Live OSAKAでジャズライブ",
      "title_en": "Jazz Live at Billboard Live OSAKA",
      "type": "venue",
      "description": "世界的アーティストが出演する高級ジャズクラブ。食事をしながら本格的なライブを楽しめる。",
      "description_en": "Premium jazz club featuring world-class artists. Enjoy live performances while dining.",
      "venue": "Billboard Live OSAKA",
      "address": "2-3-21 Umeda, Kita-ku, Osaka",
      "weather_match": "Indoor venue, perfect for any weather",
      "link": "https://www.billboard-live.com/pg/shop/show/index.php?mode=top&shop=2",
      "estimated_cost": "¥8,000-15,000",
      "duration": "2-3 hours",
      "best_time": "evening"
    },
    {
      "id": "sug_2",
      "title": "タワーレコード梅田店でレコード探し",
      "title_en": "Record Hunting at Tower Records Umeda",
      "type": "shopping",
      "description": "関西最大級のタワーレコード。インディー、ジャズの品揃えが豊富。",
      "description_en": "Kansai's largest Tower Records with extensive indie and jazz collections.",
      "venue": "Tower Records Umeda",
      "address": "1-10-12 Chayamachi, Kita-ku, Osaka",
      "weather_match": "Indoor shopping, ideal for rainy weather",
      "link": "https://tower.jp/store/kansai/umeda",
      "estimated_cost": "¥1,500-8,000",
      "duration": "1.5-2 hours",
      "best_time": "afternoon"
    }
  ],
  "llm_provider": "gemini"
}
```

**Activity Types:**
- `venue` - Live music venues, concert halls
- `shopping` - Record stores, music shops
- `playlist` - Streaming playlists, music curation
- `cafe` - Music cafes, listening bars
- `practice` - Home music practice/creation

***

### Itinerary Planning API

**Generate detailed day-by-day itinerary (15-30 seconds)**

**Endpoint:** `POST /api/itinerary`

**Content-Type:** `application/json`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `location` | string | Yes* | City name |
| `latitude` | float | Yes* | Latitude |
| `longitude` | float | Yes* | Longitude |
| `date` | string | No | Start date (YYYY-MM-DD), defaults to today |
| `duration_days` | integer | No | Number of days (1-7), default: 1 |
| `preferences` | array | No | Music genres |
| `user_query` | string | No | User's query |
| `language` | string | No | Response language (`ja` or `en`), default: `ja` |

*Either `location` OR (`latitude` AND `longitude`) required

**Example Request:**
```bash
curl -X POST http://$BACKEND_URL/api/itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Osaka",
    "date": "2025-10-12",
    "duration_days": 2,
    "preferences": ["jazz", "indie"],
    "language": "en"
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "query": {
    "location": "大阪市",
    "prefecture": "Ōsaka",
    "latitude": 34.6937,
    "longitude": 135.5023,
    "start_date": "2025-10-12",
    "end_date": "2025-10-13",
    "duration_days": 2,
    "preferences": ["jazz", "indie"],
    "user_query": "",
    "language": "en"
  },
  "weather_summary": [
    {
      "date": "2025-10-12",
      "morning": {
        "condition": "Partly cloudy",
        "temperature": 18.5,
        "precipitation": 0.0
      },
      "afternoon": {
        "condition": "Clear sky",
        "temperature": 24.0,
        "precipitation": 0.0
      },
      "evening": {
        "condition": "Mainly clear",
        "temperature": 20.2,
        "precipitation": 0.0
      }
    }
  ],
  "itinerary": [
    {
      "day": 1,
      "date": "2025-10-12",
      "day_name": "土曜日",
      "day_name_en": "Saturday",
      "weather_overview": {
        "condition": "Mostly clear with pleasant temperatures",
        "condition_ja": "概ね晴れで過ごしやすい気温",
        "temp_range": "18-24°C",
        "advice": "Perfect for outdoor activities in afternoon",
        "advice_ja": "午後の屋外活動に最適"
      },
      "schedule": [
        {
          "time_slot": "09:00 - 10:30",
          "start_time": "09:00",
          "end_time": "10:30",
          "activity": "モーニングカフェで朝食",
          "activity_en": "Breakfast at Morning Cafe",
          "type": "food",
          "location": "珈琲屋 らんぷ 梅田店",
          "location_en": "Coffee Shop Lamp Umeda",
          "address": "5-2-2 Umeda, Kita-ku, Osaka",
          "description": "大阪名物のモーニングセットを楽しめる老舗喫茶店。",
          "description_en": "Historic coffee shop serving Osaka's signature morning sets.",
          "weather_at_time": {
            "condition": "Partly cloudy",
            "condition_ja": "一部曇り",
            "temperature": 18.5,
            "precipitation": 0.0
          },
          "reason": "朝の穏やかな天気を室内で楽しみながらエネルギーチャージ",
          "reason_en": "Start day indoors while energizing",
          "cost": "¥600-1,200",
          "tips": "モーニングセットがお得。9時までに到着推奨。",
          "tips_en": "Morning sets are great value. Arrive by 9 AM.",
          "link": null,
          "estimated_duration": "90分",
          "estimated_duration_en": "90 minutes"
        }
      ],
      "daily_summary": {
        "ja": "晴天に恵まれた1日目は、レコードショッピングから始まり、夜はジャズライブで締めくくり。",
        "en": "Day 1 blessed with sunny weather starts with record shopping and concludes with jazz live."
      },
      "total_cost_estimate": "¥12,000-28,000",
      "total_duration": "9時間"
    }
  ],
  "llm_provider": "gemini"
}
```

**Schedule Activity Types:**
- `food` - Meals, cafes
- `venue` - Live music venues
- `shopping` - Record stores
- `cafe` - Music cafes
- `practice` - Music creation
- `transit` - Travel between locations

***

## Data Models

### Location Object
```typescript
{
  id: number
  name: string
  latitude: number
  longitude: number
  elevation: number
  timezone: string
  country: string
  country_code: string
  admin1: string          // Prefecture/State
  admin2: string | null   // District
  population: number
  postcodes: string[]
}
```

### Weather Object
```typescript
{
  time: string
  temperature: number    // °C
  precipitation: number  // mm
  weathercode: number    // WMO code
  condition: string      // Human-readable
  windspeed: number      // km/h
  humidity: number       // %
}
```

### Suggestion Object
```typescript
{
  id: string
  title: string              // Japanese
  title_en: string           // English
  type: "venue" | "shopping" | "playlist" | "food" | "cafe" | "practice"
  description: string        // Japanese
  description_en: string     // English
  venue: string | null
  address: string | null
  weather_match: string
  link: string | null
  estimated_cost: string
  duration: string
  best_time: "morning" | "afternoon" | "evening" | "anytime"
}
```

### Schedule Activity Object
```typescript
{
  time_slot: string          // "HH:MM - HH:MM"
  start_time: string         // "HH:MM"
  end_time: string           // "HH:MM"
  activity: string           // Japanese
  activity_en: string        // English
  type: "food" | "venue" | "shopping" | "cafe" | "practice" | "transit"
  location: string           // Japanese
  location_en: string        // English
  address: string
  description: string        // Japanese
  description_en: string     // English
  weather_at_time: {
    condition: string
    condition_ja: string
    temperature: number
    precipitation: number
  }
  reason: string             // Japanese
  reason_en: string          // English
  cost: string
  tips: string               // Japanese
  tips_en: string            // English
  link: string | null
  estimated_duration: string // Japanese
  estimated_duration_en: string  // English
}
```

***

# Testing Examples

### cURL

```bash
# Health Check
curl http://$BACKEND_URL/health

# Geocode
curl "http://$BACKEND_URL/api/geocode?city=Tokyo&language=en"

# Weather
curl "http://$BACKEND_URL/api/weather?city=Osaka"

# Quick Suggestions
curl -X POST http://$BACKEND_URL/api/suggest-quick \
  -H "Content-Type: application/json" \
  -d '{"location":"Tokyo","preferences":["jazz"],"language":"en"}'

# Itinerary
curl -X POST http://$BACKEND_URL/api/itinerary \
  -H "Content-Type: application/json" \
  -d '{"location":"Osaka","date":"2025-10-15","duration_days":2,"language":"en"}'

```

***

## Best Practices

### 1. Progressive Loading
For better UX, call endpoints sequentially:
```javascript
// Step 1: Quick suggestions (5-10s)
const suggestions = await getQuickSuggestions();
displaySuggestions(suggestions);

// Step 2: Detailed itinerary (15-30s) with loading indicator
showLoadingSpinner();
const itinerary = await getItinerary();
hideLoadingSpinner();
displayItinerary(itinerary);
```

### 2. Error Handling
Always check for errors and provide fallbacks:
```javascript
try {
  const response = await fetch('/api/suggest-quick', {...});
  const data = await response.json();
  
  if (!response.ok || data.error) {
    // Handle error
    showError(data.reason);
  } else {
    // Process success
    processData(data);
  }
} catch (error) {
  // Handle network errors
  showError('Network error. Please try again.');
}
```

***