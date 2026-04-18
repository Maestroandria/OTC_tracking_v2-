import secrets
from functools import wraps

from flask import Response, current_app, redirect, request, session, url_for


def _unauthorized_response() -> Response:
    return Response(
        "Authentification requise",
        401,
        {"WWW-Authenticate": 'Basic realm="Admin Tracking"'},
    )


def requires_basic_auth(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return _unauthorized_response()

        expected_user = current_app.config.get("ADMIN_USER")
        expected_password = current_app.config.get("ADMIN_PASSWORD")

        is_valid = secrets.compare_digest(auth.username, expected_user) and secrets.compare_digest(
            auth.password, expected_password
        )
        if not is_valid:
            return _unauthorized_response()

        return view_func(*args, **kwargs)

    return wrapped


def requires_admin_access(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        # Vérification session (système d'auth principal)
        if session.get("role") == "admin":
            return view_func(*args, **kwargs)

        # Fallback Basic Auth (accès API / scripts)
        auth = request.authorization
        if auth and auth.username and auth.password:
            expected_user = current_app.config.get("ADMIN_USER")
            expected_password = current_app.config.get("ADMIN_PASSWORD")
            is_valid = secrets.compare_digest(auth.username, expected_user) and secrets.compare_digest(
                auth.password, expected_password
            )
            if is_valid:
                return view_func(*args, **kwargs)

        # Pas authentifié → redirection vers login (pas de popup navigateur)
        return redirect(url_for("legacy.login"))

    return wrapped


def validate_webhook_token() -> bool:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False

    token = auth.split(" ", 1)[1].strip()
    expected_token = current_app.config.get("WEBHOOK_TOKEN", "")
    return secrets.compare_digest(token, expected_token)
