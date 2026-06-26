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

---

## 🌐 Deployment to PythonAnywhere

Follow these step-by-step instructions to deploy LifeFlow on a free PythonAnywhere account:

### 1. Set Up MySQL Database on PythonAnywhere
1. Log in to your [PythonAnywhere account](https://www.pythonanywhere.com/).
2. Navigate to the **Databases** tab.
3. Choose a MySQL password and initialize the MySQL server.
4. Under **Create a database**, create a new database named `blood_donation`. Note the full database name (it will be prefixed with your username, e.g., `yourusername$blood_donation`).
5. Open a **Bash Console** from the dashboard.
6. Connect to your MySQL database to import the schema:
   ```bash
   mysql -h yourusername.mysql.pythonanywhere-services.com -u yourusername -p 'yourusername$blood_donation' < /home/yourusername/Life-FLow/blood_donation.sql
   ```
   *(Ensure you run this after cloning the repository in Step 2)*.

### 2. Clone Repository & Install Dependencies
1. Open a **Bash Console** on PythonAnywhere.
2. Clone your git repository:
   ```bash
   git clone https://github.com/Astik4/Life-FLow.git
   ```
3. Navigate to the directory and set up a virtual environment:
   ```bash
   cd Life-FLow
   python -m venv venv
   source venv/bin/activate
   pip install flask mysql-connector-python python-dotenv
   ```

### 3. Configure Environment Variables
1. Inside the console (within the `Life-FLow` folder), create a `.env` file:
   ```bash
   nano .env
   ```
2. Paste the following configuration, adjusting for your credentials:
   ```env
   DB_HOST=yourusername.mysql.pythonanywhere-services.com
   DB_USER=yourusername
   DB_PASSWORD=your_mysql_password
   DB_NAME=yourusername$blood_donation
   SECRET_KEY=generate_a_random_secret_key_here
   ADMIN_USERNAME=Astik
   ADMIN_PASSWORD=Astik@042509
   ADMIN_PASSWORD_HASH=pbkdf2:sha256:1000000$SEbIrOcXrnNkJYe4$2dcd2d212dfb534eefd7d843ecc2f46f9ea375d1cc456d431b647d4f2976a512
   ```
3. Save and close (`Ctrl+O`, `Enter`, `Ctrl+X`).

### 4. Seed the Database (Optional)
To populate your hosted database with the standard realistic mock profiles:
```bash
python seed_db.py
```

### 5. Configure Web App & WSGI
1. Go to the **Web** tab on PythonAnywhere.
2. Click **Add a new web app**.
3. Choose **Manual Configuration** and select your python version (matching the virtualenv, e.g., Python 3.10 or 3.11).
4. Under **Code**, set:
   * **Source code**: `/home/yourusername/Life-FLow`
   * **Working directory**: `/home/yourusername/Life-FLow`
5. Under **Virtualenv**, set:
   * **Path**: `/home/yourusername/Life-FLow/venv`
6. Under **Code**, click on the **WSGI configuration file** link.
7. Replace the entire content of that file with the content in `pythonanywhere_wsgi.py` (making sure to replace `YOUR_PYTHONANYWHERE_USERNAME` with your actual username).
8. Go back to the **Web** tab and click **Reload**. Your site is now live at `https://yourusername.pythonanywhere.com/`!
