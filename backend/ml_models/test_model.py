"""
test_model.py — Test the trained crop classifier with 5 soil condition scenarios.

Loads the trained model via CropPredictor and runs predictions on five
representative soil / climate profiles, printing the top-3 crop predictions
with confidence scores for each scenario.

Usage:
    cd backend
    python ml_models/test_model.py
"""

from __future__ import annotations

import os
import sys

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.predict_with_model import CropPredictor

# ─── Test scenarios ───────────────────────────────────────────────────────────
# Each dict matches the 7 input features expected by the model.

SCENARIOS = [
    {
        "name": "Tropical – High humidity, warm",
        "N": 90, "P": 42, "K": 43,
        "temperature": 21.0, "humidity": 82.0, "ph": 6.5, "rainfall": 202.9,
    },
    {
        "name": "Dry – Low humidity, high K",
        "N": 0, "P": 0, "K": 0,
        "temperature": 27.0, "humidity": 65.0, "ph": 7.0, "rainfall": 50.0,
    },
    {
        "name": "Wheat belt – Moderate all",
        "N": 20, "P": 30, "K": 40,
        "temperature": 22.0, "humidity": 75.0, "ph": 6.8, "rainfall": 220.0,
    },
    {
        "name": "Rice paddy – High N, very wet",
        "N": 80, "P": 40, "K": 40,
        "temperature": 24.0, "humidity": 85.0, "ph": 6.2, "rainfall": 300.0,
    },
    {
        "name": "Coconut region – Coastal, acidic",
        "N": 22, "P": 16, "K": 30,
        "temperature": 25.7, "humidity": 95.0, "ph": 5.7, "rainfall": 167.0,
    },
]


def run_tests() -> None:
    """Run all test scenarios and print results."""
    predictor = CropPredictor()
    print(f"Model accuracy: {predictor.model_accuracy}%")
    print(f"Supported crops ({len(predictor.crop_classes)}): {predictor.crop_classes}\n")
    print("=" * 65)

    all_passed = True
    for i, scenario in enumerate(SCENARIOS, start=1):
        name = scenario.pop("name")
        result = predictor.predict(**scenario, top_n=3)
        scenario["name"] = name  # restore for display

        top_crop = result["crop"]
        confidence = result["confidence"]
        top3 = result["top_predictions"]

        status = "✅" if confidence > 50 else "⚠️"
        if confidence <= 50:
            all_passed = False

        print(f"Scenario {i}: {name}")
        print(f"  Input : N={scenario['N']} P={scenario['P']} K={scenario['K']} "
              f"T={scenario['temperature']}°C H={scenario['humidity']}% "
              f"pH={scenario['ph']} Rain={scenario['rainfall']}mm")
        print(f"  Result: {status} Top crop = {top_crop} ({confidence}% confidence)")
        print("  Top 3 predictions:")
        for rank, pred in enumerate(top3, 1):
            print(f"    {rank}. {pred['crop']:<20} {pred['confidence']:>6.2f}%")
        print()

    print("=" * 65)
    if all_passed:
        print("✅ All test scenarios passed!")
    else:
        print("⚠️  Some scenarios returned low confidence — review model or inputs.")


if __name__ == "__main__":
    run_tests()
