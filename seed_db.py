import urllib.request
import json
import random
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Database credentials
db_host = os.getenv("DB_HOST", "localhost")
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "")
db_name = os.getenv("DB_NAME", "blood_donation")

CITIES = ["Mumbai", "Delhi", "Bangalore", "Pune", "Chennai", "Hyderabad", "Kolkata", "Ahmedabad"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

def clean_phone(phone_str):
    clean = "".join([c for c in phone_str if c.isdigit()])
    if len(clean) > 10:
        return clean[:10]
    return clean if clean else "9876543210"

def get_random_date_offset(days_ago):
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

def seed():
    print("Connecting to the database...")
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            auth_plugin="mysql_native_password"
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    print("Fetching 30 random realistic profiles from RandomUser API...")
    try:
        url = "https://randomuser.me/api/?results=30&nat=in"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode())
            profiles = res_data.get("results", [])
    except Exception as e:
        print(f"Failed to fetch from API ({e}). Falling back to static generation...")
        fallback_names = [
            ("Aarav", "Male"), ("Vihaan", "Male"), ("Aditya", "Male"), ("Siddharth", "Male"),
            ("Diya", "Female"), ("Ananya", "Female"), ("Kiara", "Female"), ("Ishaan", "Male"),
            ("Arjun", "Male"), ("Rohan", "Male"), ("Neha", "Female"), ("Pooja", "Female"),
            ("Sanya", "Female"), ("Kabir", "Male"), ("Dev", "Male"), ("Maya", "Female")
        ]
        profiles = []
        for i in range(30):
            first, gender = random.choice(fallback_names)
            last = random.choice(["Sharma", "Verma", "Gupta", "Mehta", "Patel", "Singh", "Nair", "Reddy"])
            profiles.append({
                "name": {"first": first, "last": last},
                "gender": gender.lower(),
                "location": {"city": random.choice(CITIES)},
                "phone": f"98765{i:05d}"
            })

    print(f"Loaded {len(profiles)} profiles. Cleaning existing database tables...")
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE matches;")
        cursor.execute("TRUNCATE TABLE blood_request;")
        cursor.execute("TRUNCATE TABLE recipient;")
        cursor.execute("TRUNCATE TABLE donor;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
    except Exception as e:
        print(f"Error truncating tables: {e}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        return

    donor_profiles = profiles[:15]
    recipient_profiles = profiles[15:]

    donors = []
    recipients = []

    print("Inserting realistic donors...")
    for idx, p in enumerate(donor_profiles, start=1):
        donor_id = f"D{idx:03d}"
        name = f"{p['name']['first']} {p['name']['last']}"
        bg = random.choice(BLOOD_GROUPS)
        age = random.randint(18, 55)
        gender = p["gender"].capitalize()
        phone = clean_phone(p["phone"])
        city = p.get("location", {}).get("city", random.choice(CITIES)).capitalize()
        
        has_donated = random.choice([True, False])
        last_donation = get_random_date_offset(random.randint(10, 180)) if has_donated else None

        query = """
            INSERT INTO donor (Donor_id, Blood_Group, Name, Age, Gender, Phone, City, Last_Donation_Date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (donor_id, bg, name, age, gender, phone, city, last_donation))
        donors.append({
            "donor_id": donor_id,
            "name": name,
            "blood_group": bg,
            "city": city
        })

    print("Inserting realistic recipients...")
    for idx, p in enumerate(recipient_profiles, start=1):
        recipient_id = f"R{idx:03d}"
        name = f"{p['name']['first']} {p['name']['last']}"
        bg = random.choice(BLOOD_GROUPS)
        age = random.randint(15, 75)
        gender = p["gender"].capitalize()
        phone = clean_phone(p["phone"])
        city = p.get("location", {}).get("city", random.choice(CITIES)).capitalize()

        query = """
            INSERT INTO recipient (Recipient_id, Blood_Group, Name, Age, Gender, Phone, City)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (recipient_id, bg, name, age, gender, phone, city))
        recipients.append({
            "recipient_id": recipient_id,
            "name": name,
            "blood_group": bg,
            "city": city
        })

    conn.commit()

    print("Inserting blood requests...")
    requests = []
    for idx in range(1, 11):
        request_id = f"REQ{idx:03d}"
        recip = recipients[idx - 1]
        
        if idx <= 4:
            status = "matched"
        elif idx <= 7:
            status = "pending"
        else:
            status = "urgent"

        req_date = get_random_date_offset(random.randint(2, 30))
        city = recip["city"]
        bg = recip["blood_group"]

        query = """
            INSERT INTO blood_request (Request_id, Recipient_id, Blood_Group, Request_date, City, Status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (request_id, recip["recipient_id"], bg, req_date, city, status))
        requests.append({
            "request_id": request_id,
            "recipient_id": recip["recipient_id"],
            "recipient_name": recip["name"],
            "blood_group": bg,
            "city": city,
            "status": status,
            "date": req_date
        })

    conn.commit()

    print("Inserting historical matches...")
    match_count = 1
    for req in requests:
        if req["status"] == "matched":
            compatible_donors = [d for d in donors if d["blood_group"] == req["blood_group"]]
            if not compatible_donors:
                compatible_donors = donors
            
            donor = random.choice(compatible_donors)
            match_id = f"MCH{match_count:03d}"
            match_date = get_random_date_offset(random.randint(1, 5))
            
            query = """
                INSERT INTO matches (Match_id, Donor_id, Donor_name, Recipient_id, Recipient_name, Blood_Group, Match_date, City)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                match_id,
                donor["donor_id"],
                donor["name"],
                req["recipient_id"],
                req["recipient_name"],
                req["blood_group"],
                match_date,
                req["city"]
            ))
            match_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeding completed successfully! All entries uppercase-standardized.")

if __name__ == "__main__":
    seed()
