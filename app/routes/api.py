from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request

from app import db
from app.routes.auth import requires_admin_access, requires_basic_auth, validate_webhook_token
from app.services.tracking import STATUS_CODES, add_event, serialize_shipment_payload, status_label

bp = Blueprint("api", __name__)


def _require_json() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="Payload JSON invalide ou manquant")
    return payload


def _parse_event_time(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    return value


@bp.get("/status-codes")
def status_codes():
    return jsonify(STATUS_CODES)


@bp.get("/track/<tracking_number>")
def get_track(tracking_number: str):
    payload = serialize_shipment_payload(tracking_number)
    return jsonify(payload)


@bp.post("/track")
@requires_admin_access
def create_track():
    payload = _require_json()
    required = ["date", "tracking_number", "client", "poids", "colis", "envoi", "frais"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        abort(400, description=f"Champs manquants: {', '.join(missing)}")

    if db.get_shipment_by_tracking(payload["tracking_number"]):
        abort(400, description="Numéro de suivi déjà existant")

    try:
        payload["poids"] = float(payload["poids"])
        payload["colis"] = int(float(payload["colis"]))
        payload["frais"] = float(payload["frais"])
    except (TypeError, ValueError):
        abort(400, description="Poids, Colis et Frais doivent être numériques")

    shipment = db.create_shipment(payload)
    return (
        jsonify(
            {
                "message": "Colis créé",
                "tracking_number": shipment["tracking_number"],
            }
        ),
        201,
    )


@bp.post("/events")
@requires_admin_access
def create_event():
    payload = _require_json()
    required = ["tracking_number", "code"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        abort(400, description=f"Champs manquants: {', '.join(missing)}")

    if payload["code"] not in {item["code"] for item in STATUS_CODES}:
        abort(400, description="Code statut invalide")

    add_event(
        payload["tracking_number"],
        {
            "code": payload["code"],
            "label": payload.get("label") or status_label(payload["code"]),
            "location": payload.get("location"),
            "details": payload.get("details"),
            "event_time": _parse_event_time(payload.get("ts")),
        },
    )

    return jsonify({"message": "Événement ajouté"}), 201


@bp.post("/webhook/status")
def webhook_status():
    if not validate_webhook_token():
        abort(401, description="Token webhook invalide")

    payload = _require_json()
    required = ["ref", "status"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        abort(400, description=f"Champs manquants: {', '.join(missing)}")

    mapped = {
        "tracking_number": payload["ref"],
        "code": payload["status"],
        "label": status_label(payload["status"]),
        "location": payload.get("city"),
        "details": payload.get("info"),
        "event_time": _parse_event_time(payload.get("when")),
    }

    if mapped["code"] not in {item["code"] for item in STATUS_CODES}:
        abort(400, description="Statut transporteur non supporté")

    add_event(mapped["tracking_number"], mapped)
    return jsonify({"message": "Webhook traité", "tracking_number": mapped["tracking_number"]})
