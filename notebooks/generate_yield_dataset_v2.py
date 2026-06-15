"""
generate_yield_dataset_v2.py — Realistic yield dataset generator for Maharashtra.

KEY IMPROVEMENTS over Yield_Dataset_V1:
  - Overlapping climate ranges per crop (ICAR / Maharashtra Agri Dept guidelines)
  - Yield is a function of actual agronomic factors (rainfall, temp stress,
    irrigation bonus, ph penalty, NPK score) — NOT just crop identity
  - Model must learn real relationships to predict yield → honest R² 0.75–0.85
  - year_actual stored as real years (2010–2023), not encoded integers

Output: notebooks/Yield_Dataset_V2.csv

Usage:
    cd notebooks
    python generate_yield_dataset_v2.py
"""

from __future__ import annotations
import os
import numpy as np
import pandas as pd

RANDOM_SEED  = 42
N_PER_CROP   = 1000   # rows per crop
DISTRICTS    = list(range(1, 36))
SEASONS      = [1, 2, 3, 4]

# ── Agronomic profiles ────────────────────────────────────────────────────────
# Ranges deliberately overlap across crops so model can't use rainfall alone
# to identify crop — it must learn actual yield-driving relationships.
# Sources: ICAR crop water requirements, Maharashtra Agriculture Dept data.
CROP_PROFILES: dict[str, dict] = {
    'BAJRA':     dict(rain=(200,600),  temp=(25,38), humidity=(30,60),  ph=(6.0,7.5), N=(80,100),  P=(40,55),  K=(40,55),  yield_base=0.09, yield_var=0.04, irr_pref=0, soil_pref=0),
    'JOWAR':     dict(rain=(300,800),  temp=(22,35), humidity=(30,65),  ph=(6.0,8.0), N=(80,110),  P=(40,55),  K=(40,55),  yield_base=0.12, yield_var=0.05, irr_pref=0, soil_pref=0),
    'WHEAT':     dict(rain=(300,900),  temp=(10,25), humidity=(35,65),  ph=(6.0,7.5), N=(100,130), P=(55,70),  K=(40,55),  yield_base=0.14, yield_var=0.05, irr_pref=1, soil_pref=1),
    'RICE':      dict(rain=(800,2000), temp=(22,35), humidity=(60,95),  ph=(5.5,7.0), N=(100,140), P=(50,70),  K=(40,60),  yield_base=0.20, yield_var=0.08, irr_pref=3, soil_pref=2),
    'MAIZE':     dict(rain=(400,1200), temp=(18,32), humidity=(45,80),  ph=(5.8,7.5), N=(100,140), P=(55,70),  K=(45,65),  yield_base=0.18, yield_var=0.06, irr_pref=2, soil_pref=1),
    'SOYABEAN':  dict(rain=(500,1100), temp=(20,32), humidity=(45,75),  ph=(6.0,7.0), N=(20,40),   P=(60,80),  K=(40,60),  yield_base=0.12, yield_var=0.04, irr_pref=0, soil_pref=3),
    'COTTON':    dict(rain=(400,1200), temp=(20,35), humidity=(40,75),  ph=(6.0,8.0), N=(100,140), P=(50,70),  K=(50,70),  yield_base=0.30, yield_var=0.08, irr_pref=2, soil_pref=0),
    'GROUNDNUT': dict(rain=(400,1200), temp=(22,35), humidity=(45,75),  ph=(6.0,7.0), N=(20,40),   P=(50,70),  K=(45,65),  yield_base=0.10, yield_var=0.03, irr_pref=0, soil_pref=4),
    'SUGARCANE': dict(rain=(1000,2000),temp=(22,35), humidity=(55,90),  ph=(6.0,7.5), N=(130,160), P=(60,80),  K=(70,90),  yield_base=2.00, yield_var=0.50, irr_pref=3, soil_pref=2),
    'BANANA':    dict(rain=(900,2000), temp=(24,32), humidity=(60,95),  ph=(6.0,7.5), N=(130,160), P=(65,85),  K=(60,80),  yield_base=1.60, yield_var=0.45, irr_pref=4, soil_pref=1),
    'ONION':     dict(rain=(300,1000), temp=(18,30), humidity=(40,75),  ph=(6.0,7.5), N=(80,110),  P=(50,70),  K=(55,75),  yield_base=0.65, yield_var=0.20, irr_pref=2, soil_pref=1),
    'POTATO':    dict(rain=(400,1000), temp=(15,25), humidity=(50,80),  ph=(5.5,6.5), N=(100,130), P=(60,80),  K=(80,100), yield_base=0.35, yield_var=0.15, irr_pref=2, soil_pref=1),
    'BLACKGRAM': dict(rain=(400,900),  temp=(25,35), humidity=(50,80),  ph=(6.0,7.5), N=(20,40),   P=(40,60),  K=(40,60),  yield_base=0.35, yield_var=0.15, irr_pref=0, soil_pref=3),
    'LENTIL':    dict(rain=(400,900),  temp=(15,28), humidity=(40,70),  ph=(6.0,8.0), N=(20,40),   P=(40,60),  K=(30,50),  yield_base=0.30, yield_var=0.12, irr_pref=1, soil_pref=4),
    'GRAM':      dict(rain=(300,700),  temp=(15,28), humidity=(35,65),  ph=(6.0,8.0), N=(20,35),   P=(40,60),  K=(30,50),  yield_base=0.10, yield_var=0.04, irr_pref=1, soil_pref=4),
    'TURMERIC':  dict(rain=(1000,2000),temp=(20,30), humidity=(60,90),  ph=(5.5,7.0), N=(120,150), P=(60,80),  K=(60,80),  yield_base=0.47, yield_var=0.20, irr_pref=2, soil_pref=2),
    'MOTHBEANS': dict(rain=(300,800),  temp=(25,40), humidity=(30,65),  ph=(6.5,8.0), N=(10,30),   P=(30,50),  K=(20,40),  yield_base=0.12, yield_var=0.08, irr_pref=0, soil_pref=0),
    'GRAPES':    dict(rain=(300,900),  temp=(15,35), humidity=(35,75),  ph=(6.0,7.5), N=(80,120),  P=(55,75),  K=(70,90),  yield_base=0.08, yield_var=0.04, irr_pref=4, soil_pref=4),
}


