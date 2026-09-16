"""
TerraNova - Live Monitoring & Stage Demonstration Dashboard
Smart India Hackathon 2026 (PS ID 26001)
Built with Streamlit and PyDeck.
"""

import os
import sys
import json
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import pydeck as pdk

# Ensure project root is on sys.path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from database.db import (
    init_db,
    seed_initial_state,
    get_latest_zone_readings,
    get_latest_risk_assessments,
    get_all_alerts,
    log_reading,
    log_risk_assessment
)
from services.pipeline import run_pipeline, load_data

st.set_page_config(
    page_title="TerraNova | Landslide Early Warning System",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for stage presentation aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-low { background-color: #065f46; color: #34d399; border: 1px solid #059669; }
    .badge-med { background-color: #78350f; color: #fbbf24; border: 1px solid #d97706; }
    .badge-high { background-color: #7f1d1d; color: #f87171; border: 1px solid #dc2626; animation: pulse 1.5s infinite; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .zone-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #334155;
        margin-bottom: 14px;
        transition: transform 0.2s ease;
    }
    .zone-card-high {
        background-color: #2b1111;
        border: 2px solid #ef4444;
        box-shadow: 0 0 18px rgba(239, 68, 68, 0.25);
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .reroute-box {
        background: linear-gradient(135deg, #3f1010 0%, #1c1917 100%);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB and seed baseline if not present
init_db()
seed_initial_state()

# Load zones and routes
zones, routes, subscribers = load_data()

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/mountain.png", width=64)
    st.markdown("### **TerraNova Control Center**")
    st.markdown("**Smart India Hackathon 2026**\n*Problem Statement ID: 26001*")
    st.markdown("---")

    st.markdown("#### ⚡ **Stage Demo Trigger (FR-10)**")
    st.caption("Simulate cloudburst & extreme rainfall live to witness real-time flip (<10s).")
    
    target_zone_name = st.selectbox(
        "Select Demo Zone to Flood:",
        options=[z["zone_name"] for z in zones],
        index=0
    )
    target_zone = next(z for z in zones if z["zone_name"] == target_zone_name)
    target_zone_id = target_zone["zone_id"]

    if st.button("🚨 SIMULATE HIGH RAINFALL", use_container_width=True, type="primary"):
        with st.spinner("Injecting extreme precipitation & running ML risk scoring..."):
            t_start = time.time()
            results = run_pipeline(target_simulated_zone_id=target_zone_id)
            duration = round(time.time() - t_start, 2)
            st.toast(f"⚡ Live flip completed in {duration}s! SMS dispatched.", icon="🚨")
            time.sleep(0.4)
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔄 **Routine Monitoring Cycle (FR-9)**")
    if st.button("Fetch Live / Normal Readings", use_container_width=True):
        with st.spinner("Polling meteorological feeds..."):
            run_pipeline(target_simulated_zone_id=None)
            st.toast("Weather cycle updated across all zones.", icon="✅")
            time.sleep(0.3)
            st.rerun()

    if st.button("Reset to Stable Baseline", use_container_width=True):
        for z in zones:
            log_reading(z["zone_id"], 2.5, 18.0, 42.0, 20.0, 70.0, z.get("baseline_moisture", 35.0), 0)
            log_risk_assessment(z["zone_id"], 15.0, "Low", ["Baseline seasonal conditions"])
        st.toast("All zones reset to safe baseline.", icon="🧹")
        time.sleep(0.3)
        st.rerun()

    st.markdown("---")
    st.caption("⚙️ **System Configuration**\n- Model: RandomForest (120 trees, 97.6% Acc)\n- Latency: < 2.0s REST API\n- Storage: SQLite Thread-Safe Engine\n- Fail-Safe: Automatic Synthetic Fallback")

# ----------------- MAIN VIEW -----------------
# Header
col_header, col_time = st.columns([3, 1])
with col_header:
    st.markdown('<div class="main-title">⛰️ TerraNova — Landslide Risk Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI-Powered Disaster Early-Warning, Hazard Prediction & Dynamic Detour Engine | North Eastern Region Focus</div>', unsafe_allow_html=True)
with col_time:
    st.markdown(f"<div style='text-align: right; padding-top: 10px;'><span class='status-badge badge-low'>● Live Engine Active</span><br><small style='color:#64748b;'>Updated: {datetime.now().strftime('%H:%M:%S UTC')}</small></div>", unsafe_allow_html=True)

# Fetch current readings and risk assessments
readings_list = get_latest_zone_readings()
assessments_list = get_latest_risk_assessments()

readings_map = {r["zone_id"]: r for r in readings_list}
assessments_map = {a["zone_id"]: a for a in assessments_list}

# Prepare consolidated zone data
zone_data = []
high_risk_zones = []

for z in zones:
    zid = z["zone_id"]
    r = readings_map.get(zid, {})
    a = assessments_map.get(zid, {})
    
    score = a.get("risk_score", 15.0)
    level = a.get("risk_level", "Low")
    drivers = []
    if a.get("risk_drivers"):
        try:
            drivers = json.loads(a["risk_drivers"])
        except Exception:
            drivers = [a["risk_drivers"]]

    item = {
        **z,
        "rainfall_1h": r.get("rainfall_1h", 0.0),
        "rainfall_24h": r.get("rainfall_24h", 0.0),
        "rainfall_72h": r.get("rainfall_72h", 0.0),
        "temperature": r.get("temperature", 20.0),
        "humidity": r.get("humidity", 70.0),
        "soil_moisture": r.get("soil_moisture_proxy", z.get("baseline_moisture", 35.0)),
        "is_simulated": r.get("is_simulated", 0),
        "risk_score": score,
        "risk_level": level,
        "risk_drivers": drivers,
        "alternate_route": routes.get(zid, {})
    }
    zone_data.append(item)
    if level == "High":
        high_risk_zones.append(item)

# ----------------- TOP METRICS BAR -----------------
alerts = get_all_alerts(limit=50)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric(label="MONITORED CORRIDORS", value=len(zones))
with m2:
    high_count = len(high_risk_zones)
    st.metric(
        label="CRITICAL RISK ZONES",
        value=high_count,
        delta=f"{high_count} Active Alerts" if high_count > 0 else "All Normal",
        delta_color="inverse" if high_count > 0 else "normal"
    )
with m3:
    max_rain24 = max([z["rainfall_24h"] for z in zone_data]) if zone_data else 0.0
    st.metric(label="MAX 24H RAINFALL", value=f"{max_rain24:.1f} mm")
with m4:
    avg_saturation = sum([z["soil_moisture"] for z in zone_data]) / len(zone_data) if zone_data else 0.0
    st.metric(label="AVG SOIL SATURATION", value=f"{avg_saturation:.1f}%")
with m5:
    st.metric(label="ALERTS DISPATCHED", value=len(alerts))

st.markdown("---")

# ----------------- CRITICAL REROUTE ADVISORY (FR-7) -----------------
if high_risk_zones:
    for hz in high_risk_zones:
        route = hz["alternate_route"]
        st.markdown(f"""
        <div class="reroute-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="color: #ef4444; margin: 0;">🚨 HIGH RISK EVACUATION & DETOUR ADVISORY: {hz['zone_name']}</h3>
                <span class="status-badge badge-high">RISK SCORE: {hz['risk_score']}%</span>
            </div>
            <p style="margin-top: 8px; font-size: 1rem; color: #fca5a5;">
                {route.get('advisory_bulletin', 'Extreme geological instability. Primary route closed.')}
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 14px;">
                <div style="background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 8px;">
                    <span style="font-size: 0.75rem; color: #94a3b8;">PRIMARY BLOCKED CORRIDOR:</span><br>
                    <strong style="color: #fda4af;">{route.get('primary_route', hz['zone_name'])}</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 8px;">
                    <span style="font-size: 0.75rem; color: #94a3b8;">RECOMMENDED SAFE BYPASS:</span><br>
                    <strong style="color: #86efac;">{route.get('alternate_route_name', 'Designated Ridge Bypass')}</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 8px;">
                    <span style="font-size: 0.75rem; color: #94a3b8;">DETOUR OVERHEAD:</span><br>
                    <strong style="color: #e2e8f0;">+{route.get('detour_additional_km', 25)} km ({route.get('estimated_additional_time', '1 hr')})</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px 14px; border-radius: 8px;">
                    <span style="font-size: 0.75rem; color: #94a3b8;">HAZARD AVOIDANCE:</span><br>
                    <strong style="color: #fde047;">{route.get('hazard_avoidance', 'Low slope stable valley')}</strong>
                </div>
            </div>
            <div style="margin-top: 16px;">
                <a href="{route.get('google_maps_url', 'https://maps.google.com')}" target="_blank" style="
                    display: inline-block;
                    background-color: #ef4444;
                    color: white;
                    padding: 9px 18px;
                    border-radius: 8px;
                    font-weight: 700;
                    text-decoration: none;
                    font-size: 0.9rem;
                    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
                ">🗺️ Open Safe Alternate Route Navigation in Google Maps ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- GEOGRAPHIC RISK MAP & ZONE CARDS -----------------
tab_map, tab_cards, tab_alerts, tab_explain = st.tabs([
    "🗺️ Interactive Mountain Risk Map",
    "📊 Zone Telemetry Cards",
    "📱 SMS Alert Dispatch Audit Log",
    "🧠 Model Diagnostics & Explainability"
])

with tab_map:
    # Build Map Data
    map_rows = []
    for z in zone_data:
        # Determine Color: Red, Amber, Green
        if z["risk_level"] == "High":
            color = [239, 68, 68, 220] # Red
            radius = 18000
        elif z["risk_level"] == "Medium":
            color = [245, 158, 11, 200] # Orange
            radius = 14000
        else:
            color = [16, 185, 129, 180] # Green
            radius = 11000

        map_rows.append({
            "name": z["zone_name"],
            "region": z["region"],
            "lat": z["latitude"],
            "lon": z["longitude"],
            "slope": f"{z['slope_angle']}°",
            "rain24": f"{z['rainfall_24h']} mm",
            "risk_score": f"{z['risk_score']}%",
            "risk_level": z["risk_level"],
            "color": color,
            "radius": radius
        })

    map_df = pd.DataFrame(map_rows)

    # PyDeck Map
    view_state = pdk.ViewState(
        latitude=25.8,
        longitude=91.5,
        zoom=6.8,
        pitch=35
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.85,
        stroked=True,
        filled=True,
        radius_min_pixels=10,
        radius_max_pixels=40,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255, 180]
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<b>{name}</b> ({region})<br/>"
                    "Status: <b>{risk_level}</b> ({risk_score})<br/>"
                    "Slope Angle: {slope}<br/>"
                    "24h Rainfall: {rain24}",
            "style": {"backgroundColor": "#0f172a", "color": "white", "borderRadius": "8px", "padding": "10px"}
        }
    )

    st.pydeck_chart(deck, use_container_width=True)
    
    # Legend
    leg1, leg2, leg3 = st.columns(3)
    with leg1:
        st.markdown("<span style='color:#34d399; font-weight:bold;'>● LOW RISK (<40%)</span>: Baseline slope stability, green passage.", unsafe_allow_html=True)
    with leg2:
        st.markdown("<span style='color:#fbbf24; font-weight:bold;'>● MEDIUM RISK (40-69%)</span>: Elevated saturation, caution advised.", unsafe_allow_html=True)
    with leg3:
        st.markdown("<span style='color:#f87171; font-weight:bold;'>● HIGH RISK (≥70%)</span>: Critical hazard! Mandatory closure & reroute triggered.", unsafe_allow_html=True)

with tab_cards:
    cols = st.columns(len(zone_data))
    for i, z in enumerate(zone_data):
        with cols[i]:
            card_class = "zone-card-high" if z["risk_level"] == "High" else "zone-card"
            badge_class = "badge-high" if z["risk_level"] == "High" else ("badge-med" if z["risk_level"] == "Medium" else "badge-low")
            
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
                    <div>
                        <strong style="font-size:0.95rem; color:#f1f5f9;">{z['zone_name']}</strong><br/>
                        <span style="font-size:0.75rem; color:#94a3b8;">📍 {z['region']}</span>
                    </div>
                    <span class="status-badge {badge_class}">{z['risk_level']}</span>
                </div>
                <div style="margin: 12px 0 6px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:4px;">
                        <span>Risk Probability</span>
                        <strong>{z['risk_score']}%</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Native Streamlit progress bar for clean cross-browser rendering
            st.progress(min(1.0, z["risk_score"] / 100.0))

            # Details
            st.caption(f"⛰️ Slope: **{z['slope_angle']}°** | Past Events: **{z['historical_landslide_count']}**")
            st.caption(f"🌧️ Rain (1h/24h/72h): **{z['rainfall_1h']} / {z['rainfall_24h']} / {z['rainfall_72h']} mm**")
            st.caption(f"💧 Soil Moisture: **{z['soil_moisture']}%**")
            
            with st.expander("Geological Drivers"):
                for d in z["risk_drivers"]:
                    st.write(f"• {d}")

with tab_alerts:
    st.markdown("#### **Real-Time Emergency SMS Broadcast Audit Trail (FR-6)**")
    st.caption("Logs dispatch events triggered when any monitored zone crosses the critical risk threshold (score ≥ 70%).")

    if alerts:
        formatted_alerts = []
        for a in alerts:
            formatted_alerts.append({
                "Timestamp (UTC)": a["timestamp"][:19].replace("T", " "),
                "Zone": a["zone_name"],
                "Risk Score": f"{a['risk_score']}%",
                "Recipient Contact": f"{a['subscriber_name']} ({a['subscriber_phone']})",
                "Delivery Status": a["status"],
                "Dispatched Message Payload": a["message_content"]
            })
        
        df_alerts = pd.DataFrame(formatted_alerts)
        st.dataframe(
            df_alerts,
            column_config={
                "Dispatched Message Payload": st.column_config.TextColumn("SMS Content", width="large"),
                "Delivery Status": st.column_config.TextColumn("Status", width="medium"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No critical alerts logged yet. System status is safe across all monitored mountain zones.")

with tab_explain:
    st.markdown("#### **Explainable AI: Landslide Trigger Feature Attribution**")
    st.caption("Random Forest Model Feature Weights calibrated against Geological Survey of India (GSI) thresholds.")

    meta_file = os.path.join(PROJECT_DIR, "model", "model_meta.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            meta = json.load(f)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("ROC-AUC Score", meta.get("roc_auc", 0.99))
        with col_m2:
            st.metric("Model Accuracy", f"{meta.get('accuracy', 0.97) * 100:.1f}%")
        with col_m3:
            st.metric("Recall (Failure Catch)", f"{meta.get('recall', 0.95) * 100:.1f}%")
        with col_m4:
            st.metric("F1 Score", meta.get("f1_score", 0.90))

        fi = meta.get("feature_importances", {})
        fi_df = pd.DataFrame([
            {"Feature Predictor": k.replace("_", " ").title(), "Importance (%)": v * 100}
            for k, v in fi.items()
        ]).sort_values("Importance (%)", ascending=True)

        st.bar_chart(fi_df.set_index("Feature Predictor"))

        st.markdown("""
        **Physical Rationale:**
        1. **Cumulative 24h & 72h Rainfall:** Prolonged precipitation saturates mountain soil pores, causing hydrostatic pore-pressure build-up and reducing internal soil friction.
        2. **Soil Moisture Saturation Proxy:** Saturated clay/shale layers act as lubrication planes along steep bedrock.
        3. **Slope Angle:** Inclinations above 32° drastically increase shear stress relative to gravitational shear strength.
        """)
