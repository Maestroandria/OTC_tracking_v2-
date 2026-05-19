import csv
from datetime import datetime, timedelta
from io import StringIO

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, session, url_for

from app import db
from app.routes.auth import is_super_admin_session, requires_admin_access, requires_super_admin_access
from app.services.tracking import get_shipment_by_tracking

bp = Blueprint("web", __name__)


def _to_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    normalized = (
        text.replace(" ", "")
        .replace("Ar", "")
        .replace("MGA", "")
        .replace(",", ".")
    )
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def _parse_date(value) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    iso_candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(tz=None).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(tz=None).replace(tzinfo=None)
            return parsed
        except ValueError:
            continue
    return None


def _get_field(item, key: str, default=None):
    if item is None:
        return default
    if hasattr(item, "get"):
        return item.get(key, default)
    try:
        return item[key]
    except (KeyError, IndexError, TypeError):
        return default


def _shipment_datetime(item) -> datetime | None:
    return (
        _parse_date(_get_field(item, "date"))
        or _parse_date(_get_field(item, "updated_at"))
        or _parse_date(_get_field(item, "created_at"))
    )


def _build_chart_rows(rows: list[dict], value_key: str) -> list[dict]:
    if not rows:
        return []
    max_value = max(float(row.get(value_key, 0.0) or 0.0) for row in rows)
    if max_value <= 0:
        return [{**row, "pct": 0.0} for row in rows]
    return [{**row, "pct": (float(row.get(value_key, 0.0) or 0.0) / max_value) * 100.0} for row in rows]


