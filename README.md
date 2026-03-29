# 🩸 LifeFlow — Blood Donation Management System

## 📌 Overview

LifeFlow is a web-based blood donation management system that connects donors and recipients efficiently. It allows users to manage donor records, create blood requests, and helps administrators monitor and control the entire system through a secure admin panel.


## 🚀 Features

* 🔐 **Admin Authentication**

  * Secure login system using hashed passwords
  * Session-based authentication

* 🧑‍🤝‍🧑 **Donor Management**

  * Add, view, search, and delete donors

* 🏥 **Recipient Management**

  * Manage recipient details efficiently

* 🩸 **Blood Request System**

  * Create and track blood requests

* 💻 **Modern UI**

  * Clean and responsive admin interface


## 🔒 Security Features

* Password hashing using Werkzeug (PBKDF2 + SHA-256)
* Environment variables for sensitive data (`.env`)
* Protected admin routes using session authentication
* No credentials exposed in source code

## 🛠️ Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Flask)
* **Database:** MySQL
