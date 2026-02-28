# 🌾 Smart Agriculture - Crop Yield Prediction

AI-powered platform for crop yield prediction, disease detection, and farming recommendations.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000 and will proxy API calls to the backend at http://localhost:8000.

## Features
- 🌾 **Crop Prediction** — ML-based prediction using N, P, K, temperature, humidity, pH, and rainfall
- 🌤️ **Weather** — Real-time weather data via OpenWeather API
- 🤖 **AI Recommendations** — Gemini AI-powered farming advice
- 🔬 **Disease Detection** — Plant disease detection from images
