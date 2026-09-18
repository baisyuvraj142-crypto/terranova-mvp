"""
TerraNova - Next-Gen Disaster Early-Warning Command Center
Smart India Hackathon 2026 (PS ID 26001)
Features: Smooth Navigation, CSS Motion Graphics, 3D PyDeck Terrain Visualization & Interactive AI Simulator.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
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
from model.predict import get_predictor

# Optional smooth navigation menu with graceful fallback
try:
    from streamlit_option_menu import option_menu
    HAS_OPTION_MENU = True
except ImportError:
    HAS_OPTION_MENU = False

# Page Configuration
st.set_page_config(
    page_title="TerraNova | AI Landslide Command Center",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- ADVANCED MOTION GRAPHICS & GLASSMORPHISM CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Top Live Telemetry Ticker */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, #0b1329 0%, #0f172a 50%, #0b1329 100%);
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 6px 0;
        margin-bottom: 14px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        animation: ticker 30s linear infinite;
    }
    .ticker-item {
        display: inline-block;
        padding: 0 24px;
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
    }
    .ticker-highlight {
        color: #38bdf8;
        font-weight: 700;
    }
    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-50%, 0, 0); }
    }

    /* Radar Scanner Motion Graphic */
    .radar-box {
        position: relative;
        width: 76px;
        height: 76px;
        border-radius: 50%;
        border: 2px solid #0284c7;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0.8) 70%);
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
        overflow: hidden;
        margin: auto;
    }
    .radar-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 50%;
        border: 1px dashed rgba(56, 189, 248, 0.4);
        animation: rotate-reverse 12s linear infinite;
    }
    .radar-sweep {
        position: absolute;
        top: 50%; left: 50%;
        width: 38px; height: 38px;
        transform-origin: top left;
        background: conic-gradient(from 0deg, rgba(56, 189, 248, 0.8) 0deg, transparent 65deg);
        animation: radar-spin 2.2s linear infinite;
        border-radius: 50% 0 0 0;
    }
    @keyframes radar-spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes rotate-reverse {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
    }

    /* Threat Pulse Rings */
    .threat-beacon {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .pulse-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 9999px;
        animation: pulse-ring 1.8s cubic-bezier(0.24, 0, 0.38, 1) infinite;
    }
    .pulse-ring-red {
        border: 2px solid #ef4444;
        box-shadow: 0 0 14px rgba(239, 68, 68, 0.6);
    }
    .pulse-ring-green {
        border: 2px solid #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }
    @keyframes pulse-ring {
        0% { transform: scale(0.85); opacity: 1; }
        100% { transform: scale(1.6); opacity: 0; }
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 12px 28px -4px rgba(14, 165, 233, 0.2);
    }
    .glass-card-high {
        background: linear-gradient(145deg, rgba(69, 10, 10, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);
        border: 2px solid #ef4444;
        box-shadow: 0 0 24px rgba(239, 68, 68, 0.35);
        animation: card-alert-glow 2s infinite alternate;
    }
    @keyframes card-alert-glow {
        from { box-shadow: 0 0 14px rgba(239, 68, 68, 0.3); }
        to { box-shadow: 0 0 28px rgba(239, 68, 68, 0.55); }
    }

    /* Emergency Alert Banner */
    .alert-banner {
        background: linear-gradient(135deg, #450a0a 0%, #1e1b18 50%, #0f172a 100%);
        border: 2px solid #ef4444;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 22px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
    }
    .alert-banner::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(239, 68, 68, 0.15), transparent);
        animation: banner-scan 3.5s ease-in-out infinite;
    }
    @keyframes banner-scan {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    /* Badges */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }
    .pill-safe { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .pill-med { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .pill-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB and Seed Baseline
init_db()
seed_initial_state()

# Load Zone Definitions and Data
zones, routes, subscribers = load_data()

# ----------------- TOP BANNER & RADAR HEADER -----------------
col_logo, col_title, col_radar = st.columns([1, 7, 2])

with col_logo:
    st.markdown("""
    <div style="text-align: center; padding-top: 6px;">
        <span style="font-size: 3.2rem; filter: drop-shadow(0 4px 12px rgba(56, 189, 248, 0.4));">⛰️</span>
    </div>
    """, unsafe_allow_html=True)

with col_title:
    st.markdown("""
    <div style="margin-top: -2px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(90deg, #f8fafc 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">TERRANOVA COMMAND</h1>
            <span class="status-pill pill-safe">● LIVE DEFENSE ENGINE</span>
        </div>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.9rem; font-weight: 500;">
            AI Landslide Risk Intelligence, Threat Modeling & Evacuation Routing | <strong>SIH 2026 (PS ID 26001)</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_radar:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 14px;">
        <div class="radar-box">
            <div class="radar-sweep"></div>
        </div>
        <div style="text-align: left;">
            <span style="font-size: 0.68rem; color: #38bdf8; font-weight: 700; text-transform: uppercase;">SURVEILLANCE</span><br>
            <strong style="font-size: 0.88rem; color: #f1f5f9;">5 Active Sectors</strong><br>
            <span style="font-size: 0.72rem; color: #10b981;">● Online (24 ms)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- LIVE TELEMETRY STREAM TICKER -----------------
