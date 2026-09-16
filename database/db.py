"""
TerraNova - SQLite Database Persistence Layer
Stores real-time & simulated weather readings, computed risk scores, and alert dispatch audit logs.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DB_DIR)
DB_PATH = os.path.join(DB_DIR, "terranova.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zone_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        rainfall_1h REAL,
        rainfall_24h REAL,
        rainfall_72h REAL,
        temperature REAL,
        humidity REAL,
        soil_moisture_proxy REAL,
        is_simulated INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zone_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        risk_score REAL NOT NULL,
        risk_level TEXT NOT NULL,
        risk_drivers TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        zone_id TEXT NOT NULL,
        zone_name TEXT NOT NULL,
        risk_score REAL NOT NULL,
        subscriber_name TEXT,
        subscriber_phone TEXT NOT NULL,
        recipient_role TEXT,
        status TEXT NOT NULL,
        message_content TEXT NOT NULL,
        suggested_route TEXT,
        google_maps_url TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_reading(zone_id, rainfall_1h, rainfall_24h, rainfall_72h, temperature, humidity, soil_moisture_proxy, is_simulated=0):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO zone_readings 
        (zone_id, timestamp, rainfall_1h, rainfall_24h, rainfall_72h, temperature, humidity, soil_moisture_proxy, is_simulated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (zone_id, ts, rainfall_1h, rainfall_24h, rainfall_72h, temperature, humidity, soil_moisture_proxy, is_simulated))
    conn.commit()
    conn.close()

def log_risk_assessment(zone_id, risk_score, risk_level, risk_drivers):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO risk_assessments (zone_id, timestamp, risk_score, risk_level, risk_drivers)
        VALUES (?, ?, ?, ?, ?)
    """, (zone_id, ts, risk_score, risk_level, json.dumps(risk_drivers)))
    conn.commit()
    conn.close()

def log_alert(zone_id, zone_name, risk_score, subscriber_name, subscriber_phone, recipient_role, status, message_content, suggested_route, google_maps_url):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO alerts_log 
        (timestamp, zone_id, zone_name, risk_score, subscriber_name, subscriber_phone, recipient_role, status, message_content, suggested_route, google_maps_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, zone_id, zone_name, risk_score, subscriber_name, subscriber_phone, recipient_role, status, message_content, suggested_route, google_maps_url))
    conn.commit()
    conn.close()

def get_latest_zone_readings():
    """Returns the most recent reading for each zone."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.* FROM zone_readings r
        INNER JOIN (
            SELECT zone_id, MAX(id) as max_id
            FROM zone_readings
            GROUP BY zone_id
        ) latest ON r.id = latest.max_id
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_latest_risk_assessments():
    """Returns the most recent risk score for each zone."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.* FROM risk_assessments a
        INNER JOIN (
            SELECT zone_id, MAX(id) as max_id
            FROM risk_assessments
            GROUP BY zone_id
        ) latest ON a.id = latest.max_id
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_all_alerts(limit=50):
    """Returns the recent alert log entries sorted by latest timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def seed_initial_state():
    """Seeds baseline data if database is fresh."""
    init_db()
    existing = get_latest_zone_readings()
    if existing:
        return  # already seeded

    zones_path = os.path.join(PROJECT_DIR, "data", "zones.json")
    if not os.path.exists(zones_path):
        return

    with open(zones_path, "r") as f:
        zones = json.load(f)

    # Initial stable baseline conditions
    baselines = {
        "NER_ZONE_01": {"r1": 2.4, "r24": 18.0, "r72": 45.0, "temp": 19.5, "hum": 72.0, "moist": 36.0, "score": 14.5, "level": "Low"},
        "NER_ZONE_02": {"r1": 5.1, "r24": 38.0, "r72": 95.0, "temp": 16.0, "hum": 84.0, "moist": 48.0, "score": 38.2, "level": "Low"},
        "NER_ZONE_03": {"r1": 1.8, "r24": 12.0, "r72": 32.0, "temp": 24.5, "hum": 68.0, "moist": 34.0, "score": 11.2, "level": "Low"},
        "NER_ZONE_04": {"r1": 3.0, "r24": 25.0, "r72": 60.0, "temp": 21.0, "hum": 75.0, "moist": 39.0, "score": 22.8, "level": "Low"},
        "NER_ZONE_05": {"r1": 0.5, "r24": 8.0, "r72": 22.0, "temp": 8.5, "hum": 60.0, "moist": 26.0, "score": 9.4, "level": "Low"}
    }

    for z in zones:
        zid = z["zone_id"]
        b = baselines.get(zid, {"r1": 2.0, "r24": 15.0, "r72": 40.0, "temp": 20.0, "hum": 70.0, "moist": 35.0, "score": 15.0, "level": "Low"})
        log_reading(zid, b["r1"], b["r24"], b["r72"], b["temp"], b["hum"], b["moist"], is_simulated=0)
        log_risk_assessment(zid, b["score"], b["level"], ["Baseline normal seasonal conditions"])

if __name__ == "__main__":
    init_db()
    seed_initial_state()
    print("Database initialized and baseline data seeded successfully.")
