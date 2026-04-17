import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import threading
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
DATA_FILE = ROOT / "data" / "store.json"
DB_FILE = ROOT / "data" / "app.db"
SESSION_COOKIE = "welcome_session"
SESSION_SECRET = os.environ.get("WELCOME_SESSION_SECRET", secrets.token_hex(32))
ADMIN_USERNAME = os.environ.get("WELCOME_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("WELCOME_ADMIN_PASSWORD", "change-me-now")
SESSION_STORE = {}
SESSION_LOCK = threading.Lock()


def get_db():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def run_migrations():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active_stay_id TEXT,
                headline TEXT NOT NULL,
                address TEXT NOT NULL,
                wifi_name TEXT NOT NULL,
                wifi_password TEXT NOT NULL,
                check_in_note TEXT NOT NULL,
                checkout_note TEXT NOT NULL,
                house_tips_json TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                contact_phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stays (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                guest_name TEXT NOT NULL,
                guest_count INTEGER NOT NULL,
                arrival_date TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                occasion TEXT NOT NULL,
                message TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tv_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                pairing_code TEXT NOT NULL,
                property_id TEXT NOT NULL,
                status TEXT NOT NULL
            );
            """
        )

        property_count = connection.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        if property_count == 0 and DATA_FILE.exists():
            seed_store = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            write_store(connection, seed_store)


def serialize_property(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "activeStayId": row["active_stay_id"] or "",
        "headline": row["headline"],
        "address": row["address"],
        "wifiName": row["wifi_name"],
        "wifiPassword": row["wifi_password"],
        "checkInNote": row["check_in_note"],
        "checkoutNote": row["checkout_note"],
        "houseTips": json.loads(row["house_tips_json"]),
        "contactName": row["contact_name"],
        "contactPhone": row["contact_phone"],
    }


def serialize_stay(row):
    return {
        "id": row["id"],
        "propertyId": row["property_id"],
        "guestName": row["guest_name"],
        "guestCount": row["guest_count"],
        "arrivalDate": row["arrival_date"],
        "departureDate": row["departure_date"],
        "occasion": row["occasion"],
        "message": row["message"],
    }


def serialize_device(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "pairingCode": row["pairing_code"],
        "propertyId": row["property_id"],
        "status": row["status"],
    }


def load_store():
    with get_db() as connection:
        properties = [
            serialize_property(row)
            for row in connection.execute("SELECT * FROM properties ORDER BY name, id")
        ]
        stays = [
            serialize_stay(row)
            for row in connection.execute("SELECT * FROM stays ORDER BY arrival_date, id")
        ]
        devices = [
            serialize_device(row)
            for row in connection.execute("SELECT * FROM tv_devices ORDER BY name, id")
        ]
    return {"properties": properties, "stays": stays, "tvDevices": devices}


def write_store(connection, store):
    connection.execute("DELETE FROM properties")
    connection.execute("DELETE FROM stays")
    connection.execute("DELETE FROM tv_devices")

    for property_item in store.get("properties", []):
        connection.execute(
            """
            INSERT INTO properties (
                id, name, active_stay_id, headline, address, wifi_name, wifi_password,
                check_in_note, checkout_note, house_tips_json, contact_name, contact_phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property_item["id"],
                property_item["name"],
                property_item.get("activeStayId", ""),
                property_item.get("headline", ""),
                property_item.get("address", ""),
                property_item.get("wifiName", ""),
                property_item.get("wifiPassword", ""),
                property_item.get("checkInNote", ""),
                property_item.get("checkoutNote", ""),
                json.dumps(property_item.get("houseTips", [])),
                property_item.get("contactName", ""),
                property_item.get("contactPhone", ""),
            ),
        )

    for stay_item in store.get("stays", []):
        connection.execute(
            """
            INSERT INTO stays (
                id, property_id, guest_name, guest_count, arrival_date, departure_date, occasion, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stay_item["id"],
                stay_item["propertyId"],
                stay_item.get("guestName", ""),
                int(stay_item.get("guestCount", 1)),
                stay_item.get("arrivalDate", ""),
                stay_item.get("departureDate", ""),
                stay_item.get("occasion", ""),
                stay_item.get("message", ""),
            ),
        )

    for device in store.get("tvDevices", []):
        connection.execute(
            """
            INSERT INTO tv_devices (id, name, pairing_code, property_id, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                device["id"],
                device.get("name", "Fire TV"),
                device.get("pairingCode", ""),
                device.get("propertyId", ""),
                device.get("status", "pending"),
            ),
        )


def save_store(store):
    with get_db() as connection:
        write_store(connection, store)


def json_response(handler, payload, status=HTTPStatus.OK, headers=None):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    if headers:
        for key, value in headers.items():
            handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, body, status=HTTPStatus.OK, headers=None):
    encoded = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    if headers:
        for key, value in headers.items():
            handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(encoded)


