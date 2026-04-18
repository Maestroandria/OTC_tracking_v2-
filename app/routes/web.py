from flask import Blueprint, flash, redirect, render_template, request, session, url_for

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
    shipments = db.list_shipments(search=search)
    return render_template(
        "front_admin/admin.html",
        shipments=shipments,
        search=search,
    )
