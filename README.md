# Weather Query Web Application

A Django-based weather application that fetches current weather data from OpenWeatherMap API.

## Features

- 🌤️ Real-time weather data from OpenWeatherMap
- 📊 Query history with filters & pagination  
- ⚡ 5-minute caching with Redis
- 🛡️ Rate limiting (30 requests/minute)
- 📁 CSV export functionality
- ❤️ Health check endpoint
- 🐳 Docker containerization
- 🧪 Comprehensive test coverage

## Quick Start with Docker

```bash
# Clone repository
git clone <your-repo-url>
cd weather_project

# Start with Docker Compose
docker-compose up
