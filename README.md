# ⛰️ TerraNova — Landslide Risk Monitoring System (MVP)

**Smart India Hackathon 2026** | **Problem Statement ID: 26001**  
*An End-to-End AI-Powered Disaster Early-Warning, Hazard Scoring & Safe Reroute Engine for the North Eastern Region (NER) of India.*

---

## 📌 1. Project Overview

TerraNova is an end-to-end landslide early-warning MVP engineered for mountainous, disaster-prone regions (with a focus on critical mountain highway corridors across Sikkim, Meghalaya, Mizoram, Nagaland, and Arunachal Pradesh). 

The prototype demonstrates a closed-loop disaster pipeline:
$$\text{Collect Weather/Terrain Data} \longrightarrow \text{Predict Landslide Risk per Zone} \longrightarrow \text{Trigger Emergency SMS} \longrightarrow \text{Suggest Safe Alternate Bypass} \longrightarrow \text{Live Stage Dashboard}$$

### 🎯 Scope Alignment (from SRS Spec)
- **Included in MVP (Explicitly IN):**
  - [x] Scikit-Learn `RandomForestClassifier` trained on physical landslide predictors.
  - [x] Live/Simulated weather data pipeline (`rainfall_1h`, `rainfall_24h`, `rainfall_72h`, temperature, humidity).
  - [x] Real-time Flask REST API (`/predict`, `/api/zones`, `/api/simulate-rainfall`, `/api/pipeline/run`).
  - [x] SQLite thread-safe local persistence layer (zero paid cloud dependencies).
  - [x] Automated SMS emergency dispatch engine with delivery receipts (Twilio / Fast2SMS / Simulated Gateway).
  - [x] Predefined static alternate route suggestions with direct Google Maps navigation links.
  - [x] Interactive Streamlit Stage Demonstration Dashboard with PyDeck 3D map.
  - [x] 1-Click **"Simulate High Rainfall"** live stage trigger that executes the entire loop in **< 1.5 seconds** (SRS requirement: < 10s).
- **Out of Scope (Explicitly Future Work):**
  - Drone-based photogrammetry / post-disaster LIDAR scans.
  - True AI-based multi-agent dynamic traffic optimization.
  - Multi-region Kubernetes auto-scaling.
  - Native iOS/Android apps (web responsive dashboard provided for MVP).

---

## 🏛️ 2. System Architecture

```
                                  ┌────────────────────────┐
                                  │ OpenWeatherMap API     │
                                  │ (or Fallback Generator)│
                                  └───────────┬────────────┘
                                              │
                                              ▼
┌──────────────────┐               ┌───────────────────────┐
│ Static Terrain   │──────────────▶│ Feature Extraction    │
│ Dataset (Slope,  │               │ (1h, 24h, 72h Rain,   │
│ Past Landslides) │               │  Moisture, Slope)     │
└──────────────────┘               └───────────┬───────────┘
                                               │
                                               ▼
                                   ┌───────────────────────┐
                                   │ Random Forest Model   │ (ROC-AUC: 0.994)
                                   │ (Scikit-Learn .joblib)│ (Accuracy: 97.6%)
                                   └───────────┬───────────┘
                                               │
                                               ▼
                                   ┌───────────────────────┐
                                   │ Flask REST API        │ (Sub-30ms Latency)
                                   │ /api/predict          │
                                   └───────────┬───────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
            [Risk Score >= 70%?]                             [Persist to SQLite]
              /              \                                (terranova.db)
            YES               NO                                       │
            /                  \                                       ▼
 ┌─────────────────────┐   ┌───────────────────────┐       ┌───────────────────────┐
 │ Emergency SMS Alert │   │ Routine Telemetry     │       │ Streamlit Dashboard   │
 │ Dispatch (Twilio/   │   │ Update Only           │       │ (PyDeck 3D Map,       │
 │ Fast2SMS / Gateway) │   └───────────────────────┘       │  Telemetry Cards,     │
 └──────────┬──────────┘                                   │  Live Audit Log)      │
            │                                              └───────────────────────┘
            ▼
 ┌─────────────────────┐
 │ Safe Bypass Route   │
 │ (Google Maps Link)  │
 └─────────────────────┘
```

---

## 🗺️ 3. Monitored North Eastern Region (NER) Corridors

