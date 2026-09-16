"""
TerraNova - Flask REST API Service
Exposes prediction, monitoring pipeline, simulation, and alert logs as RESTful endpoints.
Meets NFR-2: sub-2-second response latency.
"""

import os
import json
import time
from flask import Flask, request, jsonify
from model.predict import get_predictor
from services.pipeline import run_pipeline, load_data
from database.db import get_latest_risk_assessments, get_latest_zone_readings, get_all_alerts, init_db

app = Flask(__name__)

# Ensure DB is ready
init_db()

@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "TerraNova Landslide Risk Monitoring API",
        "version": "1.0.0",
        "timestamp": time.time()
    })

@app.route("/api/zones", methods=["GET"])
def get_zones():
    """Returns static zone definitions merged with latest readings and risk assessments."""
    zones, routes, _ = load_data()
    readings = {r["zone_id"]: r for r in get_latest_zone_readings()}
    assessments = {a["zone_id"]: a for a in get_latest_risk_assessments()}

    results = []
    for z in zones:
        zid = z["zone_id"]
        latest_r = readings.get(zid, {})
        latest_a = assessments.get(zid, {})
        route = routes.get(zid, {})

        drivers = []
        if latest_a.get("risk_drivers"):
            try:
                drivers = json.loads(latest_a["risk_drivers"])
            except Exception:
                drivers = [latest_a["risk_drivers"]]

        results.append({
            "zone_id": zid,
            "zone_name": z["zone_name"],
            "region": z["region"],
            "latitude": z["latitude"],
            "longitude": z["longitude"],
            "slope_angle": z["slope_angle"],
            "historical_landslide_count": z["historical_landslide_count"],
            "soil_type": z.get("soil_type", "Mountainous weathered"),
            "current_weather": latest_r,
            "current_risk": {
                "risk_score": latest_a.get("risk_score", 15.0),
                "risk_level": latest_a.get("risk_level", "Low"),
                "risk_drivers": drivers,
                "timestamp": latest_a.get("timestamp")
            },
            "alternate_route": route
        })

    return jsonify({"zones": results, "count": len(results)})

@app.route("/predict", methods=["POST"])
@app.route("/api/predict", methods=["POST"])
def predict_risk():
    """
    FR-3 & FR-4: Compute landslide risk score (0-100 & Low/Medium/High) per zone using trained ML model.
    """
    start_time = time.time()
    payload = request.get_json(force=True, silent=True) or {}

    try:
        predictor = get_predictor()
        prediction = predictor.predict(payload)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return jsonify({
            "prediction": prediction,
            "execution_time_ms": latency_ms,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 400

@app.route("/api/pipeline/run", methods=["POST"])
def execute_pipeline():
    """FR-9: Allows manual refresh/re-run of the prediction cycle for demo purposes."""
    start_time = time.time()
    results = run_pipeline()
    latency_ms = round((time.time() - start_time) * 1000, 2)
    return jsonify({
        "message": "Full monitoring cycle completed successfully",
        "results": results,
        "execution_time_ms": latency_ms,
        "status": "success"
    })

@app.route("/api/simulate-rainfall", methods=["POST"])
def simulate_rainfall():
    """
    FR-10: Demo 'simulate high rainfall' trigger to force a high-risk state live on stage.
    """
    start_time = time.time()
    payload = request.get_json(force=True, silent=True) or {}
    target_zone_id = payload.get("zone_id", "NER_ZONE_01")

    results = run_pipeline(target_simulated_zone_id=target_zone_id)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    flagged_zone = next((r for r in results if r["zone_id"] == target_zone_id), None)

    return jsonify({
        "message": f"Simulated extreme rainfall triggered on {target_zone_id}",
        "flagged_zone": flagged_zone,
        "execution_time_ms": latency_ms,
        "status": "success"
    })

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """FR-6: Returns audit trail of every logged alert."""
    limit = request.args.get("limit", 50, type=int)
    alerts = get_all_alerts(limit=limit)
    return jsonify({"alerts": alerts, "total": len(alerts)})

@app.route("/api/routes/<zone_id>", methods=["GET"])
def get_alternate_route(zone_id):
    """FR-7: Predefined alternate route when a zone is flagged high-risk."""
    _, routes, _ = load_data()
    route = routes.get(zone_id)
    if not route:
        return jsonify({"error": "Zone not found"}), 404
    return jsonify({"zone_id": zone_id, "alternate_route": route})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
