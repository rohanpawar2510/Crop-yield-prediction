# Install: pip install -r backend/requirements.txt
# Run:     cd backend && uvicorn main:app --reload --port 8000

"""
main.py — FastAPI application entry point for the Smart Agriculture API.

Registers all routers, configures CORS, and exposes health + root endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.predict import router as predict_router
from routes.weather import router as weather_router
from routes.disease import router as disease_router
from routes.recommend import router as recommend_router
from models.schemas import HealthResponse, RootResponse
import config

# ─── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Agriculture API",
    description=(
        "Backend API for the Smart Agriculture Dashboard. "
        "Provides crop yield prediction, weather data, plant disease detection, "
        "and smart farming recommendations."
    ),
    version="1.0.0",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins during development so the frontend (served from any port
# or file://) can reach the API without CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(predict_router, prefix="/api", tags=["Prediction"])
app.include_router(weather_router, prefix="/api", tags=["Weather"])
app.include_router(disease_router, prefix="/api", tags=["Disease Detection"])
app.include_router(recommend_router, prefix="/api", tags=["Recommendations"])

# ─── Health & root endpoints ──────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """Health-check endpoint used by deployment platforms and load balancers."""
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/", response_model=RootResponse, tags=["System"])
def root() -> RootResponse:
    """API root — returns version info and a list of available routes."""
    return RootResponse(
        message="Smart Agriculture API is running.",
        version="1.0.0",
        routes=[
            "POST /api/predict",
            "GET  /api/weather?location={location}",
            "POST /api/detect-disease",
            "POST /api/recommend",
            "GET  /health",
        ],
    )


# ─── Dev entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
