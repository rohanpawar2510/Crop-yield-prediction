# 🌾 Smart Agriculture — Crop Yield Prediction

AI-powered platform for crop yield prediction, disease detection, weather monitoring, and smart farming recommendations.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Backend — API & Services](#backend--api--services)
- [Frontend — Pages & Components](#frontend--pages--components)
- [Work Completed](#work-completed)
- [Current Status & Future Phases](#current-status--future-phases)

---

## Features

| Feature | Description |
|---------|-------------|
| 🌾 **Crop Yield Prediction** | Predict the best crop and expected yield using soil parameters (N, P, K, pH) and climate data (temperature, humidity, rainfall) |
| 🌤️ **Real-Time Weather** | Fetch live weather data for any location via the OpenWeather API, with graceful mock-data fallback |
| 🤖 **AI Recommendations** | Get personalized fertilizer, irrigation, crop-rotation, and pest-management advice powered by Google Gemini AI |
| 🔬 **Disease Detection** | Upload a plant leaf image to detect diseases and receive treatment recommendations |
| 🌙 **Dark Mode** | Full dark/light theme support with system preference detection and manual toggle |
| 📊 **Interactive Charts** | NPK doughnut chart, soil radar chart, yield comparison bar chart, and feature importance chart |

---

## Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI library |
| **Vite 5** | Build tool and dev server |
| **Tailwind CSS 3** | Utility-first CSS framework |
| **React Router v6** | Client-side routing |
| **Chart.js + react-chartjs-2** | Interactive data visualizations (Doughnut, Bar, Radar charts) |
| **Framer Motion** | Page transitions and animations |
| **Axios** | HTTP client for API calls |
| **Lucide React** | Icon library |
| **React Hot Toast** | Toast notifications |

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Python web framework for the REST API |
| **Uvicorn** | ASGI server |
| **Pydantic v2** | Request/response validation and serialization |
| **httpx** | HTTP client for the OpenWeather API |
| **google-generativeai** | Google Gemini AI SDK for smart recommendations |
| **python-dotenv** | Environment variable management |
| **python-multipart** | Multipart form parsing (image uploads) |

---

## Project Structure

```
Crop-yield-prediction/
├── backend/
│   ├── main.py                          # FastAPI app entry point, CORS, router registration
│   ├── config.py                        # Environment config (API keys, model path, port)
│   ├── requirements.txt                 # Python dependencies
│   ├── .env.example                     # Template for environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                   # Pydantic request/response models for all endpoints
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── predict.py                   # POST /api/predict
│   │   ├── weather.py                   # GET  /api/weather
│   │   ├── disease.py                   # POST /api/detect-disease
│   │   └── recommend.py                 # POST /api/recommend
│   └── services/
│       ├── __init__.py
│       ├── prediction_service.py        # Crop yield prediction logic
│       ├── weather_service.py           # OpenWeather API integration + fallback
│       ├── disease_service.py           # Plant disease detection logic
│       └── recommendation_service.py    # Gemini AI recommendation engine
├── frontend/
│   ├── index.html                       # HTML entry point
│   ├── package.json                     # Node dependencies and scripts
│   ├── vite.config.js                   # Vite config with API proxy
│   ├── tailwind.config.js              # Tailwind theme (colors, fonts)
│   ├── postcss.config.js               # PostCSS config
│   └── src/
│       ├── main.jsx                     # React DOM root
│       ├── App.jsx                      # App shell with routing, sidebar, navbar
│       ├── index.css                    # Tailwind directives + custom utility classes
│       ├── context/
│       │   └── ThemeContext.jsx          # Dark/light theme context provider
│       ├── hooks/
│       │   └── useWeather.js            # Custom hook for weather data fetching
│       ├── services/
│       │   └── api.js                   # Axios API client (predict, weather, recommend, disease)
│       ├── pages/
│       │   ├── Dashboard.jsx            # Home dashboard with weather, stats, quick actions
│       │   ├── Predict.jsx              # Crop yield prediction page
│       │   ├── Weather.jsx              # Weather lookup page
│       │   ├── Recommend.jsx            # AI recommendations page
│       │   └── Disease.jsx              # Disease detection page
│       └── components/
│           ├── Navbar.jsx               # Top navigation bar with branding and dark mode toggle
│           ├── Sidebar.jsx              # Side navigation with route links
│           ├── DarkModeToggle.jsx       # Sun/Moon theme toggle button
│           ├── PredictionForm.jsx       # Input form for crop prediction parameters
│           ├── WeatherCard.jsx          # Weather data display card
│           ├── StatsCard.jsx            # Reusable stats display card
│           ├── LoadingSkeleton.jsx      # Shimmer loading placeholder
│           ├── NPKChart.jsx             # Doughnut chart for NPK distribution
│           ├── SoilRadarChart.jsx       # Radar chart for soil & climate profile
│           ├── YieldComparisonChart.jsx # Horizontal bar chart comparing crop yields
│           ├── FeatureImportanceChart.jsx # Bar chart showing ML feature importance
│           ├── DiseaseDetection.jsx     # Image upload + disease analysis component
│           └── RecommendationPanel.jsx  # Accordion panel for AI recommendations
└── README.md
```

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt

# Copy .env.example to .env and fill in your API keys
cp .env.example .env

python -m uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend runs at **http://localhost:3000** and proxies `/api` requests to the backend at **http://localhost:8000**.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | For live weather | API key from [OpenWeatherMap](https://openweathermap.org/api) |
| `GEMINI_API_KEY` | For AI recommendations | API key from [Google AI Studio](https://aistudio.google.com/) |
| `GEMINI_MODEL` | No (default: `gemini-2.0-flash`) | Gemini model name |
| `MODEL_PATH` | No (default: `models/crop_yield_model.pkl`) | Path to trained ML model |
| `PORT` | No (default: `8000`) | Backend server port |

---

## Backend — API & Services

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API root — returns version info and available routes |
| `GET` | `/health` | Health-check endpoint (returns `{"status": "ok"}`) |
| `POST` | `/api/predict` | Predict crop yield from soil and climate parameters |
| `GET` | `/api/weather?location=<city>` | Fetch real-time weather data for a location |
| `POST` | `/api/detect-disease` | Upload a leaf image for disease detection |
| `POST` | `/api/recommend` | Get AI-powered farming recommendations |

### Service Layer

1. **`prediction_service.py`** — Accepts N, P, K, pH, temperature, humidity, and rainfall values. Returns the recommended crop, expected yield (tons/hectare), confidence score, list of suitable crops, and a yield comparison array. *(Currently returns mock data; Phase 2 will integrate a trained ML model.)*

2. **`weather_service.py`** — Calls the OpenWeather API with the user's location. Parses temperature, humidity, wind speed (converted m/s → km/h), rainfall, pressure, visibility, feels-like temperature, and a weather icon emoji. Falls back gracefully to mock data on any API error.

3. **`disease_service.py`** — Accepts uploaded leaf image bytes and returns disease name, confidence, severity, affected area, and treatment recommendations. *(Currently returns mock data; Phase 4 will integrate a computer-vision model.)*

4. **`recommendation_service.py`** — Sends soil data to Google Gemini AI with a detailed prompt template requesting JSON-formatted recommendations for fertilizer, crop rotation, irrigation, pest management, and general advice. Parses the AI response and falls back to mock data if the API key is missing or the response is invalid.

### Pydantic Schemas

All request and response models are defined in `models/schemas.py`:

- **`SoilInput`** — Shared input model with validation constraints (e.g., nitrogen 0–140, pH 0–14)
- **`PredictResponse`** — Crop, yield, unit, confidence, suitable crops, yield comparison
- **`WeatherResponse`** — Temperature, humidity, rainfall, wind speed, description, icon, feels-like, pressure, visibility
- **`DiseaseResponse`** — Detected flag, disease name, confidence, severity, affected area, treatment
- **`RecommendResponse`** / **`FertilizerDetail`** — Nested recommendation structure with fertilizer details
- **`HealthResponse`** / **`RootResponse`** — System endpoints

---

## Frontend — Pages & Components

### Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | Landing page with weather search, stats cards (temperature, humidity, wind, rainfall), weather card, quick-action buttons, NPK chart, and farming tips |
| **Predict** | `/predict` | Prediction form (8 input fields), recommended crop display with confidence bar, NPK chart, soil radar chart, yield comparison chart, and feature importance chart |
| **Weather** | `/weather` | Weather search by city, detailed weather card, stats cards, and extra metrics (feels-like, pressure, visibility, condition) |
| **Recommend** | `/recommend` | Farm parameter form (5 fields), NPK chart, and accordion-style AI recommendation panel |
| **Disease** | `/disease` | Drag-and-drop or click-to-upload image area, preview, analyze button, and detection result card |

### Reusable Components

| Component | Description |
|-----------|-------------|
| **Navbar** | Fixed top bar with hamburger menu (mobile), brand logo, and dark mode toggle |
| **Sidebar** | Persistent side navigation (desktop) / slide-out drawer (mobile) with 5 route links |
| **DarkModeToggle** | Theme toggle button (Sun ↔ Moon icons) with localStorage persistence |
| **PredictionForm** | 8-field form (location, N, P, K, temperature, humidity, pH, rainfall) with validation |
| **WeatherCard** | Weather summary with emoji icon, temperature, humidity, wind, and rainfall |
| **StatsCard** | Reusable metric card with icon, label, value, unit, and optional trend text |
| **LoadingSkeleton** | Shimmer animation placeholder during loading states |
| **NPKChart** | Chart.js Doughnut chart visualizing N, P, K proportions |
| **SoilRadarChart** | Chart.js Radar chart normalizing all 7 soil/climate parameters to 0–100 |
| **YieldComparisonChart** | Horizontal Bar chart comparing predicted yield across suitable crops |
| **FeatureImportanceChart** | Vertical Bar chart showing ML feature importance weights |
| **DiseaseDetection** | Image upload with drag-and-drop, preview, analyze trigger, and result display |
| **RecommendationPanel** | Animated accordion with 5 collapsible sections for AI recommendations |

### UI/UX Features

- **Dark Mode** — Full dark/light theme via Tailwind `dark:` classes, React context, and localStorage
- **Responsive Layout** — Mobile sidebar drawer + desktop persistent sidebar, responsive grid layouts
- **Animations** — Framer Motion page transitions, hover effects, staggered card reveals
- **Custom CSS** — Glass-card effects, gradient backgrounds, custom scrollbar, button and input utility classes
- **Toast Notifications** — Success/error toasts for all API interactions
- **API Proxy** — Vite dev server proxies `/api` to the backend, eliminating CORS issues in development

---

## Work Completed

### ✅ Phase 1 — Project Setup & Full-Stack Architecture
- Initialized the full-stack project with separate `backend/` and `frontend/` directories
- Set up **FastAPI** backend with modular router/service architecture
- Set up **React + Vite** frontend with Tailwind CSS, React Router, and Framer Motion
- Configured **CORS middleware** for cross-origin requests
- Configured **Vite proxy** so the frontend dev server forwards `/api` calls to the backend
- Created **Pydantic v2 schemas** with field validation for all API endpoints
- Created `.env.example` and `config.py` for centralized environment configuration
- Added `.gitignore` for Python, Node, IDE, and OS artifacts

### ✅ Phase 1.5 — Dashboard & Navigation
- Built a **responsive Navbar** with hamburger menu for mobile, brand logo, and dark mode toggle
- Built a **persistent Sidebar** with route links (Dashboard, Weather, Predict, Recommend, Disease)
- Implemented **ThemeContext** with system preference detection, localStorage persistence, and class-based toggling
- Built the **Dashboard page** with weather search, stats cards, quick-action grid, NPK chart, and farming tips

### ✅ Phase 2 — Crop Yield Prediction (Mock)
- Created `POST /api/predict` endpoint with `SoilInput` validation
- Built `prediction_service.py` with mock response (placeholder for ML model integration)
- Built the **Predict page** with an 8-field PredictionForm component
- Displays recommended crop with confidence progress bar
- Added **NPKChart** (Doughnut), **SoilRadarChart** (Radar), **YieldComparisonChart** (Horizontal Bar), and **FeatureImportanceChart** (Vertical Bar)

### ✅ Phase 3 — Real-Time Weather Integration
- Created `GET /api/weather` endpoint with location query parameter
- Built `weather_service.py` with **live OpenWeather API integration**:
  - Parses temperature, humidity, rainfall (1h/3h fallback), wind speed (m/s → km/h conversion), description, icon emoji mapping, feels-like, pressure, and visibility
  - Graceful fallback to mock data on API errors with logging
  - Returns `is_mock` flag so the frontend can show a warning banner
- Built the **Weather page** with search, WeatherCard, StatsCards, and extra metric cards
- Built `useWeather` custom hook for reusable weather fetching logic

### ✅ Phase 4 — Disease Detection (Mock)
- Created `POST /api/detect-disease` endpoint accepting multipart image uploads
- Built `disease_service.py` with mock response (placeholder for CV model integration)
- Built the **DiseaseDetection component** with:
  - Drag-and-drop and click-to-upload image handling
  - Image preview display
  - Analyze button with loading state
  - Result card showing disease name, confidence bar, severity, and treatment

### ✅ Phase 5 — AI-Powered Recommendations (Gemini)
- Created `POST /api/recommend` endpoint
- Built `recommendation_service.py` with **full Google Gemini AI integration**:
  - Detailed prompt template requesting structured JSON recommendations
  - Configurable temperature and model settings
  - JSON response parsing with markdown code-fence stripping
  - Graceful fallback to mock data on any error (missing API key, invalid JSON, API failure)
- Built the **Recommend page** with farm parameter form and NPK chart
- Built the **RecommendationPanel** accordion component with 5 expandable sections:
  - Fertilizer Recommendation (with primary, amount, schedule, alternatives)
  - Crop Rotation
  - Irrigation
  - Pest Management
  - General Advice

### ✅ Cross-Cutting Concerns
- **API Client** (`api.js`) — Centralized Axios instance with `/api` base URL and 30s timeout
- **Error Handling** — Toast notifications for all API errors with backend detail messages
- **Loading States** — Skeleton placeholders, spinner buttons, and disabled form states
- **Responsive Design** — Mobile-first layouts with Tailwind breakpoints
- **Custom Styling** — Glass-card effects, gradient utilities, custom scrollbar, shimmer animation

---

## Current Status & Future Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Full-stack project setup, architecture, and navigation |
| Phase 2 | 🔶 Mock data | Crop yield prediction — needs real ML model (scikit-learn / TensorFlow) at `MODEL_PATH` |
| Phase 3 | ✅ Complete | Live weather via OpenWeather API (requires `OPENWEATHER_API_KEY`) |
| Phase 4 | 🔶 Mock data | Disease detection — needs real image classification model |
| Phase 5 | ✅ Complete | AI recommendations via Gemini (requires `GEMINI_API_KEY`) |

### Remaining Work
- **Phase 2** — Train and integrate a real crop yield prediction model (e.g., Random Forest / XGBoost) and load it from `config.MODEL_PATH`
- **Phase 4** — Train and integrate a plant disease classification model (e.g., CNN with TensorFlow/PyTorch)
- Add unit and integration tests for both backend and frontend
- Add deployment configuration (Docker, CI/CD)
- Add user authentication and history tracking