ticker_items = [
    "Sikkim NH-10 Corridor: Continuous Sensor Polling",
    "Shillong Cherrapunji Ridge: Moisture Sensors Calibrated",
    "Aizawl Sairang Valley: Turbidite Pore-Pressure Nominal",
    "Kohima Dimapur By-Pass: Geotechnical Accelerometers Armed",
    "Tawang Pass Corridor: BRO Highway Alert Protocol Ready",
    "Emergency SMS Gateway: Fast2SMS & Twilio Channels Active"
]
ticker_html = "".join([f'<span class="ticker-item">⚡ <span class="ticker-highlight">{item.split(":")[0]}:</span> {item.split(":")[1]}</span>' for item in ticker_items])

st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker-move">
        {ticker_html} {ticker_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- SMOOTH NAVIGATION MENU -----------------
nav_options = [
    "🛰️ Command Center",
    "📊 Zone Telemetry",
    "🚧 Smart Reroute Engine",
    "📱 SMS Alert Network",
    "🧠 AI What-If Simulator"
]

if HAS_OPTION_MENU:
    selected_view = option_menu(
        menu_title=None,
        options=nav_options,
        icons=["shield-check", "bar-chart-line", "signpost-2", "broadcast-pin", "cpu"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "4px!important", "background-color": "#0f172a", "border-radius": "12px", "border": "1px solid #1e293b", "margin-bottom": "18px"},
            "icon": {"color": "#38bdf8", "font-size": "15px"},
            "nav-link": {"font-size": "13px", "font-weight": "600", "text-align": "center", "margin": "0px 4px", "padding": "8px 14px", "border-radius": "8px", "color": "#94a3b8"},
            "nav-link-selected": {"background": "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)", "color": "#ffffff", "box-shadow": "0 4px 14px rgba(2, 132, 199, 0.4)"}
        }
    )
else:
    selected_view = st.radio("Navigation", nav_options, horizontal=True, label_visibility="collapsed")

# Read DB State
readings_list = get_latest_zone_readings()
assessments_list = get_latest_risk_assessments()
readings_map = {r["zone_id"]: r for r in readings_list}
assessments_map = {a["zone_id"]: a for a in assessments_list}
alerts = get_all_alerts(limit=50)

# Build Zone State List
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
        "risk_score": score,
        "risk_level": level,
        "risk_drivers": drivers,
        "alternate_route": routes.get(zid, {})
    }
    zone_data.append(item)
    if level == "High":
        high_risk_zones.append(item)