def read_json_body(handler):
    content_length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(content_length)
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def get_property(store, property_id):
    return next((item for item in store["properties"] if item["id"] == property_id), None)


def get_stay(store, stay_id):
    return next((item for item in store["stays"] if item["id"] == stay_id), None)


def get_active_stay_for_property(store, property_id):
    property_item = get_property(store, property_id)
    if not property_item:
        return None

    active_stay_id = property_item.get("activeStayId")
    if active_stay_id:
        stay_item = get_stay(store, active_stay_id)
        if stay_item and stay_item["propertyId"] == property_id:
            return stay_item

    return next((item for item in store["stays"] if item["propertyId"] == property_id), None)


def get_device(store, device_id):
    return next((item for item in store["tvDevices"] if item["id"] == device_id), None)


def get_device_by_pairing_code(store, pairing_code):
    return next((item for item in store["tvDevices"] if item.get("pairingCode") == pairing_code), None)


def make_device_id():
    return f"tv-{secrets.token_hex(6)}"


def make_pairing_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def create_device(store, device_name):
    device = {
        "id": make_device_id(),
        "name": device_name or "Fire TV",
        "pairingCode": make_pairing_code(),
        "propertyId": "",
        "status": "pending",
    }
    store["tvDevices"].append(device)
    return device


def session_signature(token):
    return hmac.new(SESSION_SECRET.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_session(username):
    token = secrets.token_urlsafe(32)
    with SESSION_LOCK:
        SESSION_STORE[token] = {"username": username}
    return f"{token}.{session_signature(token)}"


def parse_cookie(header_value):
    cookie = SimpleCookie()
    cookie.load(header_value)
    return cookie


def get_authenticated_user(handler):
    cookie_header = handler.headers.get("Cookie")
    if not cookie_header:
        return None

    cookie = parse_cookie(cookie_header)
    session_cookie = cookie.get(SESSION_COOKIE)
    if not session_cookie:
        return None

    raw_value = session_cookie.value
    if "." not in raw_value:
        return None

    token, signature = raw_value.rsplit(".", 1)
    if not hmac.compare_digest(signature, session_signature(token)):
        return None

    with SESSION_LOCK:
        session = SESSION_STORE.get(token)
    return session


def clear_session_cookie():
    return f"{SESSION_COOKIE}=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"


def make_session_cookie(session_value):
    return f"{SESSION_COOKIE}={session_value}; HttpOnly; Path=/; SameSite=Lax"


def verify_admin_credentials(username, password):
    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)


