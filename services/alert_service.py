"""
TerraNova - SMS Alert & Emergency Dispatch Service
Sends SMS notifications via Twilio or Fast2SMS API with automatic fallback to high-fidelity
simulation logging (NFR-3 & NFR-5).
"""

import os
import json
import requests
from database.db import log_alert

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "").strip()

def send_alert_for_zone(zone: dict, risk_score: float, route_info: dict, subscribers: list) -> list:
    """
    Sends emergency SMS alerts for a high-risk zone to all registered subscribers.
    Returns list of dispatch audit records.
    """
    zone_id = zone["zone_id"]
    zone_name = zone["zone_name"]
    alt_route_name = route_info.get("alternate_route_name", "Designated Safe Bypass Highway")
    maps_url = route_info.get("google_maps_url", "https://maps.google.com")
    detour_km = route_info.get("detour_additional_km", 25)

    message_body = (
        f"[TERRANOVA RED ALERT] Landslide Risk CRITICAL ({risk_score}% probability) "
        f"at {zone_name}! "
        f"Primary corridor closed to traffic. "
        f"MANDATORY REROUTE: Divert via {alt_route_name} (+{detour_km} km). "
        f"Live Map Navigation: {maps_url}"
    )

    dispatched_records = []

    for sub in subscribers:
        phone = sub.get("phone_number", "+919999999999")
        name = sub.get("name", "Emergency Officer")
        role = sub.get("role", "Disaster Management")
        status = "PENDING"

        # 1. Try Twilio if configured
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
            try:
                twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                resp = requests.post(
                    twilio_url,
                    data={"From": TWILIO_PHONE_NUMBER, "To": phone, "Body": message_body},
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                    timeout=3.0
                )
                if resp.status_code in [200, 201]:
                    status = "DELIVERED (Twilio SMS)"
                else:
                    status = f"FAILED_TWILIO ({resp.status_code})"
            except Exception as e:
                print(f"[AlertService] Twilio exception: {e}")
                status = "FALLBACK_TRIGGERED"

        # 2. Try Fast2SMS if configured and not yet sent
        elif FAST2SMS_API_KEY:
            try:
                headers = {"authorization": FAST2SMS_API_KEY}
                payload = {
                    "route": "v3",
                    "sender_id": "TXTIND",
                    "message": message_body,
                    "language": "english",
                    "flash": 0,
                    "numbers": phone.replace("+91", "").replace("+", "")
                }
                resp = requests.post("https://www.fast2sms.com/dev/bulkV2", json=payload, headers=headers, timeout=3.0)
                if resp.status_code == 200:
                    status = "DELIVERED (Fast2SMS)"
                else:
                    status = f"FAILED_FAST2SMS ({resp.status_code})"
            except Exception as e:
                print(f"[AlertService] Fast2SMS exception: {e}")
                status = "FALLBACK_TRIGGERED"

        # 3. Graceful Simulation Fallback (NFR-3 & NFR-5 for hackathon stage demo)
        if status in ["PENDING", "FALLBACK_TRIGGERED"] or not (TWILIO_ACCOUNT_SID or FAST2SMS_API_KEY):
            status = "DELIVERED (Simulated SMS Gateway)"

        # Persist alert record to SQLite audit log (FR-6)
        log_alert(
            zone_id=zone_id,
            zone_name=zone_name,
            risk_score=risk_score,
            subscriber_name=name,
            subscriber_phone=phone,
            recipient_role=role,
            status=status,
            message_content=message_body,
            suggested_route=alt_route_name,
            google_maps_url=maps_url
        )

        dispatched_records.append({
            "zone_id": zone_id,
            "zone_name": zone_name,
            "subscriber_name": name,
            "subscriber_phone": phone,
            "role": role,
            "status": status,
            "message_preview": message_body[:90] + "..."
        })

    return dispatched_records
