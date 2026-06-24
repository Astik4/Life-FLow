# 🩸 LifeFlow — Blood Donation Management System

## 📌 Overview

LifeFlow is a web-based blood donation management system designed to bridge the gap between donors and recipients. It allows public users to register profiles and log blood requests, while providing administrators with a secure dashboard to manage matches, verify records, and oversee system operations in real time.

---

## 🚀 Features

* 🔐 **Secure Admin Boundary**
  * Session-based cookie authentication.
  * Administrative endpoints protected via a server-side `@admin_required` decorator.
  * Password hashing utilizing **PBKDF2 + SHA-256** encryption in Werkzeug.
  
* 🧑‍🤝‍🧑 **Donor & Recipient Registries**
  * Public registration forms with validation checks.
  * Flexible inputs handling where optional fields (like location or donation dates) are parsed as SQL `NULL`s rather than blank strings.
  
* 🩸 **Active Request & Match Tracking**
  * Real-time creation, monitoring, and prioritizing of blood requests.
  * Intelligent matches query that filters compatible donors by location and blood group.
  * Safeguards to prevent matching without a registered recipient ID.

* 💻 **Dynamic Web Interface**
  * Premium crimson and charcoal styling built with custom Google Fonts.
  * Single-page nav layout using vanilla JavaScript `Fetch` API.
  * Public stats dashboard, blood type availability grid, and activity feed that sync automatically on page load.
  * Auto-refreshing admin panels when switching tabs.

---

## ⚙️ Architectural Refinements & Fixes

* **Thread-Safe Database Context**: Refactored the database layer in `app.py`. Instead of maintaining a single global connection (which crashes under concurrent traffic), LifeFlow binds database connections to the request context via `flask.g`, automatically tearing down connection handles when requests complete.
* **Cascade Deletions**: Configured `ON DELETE CASCADE` constraints on both `blood_request` and `matches` tables. Deleting a donor or recipient automatically cleans up related logs, preventing foreign key integrity conflicts.
* **Env Secrets Isolation**: All database logins, cookie signing keys, and admin hashes are loaded dynamically from a `.env` file, keeping secrets completely separated from source code.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (ES6+), Google Fonts
* **Backend:** Python (Flask), Werkzeug
* **Database:** MySQL 8.0, `mysql-connector-python`

---

## 💻 Setup & Installation

### 1. Prerequisites
- Python 3.8+
- MySQL Server running locally
- Python package manager (`pip`)

### 2. Configure Environment & Database
1. Restore database schema and seed data:
   ```bash
   mysql -u root -p < blood_donation.sql
   ```
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Generate an admin password hash:
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
   ```
4. Paste the generated hash and your MySQL credentials into the `.env` file.

### 3. Run the Application
1. Install requirements:
   ```bash
   pip install flask mysql-connector-python python-dotenv
   ```
2. Start the Flask server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.
