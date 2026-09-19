"""
TerraNova - ML Model Inference Engine
Loads serialized models and computes calibrated risk scores, classifications, and multi-model latency benchmarks.
"""

import os
import time
import joblib
import pandas as pd
import numpy as np

class LandslidePredictor:
    def __init__(self, model_path=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if model_path is None:
            model_path = os.path.join(current_dir, "landslide_model.joblib")
        
        self.current_dir = current_dir
        self.rf_path = model_path
        self.gbdt_path = os.path.join(current_dir, "fast_gbdt_model.joblib")
        self.linear_path = os.path.join(current_dir, "edge_linear_model.joblib")

        # Auto-train if RF model doesn't exist
        if not os.path.exists(model_path):
            from model.train import train_model
            data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "training_data.csv")
            if not os.path.exists(data_file):
                from data.generate_training_data import generate_landslide_dataset
                generate_landslide_dataset(3000, data_file)
            train_model()

        self.model = joblib.load(model_path)
        
        # Load companion models if available
        self.gbdt_model = None
        if os.path.exists(self.gbdt_path):
            try:
                self.gbdt_model = joblib.load(self.gbdt_path)
            except Exception:
                self.gbdt_model = None

        self.linear_model = None
        if os.path.exists(self.linear_path):
            try:
                self.linear_model = joblib.load(self.linear_path)
            except Exception:
                self.linear_model = None

        self.feature_cols = [
            "rainfall_1h",
            "rainfall_24h",
            "rainfall_72h",
            "slope_angle",
            "soil_moisture_proxy",
            "historical_landslide_count"
        ]

    def predict(self, feature_dict: dict) -> dict:
        """
        Default prediction using the primary RandomForest model.
        Guarantees 100% backward compatibility with existing pipeline and tests.
        """
        return self.predict_with_model(feature_dict, model_choice="Random Forest")

    def predict_with_model(self, feature_dict: dict, model_choice: str = "Random Forest") -> dict:
        """
        Computes risk using the specified model architecture and measures inference latency.
        Supported choices:
        - "Random Forest" (Ensemble Server Baseline)
        - "HistGradientBoosting" (Fast GBDT)
        - "Calibrated Linear" (Ultra-Fast Edge Model)
        """
        # Select active model
        active_model = self.model
        model_label = "Random Forest (Server Baseline)"

        if "HistGradientBoosting" in model_choice or "GBDT" in model_choice:
            if self.gbdt_model is not None:
                active_model = self.gbdt_model
                model_label = "HistGradientBoosting (Fast GBDT)"
        elif "Linear" in model_choice or "Edge" in model_choice:
            if self.linear_model is not None:
                active_model = self.linear_model
                model_label = "Calibrated Linear (Ultra-Fast Edge)"

        # Prepare input dataframe
        row = {}
        for col in self.feature_cols:
            row[col] = [float(feature_dict.get(col, 0.0))]
        df = pd.DataFrame(row)

        # High-precision latency measurement
        t0 = time.perf_counter()
        prob_positive = float(active_model.predict_proba(df)[0, 1])
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        risk_score = round(prob_positive * 100.0, 1)

        # Categorize
        if risk_score >= 70.0:
            risk_level = "High"
            is_high_risk = True
        elif risk_score >= 40.0:
            risk_level = "Medium"
            is_high_risk = False
        else:
            risk_level = "Low"
            is_high_risk = False

        # Physical risk drivers
        drivers = []
        r24 = feature_dict.get("rainfall_24h", 0)
        r72 = feature_dict.get("rainfall_72h", 0)
        r1 = feature_dict.get("rainfall_1h", 0)
        moisture = feature_dict.get("soil_moisture_proxy", 0)
        slope = feature_dict.get("slope_angle", 0)

        if r24 >= 80:
            drivers.append(f"Heavy 24h Cumulative Precipitation ({r24:.1f} mm)")
        if r72 >= 160:
            drivers.append(f"Extended 72h Ground Saturation ({r72:.1f} mm)")
        if r1 >= 30:
            drivers.append(f"High-Intensity Cloudburst / Flash Rain ({r1:.1f} mm/hr)")
        if moisture >= 65:
            drivers.append(f"Critical Soil Moisture Pore-Pressure ({moisture:.1f}%)")
        if slope >= 35:
            drivers.append(f"Steep Unstable Slope Incline ({slope:.1f}°)")

        if not drivers:
            drivers.append("Normal terrain and baseline meteorological stability")

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_high_risk": is_high_risk,
            "risk_drivers": drivers,
            "latency_ms": latency_ms,
            "model_used": model_label
        }

# Global singleton helper
_predictor_instance = None

def get_predictor(force_reload: bool = False):
    global _predictor_instance
    if _predictor_instance is None or force_reload or not hasattr(_predictor_instance, "predict_with_model"):
        _predictor_instance = LandslidePredictor()
    return _predictor_instance