| Zone ID | Highway Corridor | Region / State | Slope Angle | Baseline Soil | Critical Alternate Bypass Route |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NER_ZONE_01` | **NH-10 Gangtok-Siliguri Corridor** | Sikkim | 38.5° | Weathered gneiss | Lava - Gorubathan - Damdim Bypass (via Kalimpong) |
| `NER_ZONE_02` | **Shillong Peak - Cherrapunji Bypass** | Meghalaya | 32.0° | Sedimentary sandstone | Mawkdok - Mawlyndep - Tyrsad Valley Diversion |
| `NER_ZONE_03` | **NH-54 Aizawl - Sairang Road** | Mizoram | 35.8° | Unstable shale | Lengpui Airport Road via Tanhril Bypass |
| `NER_ZONE_04` | **NH-29 Kohima - Dimapur Highway** | Nagaland | 29.5° | Disuris siltstone | Jotsoma - Khonoma - Sechü Zubza Ring Road |
| `NER_ZONE_05` | **BCT Highway - Tawang Pass** | Arunachal Pradesh | 42.0° | Orthogneiss scree | Sela Tunnel Lower Valley Bypass |

---

## 💻 4. Tech Stack

- **Core Language:** Python 3.10+ (tested on Python 3.13)
- **Machine Learning:** `scikit-learn` (RandomForestClassifier with balanced class weighting), `pandas`, `numpy`, `joblib`
- **Backend API:** `Flask` (RESTful architecture)
- **Database:** `SQLite3` (thread-safe, local file persistence `database/terranova.db`)
- **Dashboard:** `Streamlit`, `pydeck` (interactive 3D maps and real-time state re-rendering)
- **Alert Providers:** Pluggable `Twilio` SMS SDK, `Fast2SMS` API, or high-fidelity simulated SMS gateway

---

## 🚀 5. Quick Start Instructions

### Prerequisites
Make sure Python is installed. Clone or navigate to the repository directory:
```bash
cd terranova
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Launch the Complete Prototype (API + Dashboard)
Run the one-click master launcher:
```bash
python run_demo.py
```
This script will:
1. Validate datasets and train the ML model if not already present.
2. Initialize and seed the SQLite database.
3. Start the Flask REST API on `http://127.0.0.1:5000`.
4. Launch the Streamlit presentation dashboard on `http://localhost:8501`.

*(Alternatively, run the dashboard alone using: `streamlit run dashboard/app.py`)*

---

## 🎬 6. Hackathon Live Pitch Demonstration Script

Follow this **60-second stage demo workflow** in front of judges:

1. **Baseline Overview (0:00 - 0:15):**
   - Open `http://localhost:8501`.
   - Point to the **Top Metrics Bar**: 5 Monitored mountain corridors across the North Eastern Region, 0 Critical Risk zones, all markers green.
   - Point out the **PyDeck 3D Interactive Map** showing the geological terrain and current weather telemetry.
2. **The Cloudburst Trigger (0:15 - 0:30):**
   - In the left sidebar under **"Stage Demo Trigger"**, select **"NH-10 Gangtok-Siliguri Corridor"**.
   - Click the big red button: **🚨 SIMULATE HIGH RAINFALL**.
3. **Instant Real-Time Flip (0:30 - 0:45):**
   - In under **1.5 seconds** (surpassing the SRS 10s benchmark):
     - Gangtok NH-10 flips to **CRITICAL HIGH RISK (99.9% probability)**.
     - The map pin flashes **Crimson Red**.
     - A high-contrast **RED ALERT BANNER** slides into view.
4. **Emergency Detour & SMS Audit (0:45 - 1:00):**
   - Show the recommended alternate bypass: *"Lava - Gorubathan - Damdim Bypass (via Kalimpong) (+34 km)"*.
   - Click **"Open Safe Alternate Route Navigation in Google Maps"** to show instant detour routing.
   - Switch to the **"📱 SMS Alert Dispatch Audit Log"** tab: show the delivered alert dispatched to the Sikkim State Disaster Management Authority (SSDMA) and Traffic SP.
   - Switch to the **"🧠 Model Diagnostics"** tab: show the ROC-AUC of 0.994 and the feature importances (24h rain = 43%, 72h rain = 22%, soil moisture = 18.8%).

---

## 📡 7. REST API Reference

### Health Check
```http
GET /api/health
```
```json
{
  "service": "TerraNova Landslide Risk Monitoring API",
  "status": "healthy",
  "version": "1.0.0"
}
```