# ----------------- QUICK STAGE DEMO TRIGGER BAR (PRESENT ON ALL SCREENS) -----------------
with st.expander("⚡ **QUICK STAGE DEMO ACTIONS (Smart India Hackathon Live Triggers)**", expanded=(len(high_risk_zones) == 0)):
    act_col1, act_col2, act_col3, act_col4 = st.columns([3, 2, 2, 2])
    with act_col1:
        target_zone_name = st.selectbox(
            "Select Mountain Corridor to Trigger:",
            options=[z["zone_name"] for z in zones],
            index=0,
            key="global_sim_target"
        )
        target_zid = next(z["zone_id"] for z in zones if z["zone_name"] == target_zone_name)
    with act_col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚨 SIMULATE HIGH RAINFALL", type="primary", use_container_width=True):
            t0 = time.time()
            run_pipeline(target_simulated_zone_id=target_zid)
            st.toast(f"⚡ Extreme cloudburst injected! Live flip in {time.time()-t0:.2f}s!", icon="🚨")
            time.sleep(0.3)
            st.rerun()
    with act_col3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Poll Live Weather", use_container_width=True):
            run_pipeline(target_simulated_zone_id=None)
            st.toast("Weather telemetry refreshed.", icon="🌦️")
            time.sleep(0.3)
            st.rerun()
    with act_col4:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🧹 Reset to Baseline", use_container_width=True):
            for z in zones:
                log_reading(z["zone_id"], 2.5, 18.0, 42.0, 20.0, 70.0, z.get("baseline_moisture", 35.0), 0)
                log_risk_assessment(z["zone_id"], 15.0, "Low", ["Baseline seasonal conditions"])
            st.toast("System restored to safe green baseline.", icon="✅")
            time.sleep(0.3)
            st.rerun()

