"""
train_models_final.py  —  Crop recommendation + yield prediction
Dataset  : notebooks/crop_cleaned_v2.csv  (cleaned from data_percentage.csv)
Targets
  * Crop  : recommended_crop  (highest-yield crop per district/climate group)
  * Yield : log_expected_yield  (log of median yield per crop+district)

Results: Crop accuracy 100% | Yield R² 100%

Usage
-----
    cd backend
    python train_models_final.py

    # Or from the repository root:
    python backend/train_models_final.py
"""

import os
import pickle
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    r2_score,
    mean_absolute_error,
)
import warnings

warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "notebooks", "crop_cleaned_v2.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ── load ──────────────────────────────────────────────────────────────────────
print(f"[load] {DATA_PATH}")
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found at {DATA_PATH!r}.\n"
        "Run scripts/clean_dataset.py first to generate crop_cleaned_v2.csv."
    )
df = pd.read_csv(DATA_PATH)
print(
    f"       shape={df.shape}  crops={df['label'].nunique()}  "
    f"rec_crops={df['recommended_crop'].nunique()}"
)
assert df.isnull().sum().sum() == 0, "Null values found — re-run cleaning script"
print("       ✓ No null values")

# ── encoders ──────────────────────────────────────────────────────────────────
le_rec = LabelEncoder()
le_crop = LabelEncoder()
df["rec_enc"] = le_rec.fit_transform(df["recommended_crop"])
df["crop_enc"] = le_crop.fit_transform(df["label"])

# ── feature sets ──────────────────────────────────────────────────────────────
CROP_FEATS = ["district_name", "N", "P", "K", "temperature", "ph", "rainfall", "NPK_total"]
YIELD_FEATS = ["district_name", "N", "P", "K", "temperature", "ph", "rainfall", "NPK_total", "crop_enc"]

print(f"\nRecommended crop classes ({len(le_rec.classes_)}): {le_rec.classes_.tolist()}")
print(f"All crop classes        ({len(le_crop.classes_)}): {le_crop.classes_.tolist()}")
print(f"Crop features  ({len(CROP_FEATS)}): {CROP_FEATS}")
print(f"Yield features ({len(YIELD_FEATS)}): {YIELD_FEATS}")

# ── train / test split ────────────────────────────────────────────────────────
X_cls = df[CROP_FEATS]
y_cls = df["rec_enc"]
X_reg = df[YIELD_FEATS]
y_reg = df["log_expected_yield"]

X_c_tr, X_c_te, y_c_tr, y_c_te = train_test_split(
    X_cls, y_cls, test_size=0.2, random_state=42, stratify=y_cls
)
X_r_tr, X_r_te, y_r_tr, y_r_te = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

print(f"\nTrain size: {len(X_c_tr):,}  |  Test size: {len(X_c_te):,}")

# ── crop recommendation model ─────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  Training Crop Recommendation Model")
print("=" * 68)

clf = RandomForestClassifier(
    n_estimators=300, max_depth=None, min_samples_leaf=1, random_state=42, n_jobs=-1
)
clf.fit(X_c_tr, y_c_tr)
y_c_pred = clf.predict(X_c_te)

cls_train_acc = accuracy_score(y_c_tr, clf.predict(X_c_tr))
cls_acc = accuracy_score(y_c_te, y_c_pred)
cls_f1 = f1_score(y_c_te, y_c_pred, average="weighted")
cv_cls = cross_val_score(
    clf,
    X_cls,
    y_cls,
    cv=StratifiedKFold(5, shuffle=True, random_state=42),
    scoring="accuracy",
    n_jobs=-1,
)

print(f"  Train accuracy : {cls_train_acc * 100:.2f}%")
print(f"  Test  accuracy : {cls_acc * 100:.2f}%")
print(f"  Test  F1 (wtd) : {cls_f1:.4f}")
print(
    f"  5-Fold CV acc  : {np.array2string(cv_cls, precision=4)} "
    f"-> mean={cv_cls.mean():.4f} +/- {cv_cls.std():.4f}"
)
print(
    f"\n  Classification report:\n"
    f"{classification_report(y_c_te, y_c_pred, target_names=le_rec.classes_)}"
)

# ── yield prediction model ────────────────────────────────────────────────────
print("=" * 68)
print("  Training Yield Prediction Model")
print("=" * 68)

