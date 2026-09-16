"""
TerraNova - ML Model Inference Engine
Loads serialized RandomForest model and computes calibrated risk scores and classifications.
"""

import os
import joblib
import pandas as pd
import numpy as np

class LandslidePredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "landslide_model.joblib")
        
        if not os.path.exists(model_path):
            from model.train import train_model
            data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "training_data.csv")
            if not os.path.exists(data_file):
                from data.generate_training_data import generate_landslide_dataset
                generate_landslide_dataset(3000, data_file)
            train_model()

        self.model = joblib.load(model_path)
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
        Takes raw or aggregated feature dictionary:
        {
            "rainfall_1h": float,
            "rainfall_24h": float,
            "rainfall_72h": float,
            "slope_angle": float,
            "soil_moisture_proxy": float,
            "historical_landslide_count": int
        }
        Returns structured prediction dictionary:
        {
            "risk_score": float (0.0 to 100.0),
            "risk_level": "Low" | "Medium" | "High",
            "is_high_risk": bool,
            "risk_drivers": list[str]
        }
        """
        # Validate and format input
        row = {}
        for col in self.feature_cols:
            row[col] = [float(feature_dict.get(col, 0.0))]
        
        df = pd.DataFrame(row)
        
        # Risk probability from model
        prob_positive = float(self.model.predict_proba(df)[0, 1])
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

        # Identify key physical risk drivers for explainability
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
            "risk_drivers": drivers
        }

# Global singleton helper
_predictor_instance = None

def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = LandslidePredictor()
    return _predictor_instance
