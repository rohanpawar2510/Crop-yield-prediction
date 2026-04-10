# scripts/

Data preparation and analysis utilities for the crop recommendation dataset.

---

## add_humidity_to_csv.py

A utility script that adds a `humidity` column to the Maharashtra crop dataset
and produces `Crop_recommendation.csv` — the file required by
`backend/train_models.py`.

## What the script does

| Step | Action |
|------|--------|
| 1 | Reads `notebooks/Final_Agriculture_Dataset_V2.csv` |
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

---

## clean_and_improve_dataset.py

Data cleaning pipeline that removes underrepresented crops and extreme yield
outliers, validates feature ranges, and adds five engineered features.

### Pipeline

```
Crop_recommendation.csv (30,042 rows, 37 crops)
  ↓  Step 1 — Load & validate (check nulls, column types)
  ↓  Step 2 — Remove crops with < 50 samples
  ↓  Step 3 — Remove yield outliers (> 3σ from per-crop mean)
  ↓  Step 4 — Validate agronomic ranges
  ↓  Step 5 — Feature engineering (5 new columns)
Crop_recommendation_improved.csv (~29,700 rows, ~31 crops)
```

### Usage

```bash
# Default paths (from repository root)
python scripts/clean_and_improve_dataset.py

# Custom options
python scripts/clean_and_improve_dataset.py \
    --input  notebooks/Crop_recommendation.csv \
    --output notebooks/Crop_recommendation_improved.csv \
    --min-samples 50 \
    --outlier-sigma 3.0
```

### Engineered features added

| Feature                    | Formula                                       |
|----------------------------|-----------------------------------------------|
| `NPK_total`                | N + P + K                                     |
| `NPK_ratio`                | N / (P + K)                                   |
| `Climate_score`            | 0.4×temp + 0.3×humidity + 0.3×(rainfall/100) |
| `Temp_humidity_interaction`| temperature × humidity                        |
| `Soil_quality_score`       | Gaussian centred at pH 6.5 (range 0–10)       |

---

## feature_engineering.py

Reusable feature engineering utilities. Can be used as a library or run
standalone.

### Library usage

```python
from scripts.feature_engineering import add_features

df_enriched = add_features(df)  # adds 5 new columns
```

### CLI usage

```bash
python scripts/feature_engineering.py \
    --input  notebooks/Crop_recommendation.csv \
    --output notebooks/Crop_recommendation_features.csv
```

---

## data_analysis_report.py

Generates a comprehensive data quality and exploratory analysis report.

### Sections covered

1. Dataset overview (shape, columns, dtypes)
2. Missing value audit
3. Feature range validation
4. Crop distribution (counts, % representation)
5. Yield statistics per crop (mean, std, min, max, IQR)
6. Outlier detection (values beyond ±3σ per crop)
7. Feature correlation matrix
8. Feature-label mutual information scores
9. Data validation summary

### Usage

```bash
# Analyse the standard processed dataset
python scripts/data_analysis_report.py

# Analyse the cleaned improved dataset
python scripts/data_analysis_report.py \
    --input notebooks/Crop_recommendation_improved.csv
```

---

---

## ultimate_data_cleaner.py

Aggressive 8-step cleaning and balancing pipeline designed for maximum
model accuracy. Produces `Crop_recommendation_final.csv`.

### Why use this instead of clean_and_improve_dataset.py?

| Setting              | `clean_and_improve_dataset.py` | `ultimate_data_cleaner.py` |
|----------------------|-------------------------------|---------------------------|
| Min samples per crop | 50                            | **100**                   |
| Outlier σ threshold  | 3.0                           | **2.5** (more aggressive) |
| Max samples per crop | unlimited                     | **1 000** (balance)       |
| pH valid range       | 0–14                          | **4–9** (agronomic)       |
| Temperature range    | −10 to 55 °C                  | **−10 to 50 °C**          |
| Rainfall range       | 0–5000 mm                     | **0–3000 mm**             |

### 8-step pipeline

```
Crop_recommendation.csv (~30,042 rows, 37 crops)
  ↓  Step 1 — Load & validate (columns, types)
  ↓  Step 2 — Remove all null rows
  ↓  Step 3 — Strict range validation
  ↓  Step 4 — Remove crops with < 100 samples
  ↓  Step 5 — Remove yield outliers > 2.5σ per crop
  ↓  Step 6 — Balance: cap at 1000 samples per crop
  ↓  Step 7 — Add 5 engineered features
  ↓  Step 8 — Save & comprehensive report
Crop_recommendation_final.csv (~12,000–15,000 rows, 15–20 crops)
```

### Expected output

| Metric            | Before          | After              |
|-------------------|-----------------|--------------------|
| Rows              | ~30,042         | ~12,000–15,000     |
| Crops             | 37              | 15–20              |
| Samples per crop  | highly variable | 750–1,000          |
| Null values       | some            | 0                  |
| Yield outliers    | many            | 0                  |

### Usage

```bash
# Default paths (from repository root)
python scripts/ultimate_data_cleaner.py

# Custom options
python scripts/ultimate_data_cleaner.py \
    --input   notebooks/Crop_recommendation.csv \
    --output  notebooks/Crop_recommendation_final.csv \
    --min-samples  100 \
    --max-samples  1000 \
    --outlier-sigma 2.5
```

### Command-line flags

| Flag              | Default | Description                                   |
|-------------------|---------|-----------------------------------------------|
| `--input`         | `notebooks/Crop_recommendation.csv` | Input CSV |
| `--output`        | `notebooks/Crop_recommendation_final.csv` | Output CSV |
| `--min-samples`   | `100`   | Drop crops with fewer samples                 |
| `--max-samples`   | `1000`  | Cap per crop to balance classes               |
| `--outlier-sigma` | `2.5`   | Yield outlier threshold in std deviations     |

---

## Recommended workflow

```bash
# Step 1 — Add humidity to raw dataset (if not already done)
cd scripts
python add_humidity_to_csv.py --fallback-only   # or use --api-key

# Step 2 — Analyse the standard dataset
python data_analysis_report.py

# Step 3a — Clean and improve the dataset (moderate cleaning)
python clean_and_improve_dataset.py

# Step 3b — Aggressively clean the dataset (for maximum accuracy)
python ultimate_data_cleaner.py

# Step 4 — Analyse the final dataset
python data_analysis_report.py --input notebooks/Crop_recommendation_final.csv

# Step 5 — Train final optimised models
cd ../backend
python train_models.py
```
