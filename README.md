# Weather Query Web Application

A Django-based weather application that fetches current weather data from OpenWeatherMap API.

Please write the names of cities in English!

## Features

- 🌤️ Real-time weather data from OpenWeatherMap
- 📊 Query history with filters & pagination  
- ⚡ 5-minute caching with Redis
- 🛡️ Rate limiting (30 requests/minute)
- 📁 CSV export functionality
- ❤️ Health check endpoint
- 🐳 Docker containerization
- 🧪 Comprehensive test coverage

## 🛠  Quick Start with Docker 🛠  


```bash
# Clone the repository
git clone https://github.com/Diarqq/weather_project
cd weather_project

# Start all services
docker-compose up

# Access the application
open http://localhost:8000

Note: Django logs will show http://0.0.0.0:8000 - this is normal container behavior.

## 🚀 API Endpoints

### Web Interface
- `GET /` - Weather query form
- `POST /` - Submit weather query
- `GET /history/` - Query history with filters
- `GET /history/export/` - Export history as CSV

### JSON API
- `GET /api/?city=London&units=metric` - Get weather data
- `GET /health/` - System health status

### TESTS
docker-compose up -d       
docker-compose exec web python -m pytest -v
