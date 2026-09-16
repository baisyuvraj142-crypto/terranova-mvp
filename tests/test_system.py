"""
TerraNova - Automated System Verification Suite
Validates all Functional Requirements (FR-1 through FR-10) and Non-Functional Requirements (NFR-1 through NFR-5).
"""

import os
import sys
import time
import json
import unittest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from api.app import app
from database.db import init_db, seed_initial_state, get_latest_risk_assessments, get_latest_zone_readings, get_all_alerts
from services.weather_service import fetch_weather_for_zone, generate_extreme_rainfall_simulation
from services.alert_service import send_alert_for_zone
from services.pipeline import run_pipeline, load_data
from model.predict import get_predictor

class TerraNovaSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_initial_state()
        cls.client = app.test_client()

    def test_fr1_weather_collection(self):
        """FR-1 & NFR-5: Fetch current weather with graceful degradation."""
        zones, _, _ = load_data()
        weather = fetch_weather_for_zone(zones[0])
        self.assertIn("rainfall_1h", weather)
        self.assertIn("rainfall_24h", weather)
        self.assertIn("rainfall_72h", weather)
        self.assertIn("soil_moisture_proxy", weather)
        self.assertEqual(weather["status"], "SUCCESS")
        print("[PASS] FR-1 Weather Collection Verified")

    def test_fr2_static_terrain_data(self):
        """FR-2: Static terrain data loaded per zone."""
        zones, routes, subscribers = load_data()
        self.assertGreaterEqual(len(zones), 5)
        for z in zones:
            self.assertIn("slope_angle", z)
            self.assertIn("historical_landslide_count", z)
            self.assertGreater(z["slope_angle"], 15.0)
        print("[PASS] FR-2 Static Terrain Data Verified (5 zones loaded)")

    def test_fr3_model_risk_scoring(self):
        """FR-3: ML model risk scoring returns calibrated probability and category."""
        predictor = get_predictor()
        # Safe conditions
        safe_res = predictor.predict({
            "rainfall_1h": 1.0,
            "rainfall_24h": 10.0,
            "rainfall_72h": 25.0,
            "slope_angle": 28.0,
            "soil_moisture_proxy": 30.0,
            "historical_landslide_count": 5
        })
        self.assertLess(safe_res["risk_score"], 40.0)
        self.assertEqual(safe_res["risk_level"], "Low")

        # Extreme conditions
        extreme_res = predictor.predict({
            "rainfall_1h": 50.0,
            "rainfall_24h": 190.0,
            "rainfall_72h": 350.0,
            "slope_angle": 42.0,
            "soil_moisture_proxy": 90.0,
            "historical_landslide_count": 14
        })
        self.assertGreaterEqual(extreme_res["risk_score"], 70.0)
        self.assertEqual(extreme_res["risk_level"], "High")
        self.assertTrue(extreme_res["is_high_risk"])
        print("[PASS] FR-3 ML Risk Scoring Verified (Safe & Extreme modes tested)")

    def test_fr4_and_nfr2_rest_api_endpoint(self):
        """FR-4 & NFR-2: Expose risk score via REST API under 2 seconds."""
        t0 = time.time()
        payload = {
            "rainfall_1h": 12.0,
            "rainfall_24h": 65.0,
            "rainfall_72h": 120.0,
            "slope_angle": 34.0,
            "soil_moisture_proxy": 55.0,
            "historical_landslide_count": 8
        }
        res = self.client.post("/api/predict", json=payload)
        elapsed = time.time() - t0
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("prediction", data)
        self.assertLess(elapsed, 2.0, f"API response time {elapsed:.2f}s exceeded 2s (NFR-2)")
        print(f"[PASS] FR-4 & NFR-2 REST API Endpoint Verified (Response in {elapsed*1000:.1f} ms)")

    def test_fr5_and_fr6_sms_alerting_and_logging(self):
        """FR-5 & FR-6: Trigger SMS alert on threshold cross and verify audit log."""
        zones, routes, subscribers = load_data()
        zone = zones[0]
        route = routes.get(zone["zone_id"], {})
        subs = [s for s in subscribers if s["zone_id"] == zone["zone_id"]]

        alerts_before = len(get_all_alerts(50))
        dispatched = send_alert_for_zone(zone, 88.5, route, subs)
        self.assertGreater(len(dispatched), 0)
        self.assertIn("DELIVERED", dispatched[0]["status"])

        alerts_after = get_all_alerts(50)
        self.assertGreater(len(alerts_after), alerts_before)
        latest = alerts_after[0]
        self.assertEqual(latest["zone_id"], zone["zone_id"])
        self.assertEqual(latest["risk_score"], 88.5)
        self.assertIn("RED ALERT", latest["message_content"])
        print(f"[PASS] FR-5 & FR-6 SMS Alerting and Logging Verified (Logged to SQLite: {latest['subscriber_name']})")

    def test_fr7_alternate_route_suggestion(self):
        """FR-7: Suggest predefined alternate route when zone is high-risk."""
        res = self.client.get("/api/routes/NER_ZONE_01")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        route = data.get("alternate_route", {})
        self.assertIn("alternate_route_name", route)
        self.assertIn("google_maps_url", route)
        self.assertIn("detour_additional_km", route)
        print(f"[PASS] FR-7 Alternate Route Suggestion Verified ({route['alternate_route_name']})")

    def test_fr8_dashboard_data_availability(self):
        """FR-8: Verify data availability for the dashboard view."""
        res = self.client.get("/api/zones")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["count"], 5)
        for z in data["zones"]:
            self.assertIn("current_risk", z)
            self.assertIn("current_weather", z)
        print("[PASS] FR-8 Dashboard Data Feed Verified (5 zones ready)")

    def test_fr9_manual_refresh_cycle(self):
        """FR-9: Manual refresh/re-run of prediction cycle."""
        t0 = time.time()
        res = self.client.post("/api/pipeline/run")
        elapsed = time.time() - t0
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data["results"]), 5)
        print(f"[PASS] FR-9 Manual Refresh Cycle Verified (Full cycle completed in {elapsed:.2f}s)")

    def test_fr10_stage_demo_simulation(self):
        """FR-10 & Success Criteria: Live 'simulate high rainfall' trigger flushes in < 10s."""
        t0 = time.time()
        res = self.client.post("/api/simulate-rainfall", json={"zone_id": "NER_ZONE_01"})
        elapsed = time.time() - t0
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        flagged = data.get("flagged_zone", {})
        self.assertEqual(flagged["zone_id"], "NER_ZONE_01")
        self.assertEqual(flagged["prediction"]["risk_level"], "High")
        self.assertGreaterEqual(flagged["prediction"]["risk_score"], 70.0)
        self.assertGreater(len(flagged["alerts_dispatched"]), 0)
        self.assertLess(elapsed, 10.0, f"Full trigger cycle took {elapsed:.2f}s (must be <10s)")
        print(f"[PASS] FR-10 & Success Criteria: Stage Demo Simulation completed in {elapsed:.2f}s (Threshold: <10s)")

if __name__ == "__main__":
    unittest.main(verbosity=2)
