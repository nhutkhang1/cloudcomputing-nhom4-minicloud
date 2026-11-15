from flask import Flask, jsonify, request, render_template
import json, os, time

import pymysql
import requests
from jose import jwt
from jose.exceptions import JWTError

# Fetch Keycloak public keys (JWKS) through the internal cloud-net address.
# Tokens can be obtained through localhost, a LAN IP, or a public IP, so the
# issuer host varies. Validate the signature, realm, and audience.
REALM        = os.getenv("OIDC_REALM", "realm_523H0145")
INTERNAL_URL = os.getenv("OIDC_INTERNAL_URL", f"http://authentication-identity-server:8080/auth/realms/{REALM}")
AUDIENCE     = os.getenv("OIDC_AUDIENCE", "myapp")
JWKS_URL     = f"{INTERNAL_URL}/protocol/openid-connect/certs"

DB = dict(
    host=os.getenv("DB_HOST", "relational-database-server"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "appuser"),
    password=os.getenv("DB_PASSWORD", "apppass"),
    database=os.getenv("DB_NAME", "studentdb"),
    charset="utf8mb4",
    connect_timeout=5,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_JWKS = None; _TS = 0
def get_jwks(force=False):
    global _JWKS, _TS
    now = time.time()
    if force or not _JWKS or now - _TS > 600:
        _JWKS = requests.get(JWKS_URL, timeout=5).json()
        _TS = now
    return _JWKS

def decode_token(token):
    opts = {"verify_iss": False}
    try:
        payload = jwt.decode(token, get_jwks(), algorithms=["RS256"], audience=AUDIENCE, options=opts)
    except JWTError:
        # Reload JWKS and retry once if Keycloak has rotated its signing keys.
        payload = jwt.decode(token, get_jwks(force=True), algorithms=["RS256"], audience=AUDIENCE, options=opts)
    if not str(payload.get("iss", "")).endswith(f"/realms/{REALM}"):
        raise JWTError(f"Invalid issuer: token does not belong to realm {REALM}")
    return payload

def wants_html():
    fmt = request.args.get("format")
    if fmt:
        return fmt == "html"
    return request.accept_mimetypes.best_match(["application/json", "text/html"]) == "text/html"

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False

@app.get("/hello")
def hello(): return jsonify(message="Hello from App Server!")

@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return jsonify(error="Missing Bearer token"), 401
    token = auth.split(" ",1)[1]
    try:
        payload = decode_token(token)
        return jsonify(message="Secure resource OK", preferred_username=payload.get("preferred_username"))
    except Exception as e:
        return jsonify(error=str(e)), 401

@app.get("/student")
def student():
    with open(os.path.join(BASE_DIR, "students.json"), encoding="utf-8") as f:
        data = json.load(f)
    if wants_html():
        return render_template("table.html", title="Student list (JSON)",
                               source="students.json", columns=["id", "name", "major", "gpa"], rows=data)
    return jsonify(data)

@app.get("/students-db")
def students_db():
    try:
        conn = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **DB)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, student_id, fullname, dob, major FROM students ORDER BY id")
                rows = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        return jsonify(error=f"Database error: {e}"), 503
    for r in rows:
        if r.get("dob") is not None:
            r["dob"] = r["dob"].isoformat()
    if wants_html():
        return render_template("table.html", title="Student list (MariaDB)",
                               source="studentdb.students", columns=["id", "student_id", "fullname", "dob", "major"], rows=rows)
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
