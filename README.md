# 🏥 Medcare - Smart Hospital ERP System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.2-black?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Groq AI](https://img.shields.io/badge/AI-Groq%20LLaMA3-FF4F00?style=for-the-badge&logo=artificial-intelligence)

Medcare is a comprehensive, AI-powered Hospital Management System (ERP) designed to streamline hospital operations, enhance patient care, and provide intelligent medical predictions. Built with Python and Flask, this system offers a robust architecture with role-based access control and real-time analytics.

## ✨ Key Features

* 🔐 **Role-Based Access Control (RBAC):** Dedicated, secure portals for **Admins**, **Doctors**, **Nurses**, and **Patients**.
* 🤖 **AI Diagnostic Assistant:** Integrates with the **Groq API (LLaMA-3.3-70b)** to analyze patient symptoms and uploaded medical documents (PDFs) to predict potential diseases and calculate severity scores.
* 📊 **Interactive Dashboards:** Real-time analytics and statistics using **Chart.js** (Revenue tracking, appointment trends, doctor distributions).
* 📅 **Advanced Scheduling:** Manage doctor availability, shifts, and handle patient appointment bookings efficiently.
* 🛏️ **Ward & Room Management:** Real-time tracking of room occupancy, patient assignments, and maintenance status.
* 💳 **Billing & Financials:** Generate invoices, process payments, and track outstanding hospital bills.
* 🛡️ **High Security & Auditing:** Features password hashing (Werkzeug), protection against duplicate entries, secure sessions, and a comprehensive **Audit Log** to track all system actions.

## 🛠️ Technology Stack

**Backend:**
* Python
* Flask (Web Framework)
* SQLite3 (Relational Database)

**Frontend:**
* HTML5 / CSS3 / JavaScript
* Bootstrap 5 (Responsive UI)
* Chart.js (Data Visualization)

**AI & Utilities:**
* **Groq API:** Ultra-fast LLM inference for medical predictions.
* **PyPDF2:** Parsing uploaded medical records and prescriptions.
* **Werkzeug Security:** Advanced password hashing.

## 📂 Project Structure

```text
Smart_Hospital_System/
├── static/
│   ├── css/
│   ├── img/
│   └── uploads/          # User-uploaded files (Git-ignored)
├── templates/
│   ├── admin/            # Admin-only views (Users, Audit, Depts)
│   ├── auth/             # Login, Profile, Password Management
│   ├── clinical/         # Records, Prescriptions, AI Prediction
│   ├── operations/       # Appointments, Billing, Rooms
│   ├── staff/            # Doctors, Nurses schedules
│   ├── dashboard.html    # Dynamic role-based dashboard
│   └── base.html         # Main layout and sidebar
├── app.py                # Main Flask application & routes
├── schema.sql            # Database schema for setup
├── requirements.txt      # Python dependencies
└── .env                  # API keys (Git-ignored)

```


## 🚀 Installation & Setup

Follow these steps to run the Medcare ERP locally on your machine:

### 1. Clone the Repository
```bash
git clone [https://github.com/YoussefAtef15/Medcare-Smart-Hospital-ERP.git](https://github.com/YoussefAtef15/Medcare-Smart-Hospital-ERP.git)
cd Medcare-Smart-Hospital-ERP
```
### 2. Set Up Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```


### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup
Initialize the SQLite database using the provided schema:

```bash
sqlite3 "Smart Hospital System.db" < schema.sql
```

### 5. Environment Variables
Create a `.env` file in the root directory and add your Groq API key for the AI features:

```env
GROQ_API_KEY=your_api_key_here
```

### 6. Run the Application

```bash
python app.py
```

## 🔑 Default Test Accounts

Upon the first run, the system automatically initializes the master admin account:

* **Username:** `admin`
* **Password:** `123456`

> **Note:** You can use this account to log in, create doctors, nurses, and patient profiles, and explore the system's full functionality.
