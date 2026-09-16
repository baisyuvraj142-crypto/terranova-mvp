"""
TerraNova - ML Model Training Script
Trains a RandomForestClassifier for landslide risk prediction and exports it via joblib.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

def train_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    data_path = os.path.join(project_dir, "data", "training_data.csv")
    model_path = os.path.join(current_dir, "landslide_model.joblib")
    meta_path = os.path.join(current_dir, "model_meta.json")

    print(f"Loading training data from {data_path}...")
    df = pd.read_csv(data_path)

    feature_cols = [
        "rainfall_1h",
        "rainfall_24h",
        "rainfall_72h",
        "slope_angle",
        "soil_moisture_proxy",
        "historical_landslide_count"
    ]
    target_col = "landslide_occurred"

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training RandomForestClassifier on {len(X_train)} samples...")
    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    rf.fit(X_train, y_train)

    # Evaluation
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, output_dict=True)
    conf_matrix = confusion_matrix(y_test, y_pred).tolist()

    print("\n--- Model Performance ---")
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print(f"Accuracy: {report['accuracy']:.4f}")
    print(f"Landslide Recall: {report['1']['recall']:.4f}")
    print(f"Landslide F1-Score: {report['1']['f1-score']:.4f}")

    # Feature Importances
    importances = dict(zip(feature_cols, [round(float(v), 4) for v in rf.feature_importances_]))
    print("\n--- Feature Importances ---")
    for k, v in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k:30s}: {v * 100:.1f}%")

    # Serialize Model
    joblib.dump(rf, model_path)
    print(f"\nModel successfully saved to {model_path}")

    # Save metadata
    meta = {
        "model_type": "RandomForestClassifier",
        "feature_cols": feature_cols,
        "n_samples": len(df),
        "roc_auc": round(float(roc_auc), 4),
        "accuracy": round(float(report["accuracy"]), 4),
        "recall": round(float(report["1"]["recall"]), 4),
        "f1_score": round(float(report["1"]["f1-score"]), 4),
        "feature_importances": importances,
        "confusion_matrix": conf_matrix
    }

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Model metadata written to {meta_path}")

if __name__ == "__main__":
    train_model()