class WelcomeAppHandler(BaseHTTPRequestHandler):
    server_version = "WelcomeApp/0.2"

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/healthz":
            return json_response(self, {"ok": True})

        if parsed.path == "/api/session":
            return self.handle_session_status()

        if parsed.path == "/api/store":
            if not self.require_auth_json():
                return
            return json_response(self, load_store())

        if parsed.path == "/api/display":
            return self.handle_display(parsed)

        if parsed.path == "/api/tv":
            return self.handle_tv(parsed)

        if parsed.path == "/":
            if get_authenticated_user(self):
                return self.redirect("/admin.html")
            return self.redirect("/login.html")

        if parsed.path == "/admin.html":
            if not self.require_auth_page():
                return
            return self.serve_file("admin.html")

        if parsed.path.startswith("/"):
            requested = parsed.path.lstrip("/")
            if requested:
                return self.serve_file(requested)

        json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/store":
            return json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

        if not self.require_auth_json():
            return

        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            return json_response(self, {"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)

        if "properties" not in payload or "stays" not in payload:
            return json_response(self, {"error": "Store must contain properties and stays"}, HTTPStatus.BAD_REQUEST)

        payload.setdefault("tvDevices", [])
        save_store(payload)
        json_response(self, {"ok": True})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/session":
            return self.handle_login()

        if parsed.path == "/api/tv/register":
            return self.handle_tv_register()

        if parsed.path == "/api/tv/assign":
            if not self.require_auth_json():
                return
            return self.handle_tv_assign()

        return json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/session":
            return json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

        cookie_header = self.headers.get("Cookie")
        if cookie_header:
            cookie = parse_cookie(cookie_header)
            session_cookie = cookie.get(SESSION_COOKIE)
            if session_cookie and "." in session_cookie.value:
                token = session_cookie.value.split(".", 1)[0]
                with SESSION_LOCK:
                    SESSION_STORE.pop(token, None)

        return json_response(self, {"ok": True}, headers={"Set-Cookie": clear_session_cookie()})

    def handle_login(self):
        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            return json_response(self, {"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)

        username = payload.get("username", "").strip()
        password = payload.get("password", "")
        if not verify_admin_credentials(username, password):
            return json_response(self, {"error": "Invalid username or password"}, HTTPStatus.UNAUTHORIZED)

        session_value = issue_session(username)
        return json_response(
            self,
            {"ok": True, "username": username},
            headers={"Set-Cookie": make_session_cookie(session_value)},
        )

    def handle_session_status(self):
        session = get_authenticated_user(self)
        if not session:
            return json_response(self, {"authenticated": False}, HTTPStatus.UNAUTHORIZED)
        return json_response(self, {"authenticated": True, "username": session["username"]})

    def handle_display(self, parsed):
        params = parse_qs(parsed.query)
        property_id = params.get("property", [""])[0]
        stay_id = params.get("stay", [""])[0]

        store = load_store()
        property_item = get_property(store, property_id)
        stay_item = get_stay(store, stay_id)

        if not property_item:
            return json_response(self, {"error": "Property not found"}, HTTPStatus.NOT_FOUND)

        if not stay_item:
            return json_response(self, {"error": "Stay not found"}, HTTPStatus.NOT_FOUND)

        if stay_item["propertyId"] != property_id:
            return json_response(self, {"error": "Stay does not belong to property"}, HTTPStatus.BAD_REQUEST)

        json_response(self, {"property": property_item, "stay": stay_item})

    def handle_tv(self, parsed):
        params = parse_qs(parsed.query)
        property_id = params.get("property", [""])[0]
        store = load_store()
        device_id = params.get("deviceId", [""])[0]

        if device_id:
            device = get_device(store, device_id)
            if not device:
                return json_response(self, {"error": "Device not found"}, HTTPStatus.NOT_FOUND)
            if not device.get("propertyId"):
                return json_response(
                    self,
                    {"error": "This Fire TV is not paired to a property yet", "device": device},
                    HTTPStatus.PRECONDITION_REQUIRED,
                )
            property_id = device["propertyId"]

        if not property_id:
            return json_response(self, {"error": "Missing property"}, HTTPStatus.BAD_REQUEST)

        property_item = get_property(store, property_id)
        stay_item = get_active_stay_for_property(store, property_id)

        if not property_item:
            return json_response(self, {"error": "Property not found"}, HTTPStatus.NOT_FOUND)

        if not stay_item:
            return json_response(self, {"error": "No active stay configured for property"}, HTTPStatus.NOT_FOUND)

        json_response(
            self,
            {"property": property_item, "stay": stay_item, "refreshSeconds": 300},
        )

    def handle_tv_register(self):
        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            return json_response(self, {"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)

        device_name = payload.get("deviceName", "").strip()
        device_id = payload.get("deviceId", "").strip()

        store = load_store()
        device = get_device(store, device_id) if device_id else None

        if device:
            device["name"] = device_name or device.get("name") or "Fire TV"
            device["pairingCode"] = device.get("pairingCode") or make_pairing_code()
            device["status"] = "paired" if device.get("propertyId") else "pending"
        else:
            device = create_device(store, device_name)

        save_store(store)
        return json_response(
            self,
            {"device": device, "message": "Use this pairing code in the admin dashboard to assign the TV."},
        )

    def handle_tv_assign(self):
        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            return json_response(self, {"error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)

        pairing_code = payload.get("pairingCode", "").strip().upper()
        property_id = payload.get("propertyId", "").strip()
        display_name = payload.get("displayName", "").strip()

        if not pairing_code or not property_id:
            return json_response(self, {"error": "Pairing code and property are required"}, HTTPStatus.BAD_REQUEST)

        store = load_store()
        device = get_device_by_pairing_code(store, pairing_code)
        if not device:
            return json_response(self, {"error": "Pairing code not found"}, HTTPStatus.NOT_FOUND)

        property_item = get_property(store, property_id)
        if not property_item:
            return json_response(self, {"error": "Property not found"}, HTTPStatus.NOT_FOUND)

        device["propertyId"] = property_id
        device["status"] = "paired"
        if display_name:
            device["name"] = display_name

        save_store(store)
        return json_response(self, {"ok": True, "device": device, "property": property_item})

    def redirect(self, location):
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.end_headers()

    def require_auth_json(self):
        if get_authenticated_user(self):
            return True
        json_response(self, {"error": "Authentication required"}, HTTPStatus.UNAUTHORIZED)
        return False

    def require_auth_page(self):
        if get_authenticated_user(self):
            return True
        self.redirect("/login.html")
        return False

    def serve_file(self, relative_path):
        safe_path = (STATIC_DIR / relative_path).resolve()
        try:
            safe_path.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return json_response(self, {"error": "Invalid path"}, HTTPStatus.BAD_REQUEST)

        if not safe_path.exists() or not safe_path.is_file():
            return json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

        content_type, _ = mimetypes.guess_type(str(safe_path))
        content = safe_path.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    run_migrations()
    host = os.environ.get("WELCOME_APP_HOST", "0.0.0.0")
    port = int(os.environ.get("WELCOME_APP_PORT", "8000"))
    print(f"Serving welcome app at http://{host}:{port}")
    print(f"Admin login username: {ADMIN_USERNAME}")
    server = ThreadingHTTPServer((host, port), WelcomeAppHandler)
    server.serve_forever()
