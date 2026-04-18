from flask import abort

from app import db


STATUS_CODES = [
    {"code": "CREATED", "label": "Créé"},
    {"code": "PICKED_UP", "label": "Pris en charge"},
    {"code": "IN_TRANSIT", "label": "En transit"},
    {"code": "AT_HUB", "label": "Arrivé au hub"},
    {"code": "OUT_FOR_DELIVERY", "label": "En cours de livraison"},
    {"code": "DELIVERED", "label": "Livré"},
    {"code": "EXCEPTION", "label": "Incident"},
    {"code": "RETURNED", "label": "Retourné"},
    {"code": "HELD_CUSTOMS", "label": "Bloqué en douane"},
]


def status_label(code: str) -> str:
    for item in STATUS_CODES:
        if item["code"] == code:
            return item["label"]
    return code.replace("_", " ").title()


def get_shipment_by_tracking(tracking_number: str):
    shipment = db.get_shipment_by_tracking(tracking_number)
    if not shipment:
        abort(404, description="Colis introuvable")
    return shipment


def list_events(tracking_number: str):
    shipment = get_shipment_by_tracking(tracking_number)
    return db.list_events(shipment["id"])


def add_event(tracking_number: str, payload: dict):
    shipment = get_shipment_by_tracking(tracking_number)
    event_payload = {
        "code": payload["code"],
        "label": payload.get("label") or status_label(payload["code"]),
        "location": payload.get("location"),
        "details": payload.get("details"),
        "event_time": payload["event_time"],
    }
    db.create_event(shipment["id"], event_payload)
    update_current_status(shipment["id"], event_payload)
    return shipment


def update_current_status(shipment_id: int, event_payload: dict):
    db.update_shipment_status(
        shipment_id,
        event_payload["code"],
        event_payload["label"],
        event_payload["event_time"],
    )


def serialize_shipment_payload(tracking_number: str) -> dict:
    shipment = get_shipment_by_tracking(tracking_number)
    events = db.list_events(shipment["id"])

    return {
        "tracking_number": shipment["tracking_number"],
        "status": {
            "code": shipment["status_current_code"],
            "label": shipment["status_current_label"],
            "updated_at": shipment["updated_at"],
        },
        "shipment": {
            "date": shipment["date"],
            "client": shipment["client"],
            "poids": shipment["poids"],
            "colis": shipment["colis"],
            "envoi": shipment["envoi"],
            "frais": shipment["frais"],
        },
        "events": [
            {
                "code": event["code"],
                "label": event["label"],
                "location": event["location"],
                "event_time": event["event_time"],
                "details": event["details"],
            }
            for event in events
        ],
    }
