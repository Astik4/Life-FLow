import mysql.connector
from flask import Flask, request, render_template, jsonify
import hashlib

app = Flask(__name__)

# ─────────────────────────────────────────────
#  DATABASE CONNECTION
# ─────────────────────────────────────────────

def get_db():
    """Create and return a fresh DB connection."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="blood_donation",
        auth_plugin="mysql_native_password"
    )

try:
    db = get_db()
    cursor = db.cursor()
    print("✅ Connected to MySQL database.")
except mysql.connector.Error as err:
    print(f"❌ Error connecting to MySQL: {err}")
    db = None
    cursor = None


def safe_cursor():
    """Return a working cursor, reconnecting if the connection dropped."""
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        db = get_db()
    cursor = db.cursor()
    return cursor


# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────

def success(data=None, message="Success", code=200):
    body = {"success": True, "message": message}
    if data is not None:
        body.update(data)
    return jsonify(body), code


def error(message="An error occurred", code=500):
    return jsonify({"success": False, "message": message}), code


# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin.html")


# ─────────────────────────────────────────────
#  ADMIN AUTH
# ─────────────────────────────────────────────

ADMIN_USERNAME = "Astik"
ADMIN_PASSWORD = ""          # ← change to a real password

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error("Username and password are required.", 400)

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return success(message="Login successful.")
    return error("Invalid username or password.", 401)


# ─────────────────────────────────────────────
#  DONORS
# ─────────────────────────────────────────────

@app.route("/add_donor", methods=["POST"])
def add_donor():
    data = request.get_json(silent=True) or {}
    required = ["donor_id", "blood_group", "name", "age", "gender", "phone", "city", "last_donation_date"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    query = """
        INSERT INTO donor (Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data["donor_id"], data["blood_group"], data["name"],
        data["age"], data["gender"], data["phone"],
        data["city"], data["last_donation_date"]
    )
    try:
        cur = safe_cursor()
        cur.execute(query, values)
        db.commit()
        return success(message="Donor added successfully.")
    except mysql.connector.Error as err:
        print(f"Error inserting donor: {err}")
        return error("Failed to add donor. ID may already exist.")


@app.route("/all_donors")
def all_donors():
    try:
        cur = safe_cursor()
        cur.execute("SELECT Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date FROM donor")
        rows = cur.fetchall()
        donors = [
            {
                "donor_id":           row[0],
                "blood_group":        row[1],
                "name":               row[2],
                "age":                row[3],
                "gender":             row[4],
                "phone":              row[5],
                "city":               row[6],
                "last_donation_date": str(row[7])
            }
            for row in rows
        ]
        return success({"donors": donors}, message=f"{len(donors)} donors fetched.")
    except mysql.connector.Error as err:
        print(f"Error fetching donors: {err}")
        return error("Failed to fetch donors.")


@app.route("/search_donor/<donor_id>", methods=["GET"])
def search_donor(donor_id):
    try:
        cur = safe_cursor()
        cur.execute("SELECT Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date FROM donor WHERE Donor_id = %s", (donor_id,))
        row = cur.fetchone()
        if not row:
            return error("Donor not found.", 404)
        donor = {
            "donor_id":           row[0],
            "blood_group":        row[1],
            "name":               row[2],
            "age":                row[3],
            "gender":             row[4],
            "phone":              row[5],
            "city":               row[6],
            "last_donation_date": str(row[7])
        }
        return success({"donor": donor})
    except mysql.connector.Error as err:
        print(f"Error fetching donor: {err}")
        return error("Failed to fetch donor.")


@app.route("/delete_donor/<donor_id>", methods=["DELETE"])
def delete_donor(donor_id):
    try:
        cur = safe_cursor()
        cur.execute("DELETE FROM donor WHERE Donor_id = %s", (donor_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Donor not found.", 404)
        return success(message=f"Donor '{donor_id}' deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error deleting donor: {err}")
        return error("Failed to delete donor.")


# ─────────────────────────────────────────────
#  RECIPIENTS
# ─────────────────────────────────────────────

@app.route("/add_recipient", methods=["POST"])
def add_recipient():
    data = request.get_json(silent=True) or {}
    required = ["recipient_id", "blood_group", "name", "age", "gender", "phone", "city"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    query = """
        INSERT INTO recipient (Recipient_id, Blood_Group, Name, Age, Gender, Phone, City)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data["recipient_id"], data["blood_group"], data["name"],
        data["age"], data["gender"], data["phone"], data["city"]
    )
    try:
        cur = safe_cursor()
        cur.execute(query, values)
        db.commit()
        return success(message="Recipient added successfully.")
    except mysql.connector.Error as err:
        print(f"Error inserting recipient: {err}")
        return error("Failed to add recipient. ID may already exist.")


@app.route("/all_recipients")
def all_recipients():
    try:
        cur = safe_cursor()
        cur.execute("SELECT Recipient_id, Blood_Group, Name, Age, Gender, Phone, City FROM recipient")
        rows = cur.fetchall()
        recipients = [
            {
                "recipient_id": row[0],
                "blood_group":  row[1],
                "name":         row[2],
                "age":          row[3],
                "gender":       row[4],
                "phone":        row[5],
                "city":         row[6]
            }
            for row in rows
        ]
        return success({"recipients": recipients}, message=f"{len(recipients)} recipients fetched.")
    except mysql.connector.Error as err:
        print(f"Error fetching recipients: {err}")
        return error("Failed to fetch recipients.")


@app.route("/search_recipient/<recipient_id>", methods=["GET"])
def search_recipient(recipient_id):
    try:
        cur = safe_cursor()
        cur.execute("SELECT * FROM recipient WHERE Recipient_id = %s", (recipient_id,))
        row = cur.fetchone()
        if not row:
            return error("Recipient not found.", 404)
        recipient = {
            "recipient_id": row[0],
            "blood_group":  row[1],
            "name":         row[2],
            "age":          row[3],
            "gender":       row[4],
            "phone":        row[5],
            "city":         row[6]
        }
        return success({"recipient": recipient})
    except mysql.connector.Error as err:
        print(f"Error fetching recipient: {err}")
        return error("Failed to fetch recipient.")


# ─────────────────────────────────────────────
#  BLOOD REQUESTS
# ─────────────────────────────────────────────

@app.route("/create_request", methods=["POST"])
def create_request():
    data = request.get_json(silent=True) or {}
    required = ["request_id", "recipient_id", "blood_group", "request_date", "city", "status"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    query = """
        INSERT INTO blood_request (Request_id, Recipient_id, Blood_Group, Request_date, City, Status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        data["request_id"], data["recipient_id"], data["blood_group"],
        data["request_date"], data["city"], data["status"]
    )
    try:
        cur = safe_cursor()
        cur.execute(query, values)
        db.commit()
        return success(message="Blood request created successfully.")
    except mysql.connector.Error as err:
        print(f"Error inserting blood request: {err}")
        return error("Failed to create blood request. ID may already exist.")


@app.route("/all_requests")
def all_requests():
    try:
        cur = safe_cursor()
        cur.execute("SELECT Request_id, Recipient_id, Blood_Group, Request_date, City, Status FROM blood_request")
        rows = cur.fetchall()
        requests = [
            {
                "request_id":   row[0],
                "recipient_id": row[1],
                "blood_group":  row[2],
                "request_date": str(row[3]),
                "city":         row[4],
                "status":       row[5]
            }
            for row in rows
        ]
        return success({"requests": requests}, message=f"{len(requests)} requests fetched.")
    except mysql.connector.Error as err:
        print(f"Error fetching requests: {err}")
        return error("Failed to fetch blood requests.")


# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)