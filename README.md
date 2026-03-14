# 🌾 Smart Agriculture - Crop Yield Prediction

AI-powered platform for crop yield prediction, disease detection, and farming recommendations.

## Features

- 🌾 **Crop Prediction** — ML-based prediction using N, P, K, temperature, humidity, pH, and rainfall
- 🌤️ **Weather** — Real-time weather data via OpenWeather API
- 🤖 **AI Recommendations** — Gemini AI-powered farming advice
- 🔬 **Disease Detection** — Plant disease detection from images

## Prerequisites

| Tool | Version |
|------|---------|
| **Python** | 3.9 or higher |
| **Node.js** | 18 or higher |
| **npm** | 9 or higher |

## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/rohanpawar2510/Crop-yield-prediction.git
cd Crop-yield-prediction
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# (Recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# Install Python dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```dotenv
OPENWEATHER_API_KEY=your_openweather_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:** The app will still start without API keys, but the Weather and AI Recommendations features will return mock/fallback data.

#### (Optional) Retrain ML Models

Pre-trained model files (`crop_model.pkl`, `yield_model.pkl`, `label_encoder.pkl`) are included in `backend/models/`. To retrain them:

```bash
python train_models.py
```

#### Start the Backend Server

```bash
python -m uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**. Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### 3. Frontend Setup

Open a **new terminal** and run:

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:3000** and will automatically proxy API calls to the backend at `http://localhost:8000`.

### 4. Open the Application

Open your browser and navigate to **http://localhost:3000** to use the Smart Agriculture Dashboard.

## Project Structure

```
Crop-yield-prediction/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment and app configuration
│   ├── train_models.py      # Script to train ML models
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Example environment variables
│   ├── models/
│   │   ├── schemas.py       # Pydantic request/response models
│   │   ├── crop_model.pkl   # Trained crop classifier
│   │   ├── yield_model.pkl  # Trained yield regressor
│   │   └── label_encoder.pkl
│   ├── routes/
│   │   ├── predict.py       # POST /api/predict
│   │   ├── weather.py       # GET  /api/weather
│   │   ├── disease.py       # POST /api/detect-disease
│   │   └── recommend.py     # POST /api/recommend
│   └── services/
│       ├── prediction_service.py
│       ├── weather_service.py
│       ├── disease_service.py
│       └── recommendation_service.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js       # Vite config with API proxy
    └── src/
        ├── App.jsx          # Root component with routing
        ├── main.jsx         # React entry point
        ├── services/api.js  # Axios API client
        ├── pages/           # Dashboard, Predict, Weather, Recommend, Disease
        └── components/      # Reusable UI components
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | API root with version info |
| `POST` | `/api/predict` | Predict crop and yield from soil data |
| `GET` | `/api/weather?location=...` | Get weather data for a location |
| `POST` | `/api/detect-disease` | Detect plant disease from leaf image |
| `POST` | `/api/recommend` | Get farming recommendations |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` in backend | Make sure you activated the virtual environment and ran `pip install -r requirements.txt` |
| Frontend shows network errors | Ensure the backend is running on port 8000 before starting the frontend |
| Weather returns mock data | Add a valid `OPENWEATHER_API_KEY` to `backend/.env` |
| Recommendations return fallback data | Add a valid `GEMINI_API_KEY` to `backend/.env` |
| Port already in use | Change the port: backend via `PORT` in `.env`, frontend in `vite.config.js` |