### Risk Prediction Endpoint
```http
POST /api/predict
Content-Type: application/json

{
  "rainfall_1h": 45.0,
  "rainfall_24h": 180.0,
  "rainfall_72h": 320.0,
  "slope_angle": 38.5,
  "soil_moisture_proxy": 85.0,
  "historical_landslide_count": 14
}
```
**Response:**
```json
{
  "prediction": {
    "is_high_risk": true,
    "risk_drivers": [
      "Heavy 24h Cumulative Precipitation (180.0 mm)",
      "Extended 72h Ground Saturation (320.0 mm)",
      "High-Intensity Cloudburst / Flash Rain (45.0 mm/hr)",
      "Critical Soil Moisture Pore-Pressure (85.0%)",
      "Steep Unstable Slope Incline (38.5°)"
    ],
    "risk_level": "High",
    "risk_score": 99.8
  },
  "execution_time_ms": 2.4,
  "status": "success"
}
```

### Force Stage Simulation Endpoint
```http
POST /api/simulate-rainfall
Content-Type: application/json

{
  "zone_id": "NER_ZONE_01"
}
```

### Query All Zones
```http
GET /api/zones
```

### Query Alert Logs
```http
GET /api/alerts?limit=10
```

---

## 🧪 8. Automated Verification Suite

Run the full automated test suite covering all Functional Requirements (FR-1 to FR-10) and Non-Functional Requirements (NFR-1 to NFR-5):
```bash
python tests/test_system.py
```
**Test Results:**
```
test_fr1_weather_collection ............. OK
test_fr2_static_terrain_data ............ OK
test_fr3_model_risk_scoring ............. OK
test_fr4_and_nfr2_rest_api_endpoint ..... OK (26.5 ms, limit: 2000 ms)
test_fr5_and_fr6_sms_alerting_logging .. OK (SQLite audited)
test_fr7_alternate_route_suggestion ..... OK (Lava-Gorubathan Bypass)
test_fr8_dashboard_data_availability ... OK (5 zones ready)
test_fr9_manual_refresh_cycle ........... OK (0.15s)
test_fr10_stage_demo_simulation ......... OK (1.10s, limit: 10s)
----------------------------------------------------------------------
Ran 9 tests in 1.34s -- OK (100% PASSED)
```

---

## 📋 9. SRS Compliance Checklist

| SRS Req ID | Requirement Statement | Status | Implementation Details |
| :--- | :--- | :--- | :--- |
| **FR-1** | Fetch current weather data from API | ✅ Completed | `services/weather_service.py` with OpenWeatherMap & synthetic fallback |
| **FR-2** | Store static terrain data per zone | ✅ Completed | `data/zones.json` (slope angle, historical count, soil type) |
| **FR-3** | Compute landslide risk score via ML model | ✅ Completed | `model/predict.py` using trained `RandomForestClassifier` |
| **FR-4** | Expose risk score via REST API | ✅ Completed | `api/app.py` `/api/predict` & `/api/zones` |
| **FR-5** | Trigger SMS alert when score > threshold | ✅ Completed | `services/alert_service.py` (Twilio / Fast2SMS / Gateway) |
| **FR-6** | Log every alert with timestamp, zone, score | ✅ Completed | `database/db.py` SQLite `alerts_log` table with audit query |
| **FR-7** | Predefined alternate route suggestion | ✅ Completed | `data/routes.json` with Google Maps direct navigation URLs |
| **FR-8** | Display dashboard showing all zones & alerts | ✅ Completed | `dashboard/app.py` Streamlit UI with 3D PyDeck map & cards |
| **FR-9** | Manual refresh / re-run cycle for demo | ✅ Completed | "Fetch Live / Normal Readings" button & `/api/pipeline/run` |
| **FR-10** | Demo "simulate high rainfall" trigger on stage | ✅ Completed | 1-Click sidebar button & `/api/simulate-rainfall` (<1.5s flip) |
| **NFR-1** | Dashboard load & refresh < 3 seconds | ✅ Completed | Streamlit caching & sub-second render |
| **NFR-2** | API responds within 2 seconds | ✅ Completed | Model inference latency ~25ms |
| **NFR-3** | Runs entirely on free-tier services | ✅ Completed | SQLite + local scikit-learn + synthetic fallback |
| **NFR-4** | Modular codebase | ✅ Completed | Clean separation: `data`, `model`, `database`, `services`, `api`, `dashboard` |
| **NFR-5** | Graceful degradation if APIs fail | ✅ Completed | Resilient fallback generators ensure zero-crash demo |