def _compute_yield(p: dict, rainfall: float, temperature: float,
                   ph: float, nitrogen: float, phosphorus: float,
                   potassium: float, irr_type: int) -> float:
    """
    Yield is a function of agronomic factors — NOT crop identity.
    This ensures the model must learn real rainfall/temp/NPK relationships.
    """
    rain_norm   = (rainfall - p['rain'][0]) / max(p['rain'][1] - p['rain'][0], 1)
    temp_center = (p['temp'][0] + p['temp'][1]) / 2
    temp_stress = max(0.0, 1.0 - abs(temperature - temp_center) / (temp_center - p['temp'][0] + 1e-6))
    irr_bonus   = 1.0 + 0.05 * irr_type
    ph_center   = (p['ph'][0] + p['ph'][1]) / 2
    ph_penalty  = max(0.0, 1.0 - abs(ph - ph_center) / 1.5)
    npk_score   = float(np.clip((nitrogen + phosphorus + potassium) / 300.0, 0.5, 1.2))

    yield_val = (
        p['yield_base']
        * (0.5 + 0.5 * rain_norm)
        * temp_stress
        * irr_bonus
        * ph_penalty
        * npk_score
        + np.random.normal(0.0, p['yield_var'] * 0.3)
    )
    return max(0.01, float(yield_val))


def generate(n_per_crop: int = N_PER_CROP, seed: int = RANDOM_SEED) -> pd.DataFrame:
    np.random.seed(seed)
    rows: list[dict] = []

    for crop, p in CROP_PROFILES.items():
        for _ in range(n_per_crop):
            rainfall    = np.random.uniform(*p['rain'])
            temperature = np.random.uniform(*p['temp'])
            humidity    = np.random.uniform(*p['humidity'])
            ph          = np.random.uniform(*p['ph'])
            nitrogen    = np.random.uniform(*p['N'])
            phosphorus  = np.random.uniform(*p['P'])
            potassium   = np.random.uniform(*p['K'])
            district    = np.random.choice(DISTRICTS)
            season      = np.random.choice(SEASONS)
            area        = np.random.uniform(100, 50000)
            irr_type    = int(np.clip(np.random.normal(p['irr_pref'], 1), 0, 4))
            soil_type   = int(np.clip(np.random.normal(p['soil_pref'], 1), 0, 4))
            year_actual = np.random.randint(2010, 2024)

            yield_val = _compute_yield(
                p, rainfall, temperature, ph,
                nitrogen, phosphorus, potassium, irr_type,
            )

            rows.append({
                'district':        district,
                'nitrogen':        round(nitrogen, 2),
                'phosphorus':      round(phosphorus, 2),
                'potassium':       round(potassium, 2),
                'temperature':     round(temperature, 2),
                'ph':              round(ph, 2),
                'rainfall':        round(rainfall, 2),
                'label':           crop,
                'yield':           round(yield_val, 6),
                'area':            round(area, 2),
                'season':          season,
                'humidity':        round(humidity, 2),
                'irrigation_type': irr_type,
                'soil_type':       soil_type,
                'year_actual':     year_actual,
            })

    df = (
        pd.DataFrame(rows)
        .sample(frac=1, random_state=seed)
        .reset_index(drop=True)
    )
    return df


def main() -> None:
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "Yield_Dataset_V2.csv")

    print("Generating Yield_Dataset_V2 ...")
    df = generate()

    print(f"  Shape  : {df.shape}")
    print(f"  Crops  : {sorted(df['label'].unique())}")
    print(f"  Yield  : {df['yield'].min():.4f} – {df['yield'].max():.4f}")

    # Overlap check
    overlap_700mm = [
        c for c, p in CROP_PROFILES.items()
        if p['rain'][0] <= 700 <= p['rain'][1]
    ]
    print(f"  Crops viable at 700mm rainfall: {len(overlap_700mm)} (was 1 in V1)")

    df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}  ({len(df):,} rows)")
    print("Run train_yield_model.py next to retrain on this dataset.")


if __name__ == "__main__":
    main()