def _read_positive_int(value, default: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _paginate_rows(rows: list, requested_page: int, page_size: int) -> tuple[list, dict]:
    total_items = len(rows)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = min(max(1, requested_page), total_pages)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_rows = rows[start_idx:end_idx]

    return page_rows, {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "start_item": (start_idx + 1) if total_items else 0,
        "end_item": min(end_idx, total_items),
    }


@bp.get("/")
def index():
    return render_template("front_user/index.html")


@bp.post("/contact")
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not all([name, email, message]):
        flash("Merci de remplir tous les champs du formulaire.", "error")
        return redirect(url_for("web.index") + "#contact")

    flash("Merci, votre message a bien été envoyé. Nous revenons vers vous rapidement.", "success")
    return redirect(url_for("web.index") + "#contact")


@bp.get("/track")
def track_redirect():
    tracking_number = request.args.get("tracking_number", "").strip()
    if not tracking_number:
        return redirect(url_for("web.tracking_page"))
    return redirect(url_for("web.tracking_page", tracking_number=tracking_number))


@bp.route("/tracking", methods=["GET", "POST"])
def tracking_page():
    tracking_number = ""
    if request.method == "POST":
        tracking_number = request.form.get("tracking_number", "").strip()
    else:
        tracking_number = request.args.get("tracking_number", "").strip()

    shipment = None
    events = []
    searched = bool(tracking_number)

    if tracking_number:
        shipment = db.get_shipment_by_tracking(tracking_number)
        if shipment:
            events = db.list_events(shipment["id"])

    return render_template(
        "front_user/tracking.html",
        tracking_number=tracking_number,
        shipment=shipment,
        events=events,
        searched=searched,
    )


@bp.get("/track/<tracking_number>")
def track_page(tracking_number: str):
    return redirect(url_for("web.tracking_page", tracking_number=tracking_number))


@bp.get("/admin")
@requires_admin_access
def admin():
    search = request.args.get("q", "").strip()
    client_filter = request.args.get("client", "").strip()
    status_filter = request.args.get("status", "").strip()
    envoi_filter = request.args.get("envoi", "").strip()

    filters = {
        "q": search,
        "client": client_filter,
        "status": status_filter,
        "envoi": envoi_filter,
    }

    page = request.args.get("page", default=1, type=int) or 1
    page = max(page, 1)
    per_page = 25

    total_shipments = db.count_shipments(filters=filters)
    total_pages = max((total_shipments + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    shipments = db.list_shipments(filters=filters, limit=per_page, offset=offset)

    start_item = offset + 1 if total_shipments > 0 else 0
    end_item = min(offset + len(shipments), total_shipments)
    has_filters = any([search, client_filter, status_filter, envoi_filter])
    active_search_label = search or ("Filtres actifs" if has_filters else "Toutes")

    return render_template(
        "front_admin/admin.html",
        shipments=shipments,
        is_super_admin=is_super_admin_session(),
        search=search,
        client_filter=client_filter,
        status_filter=status_filter,
        envoi_filter=envoi_filter,
        active_search_label=active_search_label,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_shipments=total_shipments,
        start_item=start_item,
        end_item=end_item,
    )


@bp.get("/admin/export")
@requires_admin_access
def admin_export():
    filters = {
        "q": request.args.get("q", "").strip(),
        "client": request.args.get("client", "").strip(),
        "status": request.args.get("status", "").strip(),
        "envoi": request.args.get("envoi", "").strip(),
    }

    rows = db.export_shipments(filters=filters)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "date",
        "tracking_number",
        "client",
        "status",
        "poids",
        "colis",
        "envoi",
        "frais",
        "created_at",
        "updated_at",
    ])

    for row in rows:
        writer.writerow([
            row.get("date") if hasattr(row, "get") else row[0],
            row.get("tracking_number") if hasattr(row, "get") else row[1],
            row.get("client") if hasattr(row, "get") else row[2],
            row.get("status_current_label") if hasattr(row, "get") else row[3],
            row.get("poids") if hasattr(row, "get") else row[4],
            row.get("colis") if hasattr(row, "get") else row[5],
            row.get("envoi") if hasattr(row, "get") else row[6],
            row.get("frais") if hasattr(row, "get") else row[7],
            row.get("created_at") if hasattr(row, "get") else row[8],
            row.get("updated_at") if hasattr(row, "get") else row[9],
        ])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"colis_filtres_{timestamp}.csv"
    csv_content = buffer.getvalue()
    buffer.close()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.get("/admin/super-dashboard")
@requires_super_admin_access
def super_admin_dashboard():
    selected_view = (request.args.get("view") or "dashboard").strip().lower()
    if selected_view not in {"dashboard", "details"}:
        selected_view = "dashboard"

    details_page_size = 20
    tc_page = _read_positive_int(request.args.get("tc_page"), 1)
    st_page = _read_positive_int(request.args.get("st_page"), 1)
    aw_page = _read_positive_int(request.args.get("aw_page"), 1)
    sv_page = _read_positive_int(request.args.get("sv_page"), 1)

    recent_shipments = db.list_shipments(limit=10, offset=0)
    all_shipments = db.export_shipments()
    total_shipments = db.count_shipments()

    try:
        total_weight = 0.0
        total_amount = 0.0

        status_stats: dict[str, dict[str, float | int]] = {}
        client_amounts: dict[str, float] = {}
        client_weight_acc: dict[str, dict[str, float | int]] = {}
        service_amounts: dict[str, float] = {}
        weekly_totals: dict[tuple[int, int], float] = {}

        latest_dt = None
        for item in all_shipments:
            weight = _to_float(_get_field(item, "poids"))
            amount = _to_float(_get_field(item, "frais"))
            total_weight += weight
            total_amount += amount

            status_label = str(_get_field(item, "status_current_label", "Sans statut") or "Sans statut").strip() or "Sans statut"
            status_bucket = status_stats.setdefault(status_label, {"count": 0, "weight": 0.0})
            status_bucket["count"] = int(status_bucket["count"]) + 1
            status_bucket["weight"] = float(status_bucket["weight"]) + weight

            client = str(_get_field(item, "client", "Client non renseigné") or "Client non renseigné").strip() or "Client non renseigné"
            client_amounts[client] = client_amounts.get(client, 0.0) + amount

            client_weight = client_weight_acc.setdefault(client, {"weight": 0.0, "count": 0})
            client_weight["weight"] = float(client_weight["weight"]) + weight
            client_weight["count"] = int(client_weight["count"]) + 1

            service = str(_get_field(item, "envoi", "Service non renseigné") or "Service non renseigné").strip() or "Service non renseigné"
            service_amounts[service] = service_amounts.get(service, 0.0) + amount

            dt = _shipment_datetime(item)
            if dt:
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
                year, week, _ = dt.isocalendar()
                weekly_totals[(int(year), int(week))] = weekly_totals.get((int(year), int(week)), 0.0) + weight

        reference_dt = latest_dt or datetime.now()
        week_start = reference_dt - timedelta(days=reference_dt.weekday())
        week_end = week_start + timedelta(days=7)
        current_week_weight = 0.0

        for item in all_shipments:
            dt = _shipment_datetime(item)
            if dt and week_start <= dt < week_end:
                current_week_weight += _to_float(_get_field(item, "poids"))

        average_weekly_weight = (
            sum(weekly_totals.values()) / len(weekly_totals)
            if weekly_totals
            else 0.0
        )

        top_clients_by_amount = [
            {"client": client, "amount": amount}
            for client, amount in sorted(
                client_amounts.items(),
                key=lambda pair: pair[1],
                reverse=True,
            )
        ]

        status_breakdown = sorted(
            [
                {
                    "label": label,
                    "count": int(values["count"]),
                    "weight": float(values["weight"]),
                }
                for label, values in status_stats.items()
            ],
            key=lambda row: row["count"],
            reverse=True,
        )

        avg_weight_by_client = sorted(
            [
                {
                    "client": client,
                    "avg_weight": (float(values["weight"]) / int(values["count"])) if int(values["count"]) else 0.0,
                    "count": int(values["count"]),
                }
                for client, values in client_weight_acc.items()
            ],
            key=lambda row: row["avg_weight"],
            reverse=True,
        )

        amount_by_service = [
            {"service": service, "amount": amount}
            for service, amount in sorted(
                service_amounts.items(),
                key=lambda pair: pair[1],
                reverse=True,
            )
        ]
    except Exception:
        current_app.logger.exception("Erreur calcul dashboard super admin")
        total_weight = 0.0
        total_amount = 0.0
        current_week_weight = 0.0
        average_weekly_weight = 0.0
        top_clients_by_amount = []
        status_breakdown = []
        avg_weight_by_client = []
        amount_by_service = []

    top_clients_page, top_clients_meta = _paginate_rows(top_clients_by_amount, tc_page, details_page_size)
    status_breakdown_page, status_meta = _paginate_rows(status_breakdown, st_page, details_page_size)
    avg_weight_by_client_page, avg_meta = _paginate_rows(avg_weight_by_client, aw_page, details_page_size)
    amount_by_service_page, service_meta = _paginate_rows(amount_by_service, sv_page, details_page_size)

    status_count_chart = _build_chart_rows(status_breakdown[:10], "count")
    service_amount_chart = _build_chart_rows(
        [
            {"label": row["service"], "amount": row["amount"]}
            for row in amount_by_service[:10]
        ],
        "amount",
    )
    top_clients_amount_chart = _build_chart_rows(
        [
            {"label": row["client"], "amount": row["amount"]}
            for row in top_clients_by_amount[:10]
        ],
        "amount",
    )

    return render_template(
        "front_admin/super_admin_dashboard.html",
        selected_view=selected_view,
        total_shipments=total_shipments,
        total_weight=total_weight,
        total_amount=total_amount,
        current_week_weight=current_week_weight,
        average_weekly_weight=average_weekly_weight,
        recent_shipments=recent_shipments,
        top_clients_by_amount=top_clients_page,
        status_breakdown=status_breakdown_page,
        avg_weight_by_client=avg_weight_by_client_page,
        amount_by_service=amount_by_service_page,
        status_count_chart=status_count_chart,
        service_amount_chart=service_amount_chart,
        top_clients_amount_chart=top_clients_amount_chart,
        tc_page=top_clients_meta["page"],
        tc_total_pages=top_clients_meta["total_pages"],
        tc_total_items=top_clients_meta["total_items"],
        tc_start_item=top_clients_meta["start_item"],
        tc_end_item=top_clients_meta["end_item"],
        st_page=status_meta["page"],
        st_total_pages=status_meta["total_pages"],
        st_total_items=status_meta["total_items"],
        st_start_item=status_meta["start_item"],
        st_end_item=status_meta["end_item"],
        aw_page=avg_meta["page"],
        aw_total_pages=avg_meta["total_pages"],
        aw_total_items=avg_meta["total_items"],
        aw_start_item=avg_meta["start_item"],
        aw_end_item=avg_meta["end_item"],
        sv_page=service_meta["page"],
        sv_total_pages=service_meta["total_pages"],
        sv_total_items=service_meta["total_items"],
        sv_start_item=service_meta["start_item"],
        sv_end_item=service_meta["end_item"],
        details_page_size=details_page_size,
    )
