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

#### (Optional) Prepare the Dataset

The training dataset (`notebooks/Crop_recommendation.csv`) needs a `humidity`
column that is not present in the raw source file.  Run the provided script to
add it before (re-)training:

```bash
# From the repository root
cd scripts

# Install script dependencies (once)
pip install pandas requests python-dotenv

# Copy and configure the environment file
cp .env.example .env
# Edit .env and set OPENWEATHER_API_KEY=<your free key from openweathermap.org>

# Run the script
python add_humidity_to_csv.py
# Or without an API key (uses estimation):
python add_humidity_to_csv.py --fallback-only
```

This reads `notebooks/Crop_Final_Updated.csv`, fetches humidity data for each
Maharashtra district from the OpenWeather API (with automatic fallback to an
estimation formula), and writes `notebooks/Crop_recommendation.csv` — the file
expected by `train_models.py`.

See [`scripts/README.md`](scripts/README.md) for full documentation.

#### (Optional) Retrain ML Models

Pre-trained model files (`crop_model.pkl`, `yield_model.pkl`, `label_encoder.pkl`) are included in `backend/models/`. To retrain them (requires the dataset step above):

```bash
python train_models.py
```

#### (Optional) Improve Model Accuracy

For significantly higher accuracy, run the data cleaning and improved training pipeline:

```bash
# Step 1 — Clean the dataset and add engineered features
python scripts/clean_and_improve_dataset.py
# Removes crops with < 50 samples, outliers beyond ±3σ, adds 5 new features
# Output: notebooks/Crop_recommendation_improved.csv (~29,700 rows, 31 crops)

# Step 2 — Train improved models
cd backend
python train_models_improved.py
# Uses StandardScaler, class weighting, better hyperparameters
# Output: backend/models/*_improved.pkl
```

You can also run a data quality analysis at any stage:

```bash
# Analyse the standard dataset
python scripts/data_analysis_report.py

# Analyse the cleaned dataset
python scripts/data_analysis_report.py \
    --input notebooks/Crop_recommendation_improved.csv
```

See [`scripts/README.md`](scripts/README.md) for full documentation on all data scripts.

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
├── scripts/
│   ├── add_humidity_to_csv.py         # Adds humidity column; produces Crop_recommendation.csv
│   ├── clean_and_improve_dataset.py   # Cleans data, removes outliers, adds engineered features
│   ├── feature_engineering.py         # Reusable feature engineering utilities
│   ├── data_analysis_report.py        # Comprehensive data quality & analysis report
│   ├── .env.example                   # Example env vars for the script
│   └── README.md                      # Script documentation
├── notebooks/
│   ├── Crop_Final_Updated.csv               # Raw dataset (source)
│   ├── Crop_recommendation.csv              # Processed dataset (with humidity)
│   └── Crop_recommendation_improved.csv     # Cleaned dataset (generated by clean script)
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment and app configuration
│   ├── train_models.py          # Script to train ML models (standard)
│   ├── train_models_improved.py # Script to train ML models (improved accuracy)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Example environment variables
│   ├── models/
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── crop_model.pkl       # Trained crop classifier
│   │   ├── yield_model.pkl      # Trained yield regressor
│   │   └── label_encoder.pkl
│   ├── routes/
│   │   ├── predict.py           # POST /api/predict
│   │   ├── weather.py           # GET  /api/weather
│   │   ├── disease.py           # POST /api/detect-disease
│   │   └── recommend.py         # POST /api/recommend
│   └── services/
│       ├── prediction_service.py
│       ├── weather_service.py
│       ├── disease_service.py
│       └── recommendation_service.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js           # Vite config with API proxy
    └── src/
        ├── App.jsx              # Root component with routing
        ├── main.jsx             # React entry point
        ├── services/api.js      # Axios API client
        ├── pages/               # Dashboard, Predict, Weather, Recommend, Disease
        └── components/          # Reusable UI components
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
