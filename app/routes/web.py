import csv
from datetime import datetime
from io import StringIO

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for

from app import db
from app.routes.auth import requires_admin_access
from app.services.tracking import get_shipment_by_tracking

bp = Blueprint("web", __name__)


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
