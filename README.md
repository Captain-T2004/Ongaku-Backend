# Music-Weather Voice Assistant - Ongaku - Backend API

## Project Structure

```
project/
├── app.py                  # Main application entry point
├── config.py              # Configuration and constants
├── utils.py               # Shared utility functions
├── routes/
│   ├── __init__.py       # Makes routes a package
│   ├── health.py         # Health check endpoint
│   ├── geocode.py        # Geocoding endpoint
│   ├── weather.py        # Weather data endpoint
│   ├── suggest.py        # Quick suggestions endpoint
│   └── itinerary.py      # Itinerary planning endpoint
└── README.md             # This file
```

## Tech Stack

### Backend: Python 3.8+, Flask
### AI/ML: Google Gemini 2.0
### Weather Data: Open-Meteo (JMA model)
### Geocoding: Open-Meteo Geocoding API
### Frontend: React (separate repository)

## Changes Made

### 1. **Split into Multiple Files**
   - Separated routes into individual blueprint modules
   - Extracted configuration into `config.py`
   - Moved utility functions to `utils.py`

### 2. **Removed Unnecessary Code**
   - Removed unused imports
   - Removed commented-out code blocks
   - Removed verbose documentation comments (kept essential ones)
   - Removed unused exception classes and handlers

### 3. **Maintained Full Functionality**
   - All 5 endpoints work exactly as before
   - No API changes
   - Same request/response formats
   - Same error handling

## Setup Instructions

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Set environment variable:
```bash
export GEMINI_API_KEY='your_api_key_here'
```

### 3. Run the application:
```bash
python app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/geocode` | Convert city name to coordinates |
| GET | `/api/weather` | Get weather forecast |
| POST | `/api/suggest-quick` | Generate 5 music activity suggestions |
| POST | `/api/itinerary` | Generate detailed day-by-day itinerary |

## Benefits of Refactored Structure

1. **Maintainability**: Each route is in its own file, making it easier to find and modify
2. **Scalability**: Easy to add new routes without cluttering a single file
3. **Organization**: Clear separation of concerns (config, utils, routes)
4. **Readability**: Smaller files are easier to understand and navigate
5. **Testing**: Individual routes can be tested in isolation

## Notes

- All functionality is preserved
- No breaking changes to the API
- Flask blueprints used for modular routing
- Configuration centralized in `config.py`
- Shared utilities in `utils.py`