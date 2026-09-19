"""
TerraNova - ML Model Training & Multi-Model Benchmark Script
Trains and serializes:
1. RandomForestClassifier (Server Ensemble Baseline)
2. HistGradientBoostingClassifier (Fast GBDT - 3x-5x faster inference)
3. LogisticRegression (Calibrated Edge Model - Sub-millisecond microsecond inference for IoT sensors)
"""

import os
import json
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

def train_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    data_path = os.path.join(project_dir, "data", "training_data.csv")
    rf_model_path = os.path.join(current_dir, "landslide_model.joblib")
    gbdt_model_path = os.path.join(current_dir, "fast_gbdt_model.joblib")
    linear_model_path = os.path.join(current_dir, "edge_linear_model.joblib")
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

    # 1. Random Forest (Ensemble Server Baseline)
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

    # 2. HistGradientBoosting (Fast GBDT - LightGBM alternative in sklearn)
    print("Training HistGradientBoostingClassifier (Fast GBDT)...")
    gbdt = HistGradientBoostingClassifier(
        max_iter=60,
        max_depth=5,
        class_weight="balanced",
        random_state=42
    )
    gbdt.fit(X_train, y_train)

    # 3. Logistic Regression (Ultra-Fast Edge AI for Microcontrollers)
    print("Training LogisticRegression (Calibrated Edge Model)...")
    edge_lr = LogisticRegression(
        max_iter=500,
        class_weight="balanced",
        random_state=42
    )
    edge_lr.fit(X_train, y_train)

    # Latency & Performance Benchmarks
    models = {
        "Random Forest (Server Baseline)": rf,
        "HistGradientBoosting (Fast GBDT)": gbdt,
        "Calibrated Linear (Ultra-Fast Edge)": edge_lr
    }

    sample_single = X_test.iloc[[0]]
    benchmarks = []

    for name, m in models.items():
        y_pred = m.predict(X_test)
        y_prob = m.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, y_prob))
        acc = float(np.mean(y_pred == y_test))

        # Measure 500 single-inference calls
        t0 = time.perf_counter()
        for _ in range(500):
            _ = m.predict_proba(sample_single)
        t_total_ms = (time.perf_counter() - t0) * 1000.0
        avg_latency_ms = round(t_total_ms / 500.0, 3)

        benchmarks.append({
            "model_name": name,
            "roc_auc": round(auc, 4),
            "accuracy": round(acc * 100, 1),
            "avg_latency_ms": avg_latency_ms,
            "speedup_vs_rf": round(1.0 if "Random Forest" in name else (benchmarks[0]["avg_latency_ms"] / max(0.001, avg_latency_ms)), 1)
        })

    # Primary RF Evaluation for compatibility
    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    roc_auc_rf = roc_auc_score(y_test, y_prob_rf)
    report_rf = classification_report(y_test, y_pred_rf, output_dict=True)
    conf_matrix_rf = confusion_matrix(y_test, y_pred_rf).tolist()

    importances = dict(zip(feature_cols, [round(float(v), 4) for v in rf.feature_importances_]))

    # Save models
    joblib.dump(rf, rf_model_path)
    joblib.dump(gbdt, gbdt_model_path)
    joblib.dump(edge_lr, linear_model_path)
    print(f"Models successfully saved to {current_dir}")

    # Metadata
    meta = {
        "model_type": "RandomForestClassifier",
        "feature_cols": feature_cols,
        "n_samples": len(df),
        "roc_auc": round(float(roc_auc_rf), 4),
        "accuracy": round(float(report_rf["accuracy"]), 4),
        "recall": round(float(report_rf["1"]["recall"]), 4),
        "f1_score": round(float(report_rf["1"]["f1-score"]), 4),
        "feature_importances": importances,
        "confusion_matrix": conf_matrix_rf,
        "model_benchmarks": benchmarks
    }

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Model metadata written to {meta_path}")

if __name__ == "__main__":
    train_model()
