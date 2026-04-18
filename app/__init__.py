import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from .db import close_db


class JsonFormatter(logging.Formatter):
    """Format JSON lisible par Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.now(timezone.utc).isoformat(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging(app: Flask) -> None:
    if app.config.get("GOOGLE_CLOUD_PROJECT"):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )


def _is_api_request() -> bool:
    accepts = request.headers.get("Accept", "")
    return request.path.startswith("/api") or "application/json" in accepts


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-insecure-secret"),
        DATABASE=os.getenv("DATABASE", os.path.join(app.instance_path, "app.db")),
        ADMIN_USER=os.getenv("APP_ADMIN_USER", "admin"),
        ADMIN_PASSWORD=os.getenv("APP_ADMIN_PASSWORD", "admin123"),
        CONTACT_EMAIL=os.getenv("APP_CONTACT_EMAIL", "contact@osl.local"),
        WEBHOOK_TOKEN=os.getenv("WEBHOOK_TOKEN", "change-me"),
        GOOGLE_CLOUD_PROJECT=os.getenv("GOOGLE_CLOUD_PROJECT"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    _configure_logging(app)

    from . import db

    db.init_app(app)

    from .routes.api import bp as api_bp
    from .routes.legacy import bp as legacy_bp
    from .routes.web import bp as web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(legacy_bp)

    from .legacy_db import get_legacy_db

    with app.app_context():
        db.init_db()
        get_legacy_db().ensure_default_users()

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.context_processor
    def inject_contact_email():
        contact_email = app.config.get("CONTACT_EMAIL", "contact@osl.local")
        return {
            "contact_email": contact_email,
            "contact_mailto": f"mailto:{contact_email}",
        }

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'"
        return response

    @app.teardown_appcontext
    def teardown_db(exception):
        close_db(exception)

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_errors(error):
        code = getattr(error, "code", 500)
        message = getattr(error, "description", "Une erreur est survenue")

        if _is_api_request():
            return jsonify({"error": {"code": code, "message": message}}), code

        return (
            f"<h1>Erreur {code}</h1><p>{message}</p><p><a href='/'>Retour accueil</a></p>",
            code,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    return app
