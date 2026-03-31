import mysql.connector
from flask import Flask, request, render_template, jsonify, redirect, session
from werkzeug.security import check_password_hash
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-dev-secret")

#  DATABASE CONNECTION
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "blood_donation"),
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


#  RESPONSE HELPERS
def success(data=None, message="Success", code=200):
    body = {"success": True, "message": message}
    if data is not None:
        body.update(data)
    return jsonify(body), code

def error(message="An error occurred", code=500):
    return jsonify({"success": False, "message": message}), code


#  AUTH GUARD DECORATOR
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return error("Unauthorized. Please log in.", 403)
        return f(*args, **kwargs)
    return decorated

#  PAGE ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin")
    return render_template("admin.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin")


#  ADMIN AUTH
ADMIN_USERNAME      = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True)
    if not data:
        return error("No data received.", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error("Username and password are required.", 400)

    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session["admin_logged_in"] = True
        return jsonify({"success": True, "message": "Login successful."})

    return jsonify({"success": False, "message": "Invalid username or password."}), 401


#  DONORS
@app.route("/add_donor", methods=["POST"])
def add_donor():
    data = request.get_json(silent=True) or {}
    required = ["donor_id", "blood_group", "name", "age", "gender", "phone", "city", "last_donation_date"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
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
        cur.execute("""
            SELECT Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date
            FROM donor
        """)
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
                "last_donation_date": str(row[7]) if row[7] else ""
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
        # ✅ FIXED: original had broken SQL "WHERE Donor_id and = %s"
        cur.execute("""
            SELECT Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date
            FROM donor WHERE Donor_id = %s
        """, (donor_id,))
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
            "last_donation_date": str(row[7]) if row[7] else ""
        }
        return success({"donor": donor})
    except mysql.connector.Error as err:
        print(f"Error fetching donor: {err}")
        return error("Failed to fetch donor.")


@app.route("/delete_donor/<donor_id>", methods=["DELETE"])
@admin_required
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
    
#  RECIPIENTS
@app.route("/add_recipient", methods=["POST"])
def add_recipient():
    data = request.get_json(silent=True) or {}
    required = ["recipient_id", "blood_group", "name", "age", "gender", "phone", "city"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
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
        cur.execute("""
            SELECT Recipient_id, Blood_Group, Name, Age, Gender, Phone, City
            FROM recipient
        """)
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
        cur.execute("""
            SELECT Recipient_id, Blood_Group, Name, Age, Gender, Phone, City
            FROM recipient WHERE Recipient_id = %s
        """, (recipient_id,))
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


@app.route("/delete_recipient/<recipient_id>", methods=["DELETE"])
@admin_required
def delete_recipient(recipient_id):
    try:
        cur = safe_cursor()
        cur.execute("DELETE FROM recipient WHERE Recipient_id = %s", (recipient_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Recipient not found.", 404)
        return success(message=f"Recipient '{recipient_id}' deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error deleting recipient: {err}")
        return error("Failed to delete recipient.")


#  BLOOD REQUESTS
@app.route("/create_request", methods=["POST"])
def create_request():
    data = request.get_json(silent=True) or {}
    required = ["request_id", "recipient_id", "blood_group", "request_date", "city", "status"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
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
        cur.execute("""
            SELECT Request_id, Recipient_id, Blood_Group, Request_date, City, Status
            FROM blood_request
        """)
        rows = cur.fetchall()
        requests = [
            {
                "request_id":   row[0],
                "recipient_id": row[1],
                "blood_group":  row[2],
                "request_date": str(row[3]) if row[3] else "",
                "city":         row[4],
                "status":       row[5]
            }
            for row in rows
        ]
        return success({"requests": requests}, message=f"{len(requests)} requests fetched.")
    except mysql.connector.Error as err:
        print(f"Error fetching requests: {err}")
        return error("Failed to fetch blood requests.")


@app.route("/delete_request/<request_id>", methods=["DELETE"])
@admin_required
def delete_request(request_id):
    try:
        cur = safe_cursor()
        cur.execute("DELETE FROM blood_request WHERE Request_id = %s", (request_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Blood request not found.", 404)
        return success(message=f"Blood request '{request_id}' deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error deleting blood request: {err}")
        return error("Failed to delete blood request.")


#  MATCHES
@app.route("/find_matches")
def find_matches():
    """Return donors filtered by blood_group and/or city for the matches panel."""
    blood_group = request.args.get("blood_group", "").strip()
    city        = request.args.get("city", "").strip()

    if not blood_group and not city:
        return error("Provide at least blood_group or city.", 400)

    conditions, values = [], []
    if blood_group:
        conditions.append("Blood_Group = %s")
        values.append(blood_group)
    if city:
        conditions.append("LOWER(City) LIKE %s")
        values.append(f"%{city.lower()}%")

    query = f"""
        SELECT Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date
        FROM donor WHERE {" AND ".join(conditions)}
    """
    try:
        cur = safe_cursor()
        cur.execute(query, tuple(values))
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
                "last_donation_date": str(row[7]) if row[7] else ""
            }
            for row in rows
        ]
        return success({"donors": donors}, message=f"{len(donors)} compatible donors found.")
    except mysql.connector.Error as err:
        print(f"Error finding matches: {err}")
        return error("Failed to find matches.")


@app.route("/create_match", methods=["POST"])
@admin_required
def create_match():
    data = request.get_json(silent=True) or {}
    required = ["match_id", "donor_id", "recipient_id", "match_date", "city"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    query = """
        INSERT INTO matches
            (Match_id, Donor_id, Donor_name, Recipient_id, Recipient_name, Blood_Group, Match_date, City)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data["match_id"],
        data["donor_id"],
        data.get("donor_name", ""),
        data["recipient_id"],
        data.get("recipient_name", ""),
        data.get("blood_group", ""),
        data["match_date"],
        data["city"]
    )
    try:
        cur = safe_cursor()
        cur.execute(query, values)
        db.commit()
        return success(message=f"Match '{data['match_id']}' recorded successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating match: {err}")
        return error("Failed to record match. ID may already exist.")


@app.route("/all_matches")
def all_matches():
    try:
        cur = safe_cursor()
        cur.execute("""
            SELECT Match_id, Donor_id, Donor_name, Recipient_id, Recipient_name,
                   Blood_Group, Match_date, City
            FROM matches
        """)
        rows = cur.fetchall()
        matches = [
            {
                "match_id":       row[0],
                "donor_id":       row[1],
                "donor_name":     row[2] or "",
                "recipient_id":   row[3],
                "recipient_name": row[4] or "",
                "blood_group":    row[5] or "",
                "match_date":     str(row[6]) if row[6] else "",
                "city":           row[7] or ""
            }
            for row in rows
        ]
        return success({"matches": matches}, message=f"{len(matches)} matches fetched.")
    except mysql.connector.Error as err:
        print(f"Error fetching matches: {err}")
        return error("Failed to fetch matches.")


@app.route("/delete_match/<match_id>", methods=["DELETE"])
@admin_required
def delete_match(match_id):
    try:
        cur = safe_cursor()
        cur.execute("DELETE FROM matches WHERE Match_id = %s", (match_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Match not found.", 404)
        return success(message=f"Match '{match_id}' deleted successfully.")
    except mysql.connector.Error as err:
        print(f"Error deleting match: {err}")
        return error("Failed to delete match.")


if __name__ == "__main__":
    app.run(debug=True)