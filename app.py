import mysql.connector
from flask import Flask, request, render_template, jsonify, redirect, session
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

#  DATABASE CONNECTION
def get_db():
    return mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
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


#  HELPER
def success(data=None, message="Success", code=200):
    body = {"success": True, "message": message}
    if data is not None:
        body.update(data)
    return jsonify(body), code


def error(message="An error occurred", code=500):
    return jsonify({"success": False, "message": message}), code


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

#LOGOUT
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/")


#  ADMIN AUTH
ADMIN_USERNAME = "Astik"

ADMIN_PASSWORD_HASH = "pbkdf2:sha256:1000000$SEbIrOcXrnNkJYe4$2dcd2d212dfb534eefd7d843ecc2f46f9ea375d1cc456d431b647d4f2976a512"

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        session["admin_logged_in"] = True
        return jsonify({"success": True})
    
    if not session.get("admin_logged_in"):
        return error("Unauthorized", 403)

    return jsonify({"success": False, "message": "Invalid username or password"}), 401

#  DONORS
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
        cur.execute("SELECT * FROM donor")
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


@app.route("/search_donor/", methods=["GET"])
def search_donor():
    donor_id = request.args.get("donor_id")
    city = request.args.get("city")
    try:
        cur = safe_cursor()
        cur.execute("SELECT * FROM donor WHERE Donor_id = %s OR City = %s", (donor_id, city))
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

#  RECIPIENTS
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
        cur.execute("SELECT * FROM recipient")
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
    
@app.route("/delete_recipient/<recipient_id>", methods=["DELETE"])
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
        cur.execute("SELECT * FROM blood_request")
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
    
@app.route("/delete_request/<request_id>", methods=["DELETE"])
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
    

if __name__ == "__main__":
    app.run(debug=True)