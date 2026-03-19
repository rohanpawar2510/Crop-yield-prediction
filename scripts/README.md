# scripts/add_humidity_to_csv.py

A utility script that adds a `humidity` column to the Maharashtra crop dataset
and produces `Crop_recommendation.csv` — the file required by
`backend/train_models.py`.

## What the script does

| Step | Action |
|------|--------|
| 1 | Reads `notebooks/Crop_Final_Updated.csv` (or `Crop_Final_Updated (1).csv`) |
| 2 | Maps each Maharashtra district code (25–60) to a city name |
| 3 | Fetches real-time humidity from the **OpenWeather API** (free tier) with caching and rate limiting |
| 4 | Falls back to an estimation formula (`rainfall + temperature → humidity`) for any API failures or when no API key is provided |
| 5 | Adds the `humidity` column and reorders columns to the required structure |
| 6 | Validates data quality (no nulls, humidity in range 20–95 %, numeric types) |
| 7 | Saves `notebooks/Crop_recommendation.csv` |

## Required output format

```
district_name,N,P,K,temperature,humidity,ph,rainfall,label,yield
25,78.12,49.75,44.17,25.0,65.0,6.5,800.0,RICE,64.75
```

10 columns — exactly what `backend/train_models.py` expects.

## Prerequisites

```bash
pip install pandas requests python-dotenv
```

> `python-dotenv` is optional but recommended — it lets you store your API key
> in a `.env` file instead of setting an environment variable.

## Setup

```bash
cd scripts
cp .env.example .env
# Edit .env and set OPENWEATHER_API_KEY=<your key>
```

Get a free API key at <https://openweathermap.org/api>.

## Usage

```bash
# From the repository root:
cd scripts

# Option A — Use the OpenWeather API (recommended for production)
python add_humidity_to_csv.py --api-key YOUR_KEY

# Option B — API key from .env / environment variable
python add_humidity_to_csv.py

# Option C — Estimation only (no network calls)
python add_humidity_to_csv.py --fallback-only
```

### Command-line flags

| Flag | Description |
|------|-------------|
| `--api-key KEY` | OpenWeather API key (overrides `OPENWEATHER_API_KEY` env var) |
| `--fallback-only` | Skip the API; estimate humidity from rainfall & temperature |

## District mapping

The dataset uses numeric codes for Maharashtra districts (25–60).
The script maps these codes to city names for the OpenWeather API:

| Code | City |
|------|------|
| 25 | Pune |
| 26 | Nashik |
| 27 | Aurangabad (Chhatrapati Sambhajinagar) |
| 28 | Amravati |
| 29 | Nagpur |
| 30 | Kolhapur |
| … | … (see script for full list) |

## Fallback estimation formula

When no API key is set or an API call fails, humidity is estimated as:

```
humidity = 60
         + min(rainfall / 30, 25)
         - max((temperature - 25) * 0.5, 0)
```

Clamped to [20, 95].

This heuristic captures the key relationships:
- More rainfall → higher humidity
- Higher temperature → lower relative humidity

## Output

After a successful run the file `notebooks/Crop_recommendation.csv` will be
created/overwritten and can be used immediately to (re-)train the models:

```bash
cd backend
python train_models.py
```

## Error codes

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Fatal error (source file not found, missing required column) |
| 2 | Saved with validation warnings (review the console output) |