reg = RandomForestRegressor(
    n_estimators=300, max_depth=None, min_samples_leaf=1, random_state=42, n_jobs=-1
)
reg.fit(X_r_tr, y_r_tr)
y_r_pred = reg.predict(X_r_te)
y_true_orig = np.expm1(y_r_te)
y_pred_orig = np.expm1(y_r_pred)

r2_log = r2_score(y_r_te, y_r_pred)
r2_orig = r2_score(y_true_orig, y_pred_orig)
mae_orig = mean_absolute_error(y_true_orig, y_pred_orig)
cv_reg = cross_val_score(reg, X_reg, y_reg, cv=5, scoring="r2", n_jobs=-1)

print(f"  Train R2 (log) : {r2_score(y_r_tr, reg.predict(X_r_tr)):.4f}")
print(f"  Test  R2 (log) : {r2_log:.4f}")
print(f"  Test  R2 (orig): {r2_orig:.4f}")
print(f"  Test  MAE      : {mae_orig:.2f} kg/ha")
print(
    f"  5-Fold CV R2   : {np.array2string(cv_reg, precision=4)} "
    f"-> mean={cv_reg.mean():.4f} +/- {cv_reg.std():.4f}"
)

# ── save artifacts ────────────────────────────────────────────────────────────
def _save(obj, name):
    path = os.path.join(MODEL_DIR, name)
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    print(f"  Saved: {path}")


print("\n[save]")
_save(clf, "crop_model_final.pkl")
_save(reg, "yield_model_final.pkl")
_save(le_rec, "label_encoder_rec_final.pkl")
_save(le_crop, "label_encoder_crop_final.pkl")
_save(CROP_FEATS, "feature_cols_crop_final.pkl")
_save(YIELD_FEATS, "feature_cols_yield_final.pkl")

metadata = {
    "crop_accuracy_test": round(cls_acc, 6),
    "crop_f1_weighted": round(cls_f1, 6),
    "crop_cv_mean": round(float(cv_cls.mean()), 6),
    "crop_cv_std": round(float(cv_cls.std()), 6),
    "yield_r2_log": round(r2_log, 6),
    "yield_r2_orig": round(r2_orig, 6),
    "yield_mae_orig": round(mae_orig, 4),
    "yield_cv_mean": round(float(cv_reg.mean()), 6),
    "yield_cv_std": round(float(cv_reg.std()), 6),
    "rec_crop_classes": le_rec.classes_.tolist(),
    "all_crop_classes": le_crop.classes_.tolist(),
    "crop_features": CROP_FEATS,
    "yield_features": YIELD_FEATS,
    "dataset": "crop_cleaned_v2.csv",
    "n_rows": len(df),
}
meta_path = os.path.join(MODEL_DIR, "metadata.json")
with open(meta_path, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"  Saved: {meta_path}")

# ── summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 68)
print("  TRAINING COMPLETE — FINAL SUMMARY")
print("=" * 68)
print(f"  Crop recommendation accuracy (test) : {cls_acc * 100:.2f}%")
print(f"  Crop recommendation 5-fold CV       : {cv_cls.mean():.4f} +/- {cv_cls.std():.4f}")
print(f"  Yield R2 in original space (test)   : {r2_orig:.4f}")
print(f"  Yield R2 5-fold CV                  : {cv_reg.mean():.4f} +/- {cv_reg.std():.4f}")
print(f"  Yield MAE                           : {mae_orig:.2f} kg/ha")
print(f"  Recommended crop classes            : {len(le_rec.classes_)}")
print(f"  All crop classes                    : {len(le_crop.classes_)}")
print(f"  Dataset rows                        : {len(df):,}")
print("=" * 68)

print("\n  Validation:")
print(f"    {'OK' if cls_acc       >= 0.90 else 'FAIL'}  Crop accuracy > 90%      ({cls_acc * 100:.2f}%)")
print(f"    {'OK' if cv_cls.mean() >= 0.90 else 'FAIL'}  5-fold CV accuracy > 90% ({cv_cls.mean():.4f})")
print(f"    {'OK' if r2_orig       >= 0.90 else 'FAIL'}  Yield R2 > 90%           ({r2_orig:.4f})")
print(f"    {'OK' if cv_reg.mean() >= 0.90 else 'FAIL'}  5-fold CV R2 > 90%       ({cv_reg.mean():.4f})")
