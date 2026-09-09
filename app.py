"""
Password Strength Analyzer — Flask Web Application
----------------------------------------------------------------
Routes:
    GET  /             Renders the analyzer UI.
    POST /api/check    JSON API: {"password": "..."} -> strength report.

Run (development):
    pip install -r requirements.txt
    python app.py
    -> open http://127.0.0.1:5000

Run (production-style, no debugger, no auto-reload):
    pip install -r requirements.txt gunicorn
    gunicorn app:app
"""

import os

from flask import Flask, jsonify, render_template, request

from checker import CHECK_LABELS, IDEAL_LENGTH, MIN_LENGTH, analyze_password

# Hard ceiling on accepted password length. Checked both here (so Flask
# rejects an oversized request body before it is ever fully parsed) and
# again inside the route (so the limit is enforced on the value itself,
# not just the raw request size).
MAX_PASSWORD_LENGTH = 256

app = Flask(__name__)

# Reject any request body larger than 16 KB outright. A password field has
# no legitimate reason to be anywhere near this size, so this stops an
# oversized payload from ever reaching Flask's JSON parser.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.route("/")
def index():
    return render_template("index.html", min_length=MIN_LENGTH, ideal_length=IDEAL_LENGTH)


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not isinstance(password, str):
        return jsonify({"error": "Field 'password' must be a string."}), 400

    # Guard against absurdly long input before it ever reaches the
    # analysis engine or gets echoed back in a response.
    if len(password) > MAX_PASSWORD_LENGTH:
        return jsonify(
            {"error": f"Password exceeds maximum accepted length ({MAX_PASSWORD_LENGTH})."}
        ), 400

    result = analyze_password(password)
    payload = result.to_dict()
    payload["labels"] = CHECK_LABELS

    # The plaintext password is intentionally never included in the
    # response or logged — only the derived analysis is returned.
    return jsonify(payload)


@app.errorhandler(413)
def request_too_large(_err):
    return jsonify({"error": "Request body too large."}), 413


@app.errorhandler(404)
def not_found(_err):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return render_template("index.html", min_length=MIN_LENGTH, ideal_length=IDEAL_LENGTH), 404


if __name__ == "__main__":
    # Debug mode (auto-reload + interactive debugger) is OFF unless you
    # explicitly opt in. Werkzeug's interactive debugger can allow
    # arbitrary code execution if it is ever reachable from the network,
    # so it must never be enabled in a real deployment.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug_mode, port=port)
