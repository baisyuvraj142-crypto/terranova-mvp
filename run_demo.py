"""
TerraNova - Master Prototype Launcher
Convenience orchestrator to initialize the database, verify ML assets,
and launch both the Flask REST API and Streamlit Dashboard.
"""

import os
import sys
import time
import subprocess
import argparse

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_prepare_environment():
    print("=" * 65)
    print("⛰️  TerraNova: Landslide Risk Monitoring System (SIH 2026)")
    print("=" * 65)
    
    # Check dataset
    data_file = os.path.join(PROJECT_DIR, "data", "training_data.csv")
    if not os.path.exists(data_file):
        print("[*] Generating synthetic historical landslide dataset...")
        from data.generate_training_data import generate_landslide_dataset
        generate_landslide_dataset(3000, data_file)
    else:
        print("[OK] Training dataset found.")

    # Check model
    model_file = os.path.join(PROJECT_DIR, "model", "landslide_model.joblib")
    if not os.path.exists(model_file):
        print("[*] Training RandomForest model...")
        from model.train import train_model
        train_model()
    else:
        print("[OK] Trained ML model found.")

    # Check database
    from database.db import init_db, seed_initial_state
    init_db()
    seed_initial_state()
    print("[OK] SQLite database initialized and seeded.")

def start_services(start_api=True, start_dashboard=True):
    check_and_prepare_environment()

    procs = []
    try:
        if start_api:
            print("\n[+] Launching Flask REST API on http://127.0.0.1:5000 ...")
            api_proc = subprocess.Popen(
                [sys.executable, os.path.join(PROJECT_DIR, "api", "app.py")],
                cwd=PROJECT_DIR
            )
            procs.append(api_proc)
            time.sleep(1.5)

        if start_dashboard:
            print("[+] Launching Streamlit Stage Dashboard on http://localhost:8501 ...")
            dash_proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", os.path.join(PROJECT_DIR, "dashboard", "app.py"), "--server.port=8501", "--server.headless=true"],
                cwd=PROJECT_DIR
            )
            procs.append(dash_proc)

        print("\n" + "=" * 65)
        print("🚀 TerraNova is LIVE and ready for presentation!")
        print("   - Streamlit Dashboard: http://localhost:8501")
        print("   - Flask REST API:      http://127.0.0.1:5000")
        print("   - Health Endpoint:     http://127.0.0.1:5000/api/health")
        print("   - Predict Endpoint:    POST http://127.0.0.1:5000/api/predict")
        print("Press Ctrl+C to terminate all services.")
        print("=" * 65 + "\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Shutting down TerraNova services...")
        for p in procs:
            p.terminate()
        print("[OK] All processes stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TerraNova Launcher")
    parser.add_argument("--api-only", action="store_true", help="Launch only the Flask REST API")
    parser.add_argument("--dashboard-only", action="store_true", help="Launch only the Streamlit Dashboard")
    args = parser.parse_args()

    if args.api_only:
        start_services(start_api=True, start_dashboard=False)
    elif args.dashboard_only:
        start_services(start_api=False, start_dashboard=True)
    else:
        start_services(start_api=True, start_dashboard=True)