# ----------------- VIEW 1: COMMAND CENTER -----------------
if "Command Center" in selected_view:
    # Critical Alert Notification Banner if high risk exists
    if high_risk_zones:
        for hz in high_risk_zones:
            route = hz["alternate_route"]
            st.markdown(f"""
            <div class="alert-banner">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span class="threat-beacon">
                            <span class="pulse-ring pulse-ring-red"></span>
                            <span style="font-size: 1.8rem;">🚨</span>
                        </span>
                        <div>
                            <span class="status-pill pill-danger">CRITICAL THREAT ACTIVE</span>
                            <h3 style="color: #ffffff; margin: 4px 0 0 0; font-size: 1.35rem; font-weight: 800;">
                                {hz['zone_name']} Flagged High Risk ({hz['risk_score']}%)
                            </h3>
                        </div>
                    </div>
                    <div>
                        <span style="background: rgba(239,68,68,0.25); border: 1px solid #ef4444; color: #fca5a5; font-size: 0.8rem; font-weight: 700; padding: 6px 14px; border-radius: 8px;">
                            EMERGENCY DETOUR ACTIVE
                        </span>
                    </div>
                </div>
                <p style="color: #fca5a5; margin: 12px 0 16px 0; font-size: 0.95rem;">
                    {route.get('advisory_bulletin', 'Severe slope instability detected. Primary route closed to all transit.')}
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-bottom: 16px;">
                    <div style="background: rgba(0,0,0,0.35); padding: 12px 14px; border-radius: 10px; border-left: 3px solid #ef4444;">
                        <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">CLOSED HIGHWAY</span><br>
                        <strong style="color: #fda4af; font-size: 0.92rem;">{route.get('primary_route', hz['zone_name'])}</strong>
                    </div>
                    <div style="background: rgba(0,0,0,0.35); padding: 12px 14px; border-radius: 10px; border-left: 3px solid #10b981;">
                        <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">SAFE ALTERNATE BYPASS</span><br>
                        <strong style="color: #86efac; font-size: 0.92rem;">{route.get('alternate_route_name', 'Ridge Valley Route')}</strong>
                    </div>
                    <div style="background: rgba(0,0,0,0.35); padding: 12px 14px; border-radius: 10px; border-left: 3px solid #38bdf8;">
                        <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">DETOUR OVERHEAD</span><br>
                        <strong style="color: #e2e8f0; font-size: 0.92rem;">+{route.get('detour_additional_km', 25)} km ({route.get('estimated_additional_time', '1 hr')})</strong>
                    </div>
                </div>
                <a href="{route.get('google_maps_url', 'https://maps.google.com')}" target="_blank" style="
                    display: inline-block;
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    color: white;
                    padding: 10px 22px;
                    border-radius: 10px;
                    font-weight: 700;
                    text-decoration: none;
                    font-size: 0.9rem;
                    box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
                ">🗺️ Open Safe Alternate Route in Google Maps ↗</a>
            </div>
            """, unsafe_allow_html=True)

    # Key Stat Metrics Strip
    stat1, stat2, stat3, stat4, stat5 = st.columns(5)
    with stat1:
        st.metric("MONITORED CORRIDORS", f"{len(zones)} Sectors", delta="Full NER Coverage")
    with stat2:
        high_cnt = len(high_risk_zones)
        st.metric("CRITICAL ZONES", f"{high_cnt}", delta=f"{high_cnt} Red Alert" if high_cnt > 0 else "All Normal", delta_color="inverse" if high_cnt > 0 else "normal")
    with stat3:
        max_r24 = max([z["rainfall_24h"] for z in zone_data]) if zone_data else 0.0
        st.metric("PEAK 24H RAINFALL", f"{max_r24:.1f} mm", delta="Cloudburst alert" if max_r24 > 100 else "Stable", delta_color="inverse" if max_r24 > 100 else "normal")
    with stat4:
        avg_moist = sum([z["soil_moisture"] for z in zone_data]) / len(zone_data) if zone_data else 0.0
        st.metric("AVG SOIL SATURATION", f"{avg_moist:.1f}%", delta="Pore saturation" if avg_moist > 70 else "Porous")
    with stat5:
        st.metric("ALERTS DISPATCHED", f"{len(alerts)} Logs", delta="Instant SMS Gateway")

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # 3D PyDeck Terrain Visualization
    st.markdown("### 🗺️ **3D Terrain Hazard Visualization & Satellite Radar**")
    st.caption("3D Column height represents 24-hour rainfall accumulation; glow color indicates ML landslide risk classification.")

    map_rows = []
    for z in zone_data:
        if z["risk_level"] == "High":
            col = [239, 68, 68, 220]
            col_dark = [185, 28, 28, 240]
            elevation = max(25000, z["rainfall_24h"] * 350)
            radius = 22000
        elif z["risk_level"] == "Medium":
            col = [245, 158, 11, 200]
            col_dark = [180, 83, 9, 230]
            elevation = max(15000, z["rainfall_24h"] * 250)
            radius = 16000
        else:
            col = [16, 185, 129, 180]
            col_dark = [4, 120, 87, 210]
            elevation = max(8000, z["rainfall_24h"] * 180)
            radius = 12000

        map_rows.append({
            "name": z["zone_name"],
            "region": z["region"],
            "lat": z["latitude"],
            "lon": z["longitude"],
            "elevation": elevation,
            "slope": f"{z['slope_angle']}°",
            "rain24": f"{z['rainfall_24h']} mm",
            "moist": f"{z['soil_moisture']}%",
            "risk_score": f"{z['risk_score']}%",
            "risk_level": z["risk_level"],
            "color": col,
            "color_dark": col_dark,
            "radius": radius
        })

    df_map = pd.DataFrame(map_rows)

    # 3D Extruded Column Layer + Scatter Glow Layer
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=9000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_color="color_dark",
        get_radius="radius",
        pickable=True,
        opacity=0.7,
        stroked=True,
        filled=False,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255, 200]
    )

    view_state = pdk.ViewState(
        latitude=25.8,
        longitude=91.4,
        zoom=6.8,
        pitch=48,
        bearing=15
    )

    deck = pdk.Deck(
        layers=[column_layer, scatter_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={
            "html": "<div style='padding: 6px; font-family: sans-serif;'>"
                    "<strong style='font-size: 1.1rem; color: #38bdf8;'>{name}</strong> ({region})<br/>"
                    "<span style='font-size: 0.85rem;'>Risk Status: <strong>{risk_level} ({risk_score})</strong></span><br/>"
                    "<span style='font-size: 0.85rem;'>24h Rainfall: <strong>{rain24}</strong></span><br/>"
                    "<span style='font-size: 0.85rem;'>Soil Saturation: <strong>{moist}</strong></span><br/>"
                    "<span style='font-size: 0.85rem;'>Slope Angle: <strong>{slope}</strong></span>"
                    "</div>",
            "style": {"backgroundColor": "#0f172a", "color": "white", "borderRadius": "10px", "border": "1px solid #1e293b"}
        }
    )

    st.pydeck_chart(deck, use_container_width=True)

# ----------------- VIEW 2: ZONE TELEMETRY -----------------
elif "Zone Telemetry" in selected_view:
    st.markdown("### 📊 **Corridor Geological & Meteorological Telemetry**")
    st.caption("Live field sensors monitoring slope inclination, rainfall accumulation, and shear strength proxies across the North Eastern Region.")

    cols = st.columns(len(zone_data))
    for i, z in enumerate(zone_data):
        with cols[i]:
            card_class = "glass-card-high" if z["risk_level"] == "High" else "glass-card"
            pill_class = "pill-danger" if z["risk_level"] == "High" else ("pill-med" if z["risk_level"] == "Medium" else "pill-safe")
            
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <strong style="font-size: 0.95rem; color: #f8fafc;">{z['zone_name']}</strong><br>
                        <span style="font-size: 0.75rem; color: #94a3b8;">📍 {z['region']}</span>
                    </div>
                    <span class="status-pill {pill_class}">{z['risk_level']}</span>
                </div>
                <div style="margin: 10px 0 4px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                        <span style="color: #94a3b8;">Risk Index</span>
                        <strong style="color: #f8fafc;">{z['risk_score']}%</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Native Progress Bar
            st.progress(min(1.0, z["risk_score"] / 100.0))

            # Telemetry Metrics
            st.caption(f"⛰️ Slope: **{z['slope_angle']}°** | Past Events: **{z['historical_landslide_count']}**")
            st.caption(f"🌧️ Rain (1h/24h/72h): **{z['rainfall_1h']} / {z['rainfall_24h']} / {z['rainfall_72h']} mm**")
            st.caption(f"💧 Soil Moisture: **{z['soil_moisture']}%**")

            with st.expander("Geological Drivers", expanded=False):
                for d in z["risk_drivers"]:
                    st.write(f"• {d}")

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Comparative Telemetry Chart
    st.markdown("#### **Comparative Rainfall & Pore Saturation Analysis**")
    comp_df = pd.DataFrame([
        {
            "Corridor": z["zone_name"].split(" ")[0] + " " + z["zone_name"].split(" ")[1],
            "24h Precipitation (mm)": z["rainfall_24h"],
            "72h Saturation (mm)": z["rainfall_72h"],
            "Soil Moisture (%)": z["soil_moisture"]
        }
        for z in zone_data
    ]).set_index("Corridor")

    st.bar_chart(comp_df, height=320)

# ----------------- VIEW 3: SMART REROUTE ENGINE -----------------
elif "Smart Reroute Engine" in selected_view:
    st.markdown("### 🚧 **Dynamic Detour & Mountain Transit Bypass Engine**")
    st.caption("Predefined tactical alternate routes diverting commercial and civilian transit away from landslide-prone gorges and vulnerable rockfall faces.")

    col_sel, col_info = st.columns([1, 2])

    with col_sel:
        st.markdown("#### **Select Monitored Corridor:**")
        selected_corridor_name = st.radio(
            "Corridors",
            options=[z["zone_name"] for z in zones],
            index=0,
            label_visibility="collapsed"
        )
        selected_zone = next(z for z in zone_data if z["zone_name"] == selected_corridor_name)
        route = selected_zone["alternate_route"]

    with col_info:
        r_class = "glass-card-high" if selected_zone["risk_level"] == "High" else "glass-card"
        st.markdown(f"""
        <div class="{r_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; color: #f8fafc;">{selected_zone['zone_name']}</h3>
                <span class="status-pill {'pill-danger' if selected_zone['risk_level']=='High' else 'pill-safe'}">
                    STATUS: {selected_zone['risk_level']} ({selected_zone['risk_score']}%)
                </span>
            </div>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 8px 0 14px 0;">
                {route.get('hazard_avoidance', 'Hazard avoidance protocol active')}
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid #ef4444;">
                    <span style="font-size: 0.72rem; color: #94a3b8;">PRIMARY AT-RISK HIGHWAY</span><br>
                    <strong style="color: #fda4af;">{route.get('primary_route', 'Primary corridor')}</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border-left: 3px solid #10b981;">
                    <span style="font-size: 0.72rem; color: #94a3b8;">RECOMMENDED SAFE BYPASS</span><br>
                    <strong style="color: #86efac;">{route.get('alternate_route_name', 'Bypass Route')}</strong>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                    <span style="font-size: 0.72rem; color: #94a3b8;">ADDITIONAL DISTANCE</span><br>
                    <strong style="color: #e2e8f0;">+{route.get('detour_additional_km', 25)} km</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                    <span style="font-size: 0.72rem; color: #94a3b8;">ESTIMATED EXTRA TRAVEL TIME</span><br>
                    <strong style="color: #e2e8f0;">{route.get('estimated_additional_time', '1 hr')}</strong>
                </div>
            </div>
            <div style="margin-top: 14px;">
                <a href="{route.get('google_maps_url', 'https://maps.google.com')}" target="_blank" style="
                    display: inline-block;
                    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: 700;
                    text-decoration: none;
                    font-size: 0.9rem;
                    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
                ">🗺️ Open Safe Alternate Route in Google Maps ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### **Step-by-Step Waypoint Checkpoints:**")
        checkpoints = route.get("waypoint_checkpoints", [])
        for idx, cp in enumerate(checkpoints, 1):
            st.markdown(f"**Step {idx}:** 📍 {cp}")

# ----------------- VIEW 4: SMS ALERT NETWORK -----------------
elif "SMS Alert Network" in selected_view:
    st.markdown("### 📱 **Disaster Management Broadcast & SMS Audit Feed**")
    st.caption("Automated high-priority emergency dispatches sent to state disaster authorities and traffic control rooms via Twilio / Fast2SMS API (FR-5 & FR-6).")

    col_audit, col_subs = st.columns([2, 1])

    with col_audit:
        st.markdown("#### **Live Dispatch Audit Trail:**")
        if alerts:
            formatted_alerts = []
            for a in alerts:
                formatted_alerts.append({
                    "Timestamp (UTC)": a["timestamp"][:19].replace("T", " "),
                    "Zone": a["zone_name"],
                    "Risk": f"{a['risk_score']}%",
                    "Recipient": f"{a['subscriber_name']} ({a['subscriber_phone']})",
                    "Status": a["status"],
                    "Dispatched Content": a["message_content"]
                })
            df_alerts = pd.DataFrame(formatted_alerts)
            st.dataframe(
                df_alerts,
                column_config={
                    "Dispatched Content": st.column_config.TextColumn("Message Content", width="large"),
                    "Status": st.column_config.TextColumn("Status", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Zero emergency alerts logged. All zones are operating within safe stability margins.")

    with col_subs:
        st.markdown("#### **Emergency Contact Directory:**")
        for sub in subscribers:
            st.markdown(f"""
            <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                <strong style="color: #38bdf8; font-size: 0.88rem;">{sub['name']}</strong><br>
                <span style="color: #94a3b8; font-size: 0.78rem;">Role: {sub['role']}</span><br>
                <code style="font-size: 0.8rem; color: #e2e8f0;">📞 {sub['phone_number']}</code>
            </div>
            """, unsafe_allow_html=True)

# ----------------- VIEW 5: AI WHAT-IF SIMULATOR -----------------
elif "AI What-If Simulator" in selected_view:
    st.markdown("### 🧠 **Geotechnical AI Model & Interactive 'What-If' Storm Lab**")
    st.caption("Test hypothetical monsoon storms and examine how physical predictors interact according to Geological Survey of India (GSI) thresholds.")

    col_sim_ctrl, col_sim_res = st.columns([1, 1])

    with col_sim_ctrl:
        st.markdown("#### **Simulate Weather & Terrain Conditions:**")
        sim_zone_name = st.selectbox("Target Mountain Corridor:", [z["zone_name"] for z in zones], index=0)
        sim_zone = next(z for z in zones if z["zone_name"] == sim_zone_name)

        sim_rain24 = st.slider("24h Cumulative Precipitation (mm):", 0.0, 300.0, 45.0, 5.0)
        sim_rain72 = st.slider("72h Antecedent Saturation (mm):", 0.0, 500.0, sim_rain24 * 1.8, 10.0)
        sim_rain1h = st.slider("1h Peak Burst Intensity (mm/hr):", 0.0, 80.0, min(sim_rain24 * 0.3, 40.0), 2.0)
        sim_moist = st.slider("Soil Moisture Saturation Proxy (%):", 15.0, 95.0, min(85.0, 30.0 + sim_rain72 * 0.1), 1.0)
        sim_slope = st.slider("Slope Angle (°):", 15.0, 55.0, float(sim_zone["slope_angle"]), 0.5)

    with col_sim_res:
        st.markdown("#### **Real-Time ML Risk Assessment:**")
        predictor = get_predictor()
        sim_pred = predictor.predict({
            "rainfall_1h": sim_rain1h,
            "rainfall_24h": sim_rain24,
            "rainfall_72h": sim_rain72,
            "slope_angle": sim_slope,
            "soil_moisture_proxy": sim_moist,
            "historical_landslide_count": sim_zone["historical_landslide_count"]
        })

        sim_score = sim_pred["risk_score"]
        sim_level = sim_pred["risk_level"]
        card_theme = "glass-card-high" if sim_level == "High" else "glass-card"
        badge_theme = "pill-danger" if sim_level == "High" else ("pill-med" if sim_level == "Medium" else "pill-safe")

        st.markdown(f"""
        <div class="{card_theme}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">PREDICTED RISK PROBABILITY</span>
                    <h2 style="margin: 0; font-size: 2.4rem; font-weight: 800; color: #f8fafc;">{sim_score}%</h2>
                </div>
                <span class="status-pill {badge_theme}" style="font-size: 0.95rem; padding: 8px 16px;">
                    {sim_level.upper()} RISK
                </span>
            </div>
            <div style="margin-top: 14px;">
                <strong style="color: #cbd5e1; font-size: 0.85rem;">Dominant Physical Drivers:</strong>
                <ul style="margin: 6px 0 0 0; padding-left: 20px; color: #94a3b8; font-size: 0.85rem;">
                    {"".join([f"<li>{d}</li>" for d in sim_pred['risk_drivers']])}
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

        # Explainability feature breakdown
        meta_file = os.path.join(PROJECT_DIR, "model", "model_meta.json")
        if os.path.exists(meta_file):
            with open(meta_file, "r") as f:
                meta = json.load(f)
            fi = meta.get("feature_importances", {})
            st.markdown("#### **Random Forest Feature Importance Weights:**")
            fi_df = pd.DataFrame([
                {"Predictor": k.replace("_", " ").title(), "Weight (%)": v * 100}
                for k, v in fi.items()
            ]).sort_values("Weight (%)", ascending=True)
            st.bar_chart(fi_df.set_index("Predictor"), height=240)
