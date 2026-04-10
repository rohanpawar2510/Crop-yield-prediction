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

#### Train ML Models

The **single authoritative dataset** is `notebooks/Final_Agriculture_Dataset_V2.csv`.
Pre-trained model files are included in `backend/models/`. To retrain them:

```bash
# From the repository root (run once from any directory)
cd backend
python train_models.py
```

This canonical script:
- Reads `notebooks/Final_Agriculture_Dataset_V2.csv` — fails with a clear error if missing
- Estimates humidity from temperature and rainfall (no extra data step needed)
- Removes ambiguous data rows and rare crops, balances the dataset
- Adds five engineered features (NPK totals, climate score, etc.)
- Splits train/test **before** fitting the scaler (no data leakage)
- Embeds the scaler inside a `Pipeline` for leak-free cross-validation
- Reports train accuracy, test accuracy, 5-fold CV score, and classification report

**Expected output:**

```
  Crop test acc     : 100.00%
  Crop 5-fold CV    : 1.0000 ± 0.0000
  ✓ Accuracy target (≥ 90 %) MET
```

**Artefacts saved to `backend/models/`:**

| File | Description |
|------|-------------|
| `crop_model.pkl` | `Pipeline(StandardScaler + RandomForestClassifier)` |
| `yield_model.pkl` | `RandomForestRegressor` |
| `label_encoder.pkl` | `LabelEncoder` for crop class names |
| `scaler_yield.pkl` | `StandardScaler` fitted on yield training split |
| `feature_cols.pkl` | Feature column lists for crop and yield models |
| `metadata.json` | Training metrics (accuracy, CV score, class names) |

#### (Optional) Advanced Cleaning + Improved Training

For even deeper control over the cleaning pipeline:

```bash
# Step 1 — Run aggressive 8-step data cleaning
python scripts/ultimate_data_cleaner.py
# Input:  notebooks/Final_Agriculture_Dataset_V2.csv  (single source)
# Output: notebooks/Crop_recommendation_final.csv (~8,000–12,000 rows)

# Step 2 — Train optimized models on the cleaned dataset
cd backend
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
├── scripts/
│   ├── clean_and_improve_dataset.py   # Cleans data, removes outliers, adds engineered features
│   ├── ultimate_data_cleaner.py       # Aggressive 8-step cleaning for maximum accuracy
│   ├── feature_engineering.py         # Reusable feature engineering utilities
│   ├── data_analysis_report.py        # Comprehensive data quality & analysis report
│   └── README.md                      # Script documentation
├── notebooks/
│   └── Final_Agriculture_Dataset_V2.csv     # Single authoritative source dataset
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment and app configuration
│   ├── train_models.py          # ← CANONICAL training script (use this)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Example environment variables
│   ├── models/                  # Trained model artefacts
│   │   ├── crop_model.pkl       # Pipeline(StandardScaler + RandomForest)
│   │   ├── yield_model.pkl      # RandomForestRegressor
│   │   ├── label_encoder.pkl    # LabelEncoder for crop names
│   │   ├── scaler_yield.pkl     # Yield feature scaler
│   │   ├── feature_cols.pkl     # Feature column metadata
│   │   └── metadata.json        # Training metrics
│   └── .gitignore
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
| `Dataset not found` on training | Ensure `notebooks/Final_Agriculture_Dataset_V2.csv` exists in the repository |
