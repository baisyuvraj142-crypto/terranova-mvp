"""
TerraNova - Pipeline Orchestrator
Coordinates the full end-to-end loop:
Collect weather -> Compute features -> Predict risk -> Check threshold -> Trigger SMS -> Log reroute -> Return summary.
"""

import os
import json
from database.db import log_reading, log_risk_assessment, get_latest_risk_assessments, get_latest_zone_readings
from model.predict import get_predictor
from services.weather_service import fetch_weather_for_zone, generate_extreme_rainfall_simulation
from services.alert_service import send_alert_for_zone

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    zones_file = os.path.join(PROJECT_DIR, "data", "zones.json")
    routes_file = os.path.join(PROJECT_DIR, "data", "routes.json")
    subs_file = os.path.join(PROJECT_DIR, "data", "subscribers.json")

    with open(zones_file, "r") as f:
        zones = json.load(f)
    with open(routes_file, "r") as f:
        routes = json.load(f)
    with open(subs_file, "r") as f:
        subscribers = json.load(f)

    return zones, routes, subscribers

def run_pipeline(target_simulated_zone_id=None):
    """
    Executes a full monitoring cycle across all demo zones.
    If target_simulated_zone_id is provided, forces extreme rainfall on that specific zone (FR-10).
    """
    zones, routes, subscribers = load_data()
    predictor = get_predictor()
    results = []

    for zone in zones:
        zid = zone["zone_id"]
        is_simulated = (target_simulated_zone_id == zid)

        # 1. Fetch weather
        if is_simulated:
            weather = generate_extreme_rainfall_simulation(zone)
        else:
            weather = fetch_weather_for_zone(zone)

        # 2. Extract feature set
        features = {
            "rainfall_1h": weather["rainfall_1h"],
            "rainfall_24h": weather["rainfall_24h"],
            "rainfall_72h": weather["rainfall_72h"],
            "slope_angle": zone["slope_angle"],
            "soil_moisture_proxy": weather["soil_moisture_proxy"],
            "historical_landslide_count": zone["historical_landslide_count"]
        }

        # 3. Model Prediction
        pred = predictor.predict(features)

        # 4. Persist to DB
        log_reading(
            zone_id=zid,
            rainfall_1h=weather["rainfall_1h"],
            rainfall_24h=weather["rainfall_24h"],
            rainfall_72h=weather["rainfall_72h"],
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            soil_moisture_proxy=weather["soil_moisture_proxy"],
            is_simulated=1 if is_simulated else 0
        )
        log_risk_assessment(
            zone_id=zid,
            risk_score=pred["risk_score"],
            risk_level=pred["risk_level"],
            risk_drivers=pred["risk_drivers"]
        )

        # 5. Threshold Check & Alert Trigger
        route_info = routes.get(zid, {})
        alerts_sent = []
        if pred["is_high_risk"]:
            zone_subs = [s for s in subscribers if s["zone_id"] == zid]
            if not zone_subs:
                # Default generic contact if none explicitly mapped
                zone_subs = [{"phone_number": "+919876543210", "name": "Regional Disaster Response", "role": "Emergency Liaison"}]
            alerts_sent = send_alert_for_zone(zone, pred["risk_score"], route_info, zone_subs)

        results.append({
            "zone_id": zid,
            "zone_name": zone["zone_name"],
            "region": zone["region"],
            "latitude": zone["latitude"],
            "longitude": zone["longitude"],
            "slope_angle": zone["slope_angle"],
            "weather": weather,
            "prediction": pred,
            "route_advisory": route_info,
            "alerts_dispatched": alerts_sent,
            "is_simulated_high_risk": is_simulated
        })

    return results
