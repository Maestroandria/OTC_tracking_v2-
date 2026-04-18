from datetime import datetime, timezone

from app import create_app
from app import db
from app.legacy_db import get_legacy_db
from app.services.tracking import add_event


def main():
    app = create_app()
    with app.app_context():
        db.init_db()
        legacy_db = get_legacy_db()
        legacy_db.ensure_default_users()

        tracking_number = "OSL-2026-0001"
        existing = db.get_shipment_by_tracking(tracking_number)
        if not existing:
            db.create_shipment(
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "tracking_number": tracking_number,
                    "client": "ACME Madagascar",
                    "poids": 12.5,
                    "colis": 3,
                    "envoi": "Express",
                    "frais": 185000,
                    "status_current_code": "CREATED",
                    "status_current_label": "Créé",
                }
            )
        elif not existing["date"] and not existing["client"]:
            connection = db.get_db()
            connection.execute(
                """
                UPDATE colis
                SET date = ?,
                    client = ?,
                    poids = ?,
                    colis = ?,
                    envoi = ?,
                    frais = ?,
                    updated_at = ?
                WHERE tracking_number = ?
                """,
                (
                    datetime.now().strftime("%Y-%m-%d"),
                    "ACME Madagascar",
                    12.5,
                    3,
                    "Express",
                    185000,
                    datetime.now(timezone.utc).isoformat(),
                    tracking_number,
                ),
            )
            connection.commit()

        # Seed d'événements de démonstration.
        seed_events = [
            {
                "code": "PICKED_UP",
                "label": "Pris en charge",
                "location": "Antananarivo",
                "details": "Colis récupéré",
                "event_time": "2026-03-02T09:00:00Z",
            },
            {
                "code": "IN_TRANSIT",
                "label": "En transit",
                "location": "Nairobi Hub",
                "details": "Départ du hub",
                "event_time": "2026-03-02T18:12:00Z",
            },
            {
                "code": "AT_HUB",
                "label": "Arrivé au hub",
                "location": "Antananarivo Hub",
                "details": "Préparation tournée finale",
                "event_time": datetime.now(timezone.utc).isoformat(),
            },
        ]

        current_events = db.list_events(db.get_shipment_by_tracking(tracking_number)["id"])
        if not current_events:
            for event in seed_events:
                add_event(tracking_number, event)

        print("Base SQLite unique (ERP + tracking) initialisée avec données de démonstration.")


if __name__ == "__main__":
    main()
