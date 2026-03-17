# 🏥 Medcare - Smart Hospital ERP

![Medcare Banner](https://img.shields.io/badge/Medcare-Smart_Hospital_System-158765?style=for-the-badge&logo=hospital)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.2-black?style=flat-square&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap)
![Groq AI](https://img.shields.io/badge/AI-Groq_API-f56565?style=flat-square)

## 📌 Overview
**Medcare** is a comprehensive, AI-powered Enterprise Resource Planning (ERP) system designed specifically for modern hospitals and healthcare facilities. It streamlines hospital operations, automates administrative workflows, and integrates cutting-edge Generative AI (via Groq) to assist medical professionals with disease prediction, medical document analysis, and smart scheduling.

## ✨ Key Features

### 🔐 Role-Based Access Control (RBAC)
Dedicated, secure dashboards dynamically tailored for 4 distinct user roles:
* **Admin:** Full system oversight, user management, financial tracking, and audit logs.
* **Doctor:** Medical records management, prescription generation, patient tracking, and AI diagnostic assistance.
* **Nurse:** Ward/room assignments, patient monitoring, and shift management.
* **Patient:** Personal appointment booking, billing history, and medical record viewing.

### 🤖 Medcare AI Center (Powered by Groq)
* **Diagnostic Assistant:** Analyzes patient symptoms, age, and gender to predict potential diseases with a calculated Confidence Score.
* **Vision AI Integration:** Upload medical reports (PDF) or medical scans (X-Rays/MRIs via JPG/PNG) for automated AI contextual analysis.
* **Smart Hospital Analytics:** Generates real-time insights on peak hours, common diagnoses, and busiest departments.
* **Interactive AI Chat:** Doctors can chat securely with the AI to discuss specific diagnoses and treatment plans based on patient history.

### 🏥 Core Modules
* **Patient Management:** Complete CRUD operations for patient profiles, medical history, and demographics.
* **Appointment Scheduling:** Real-time booking, status tracking (Pending, Completed, Canceled), and doctor availability management.
* **Medical Records & Prescriptions:** Secure logging of visit details, diagnoses, treatments, allergies, and printable medication prescriptions.
* **Billing & Finance:** Automated invoice generation (consultation, lab, meds), payment tracking (Full/Partial), and revenue analytics.
* **Rooms & Wards:** Visual management of hospital capacity, real-time room status (Available, Occupied, Maintenance), and admission history.
* **Staff Management:** Directories and shift scheduling for doctors and nurses.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend Framework** | Python, Flask, Werkzeug |
| **Database** | SQLite (Relational DB with 11 interlinked tables) |
| **Frontend Integration** | HTML5, CSS3, Bootstrap 5, Vanilla JavaScript |
| **Data Visualization** | Chart.js (Dynamic Dashboards) |
| **Alerts & UI** | SweetAlert2 |
| **AI Integration** | Groq API (LLMs and Vision Models via OpenAI SDK) |
| **Deployment Prep** | Gunicorn |

---

## 🗄️ Database Architecture
The system utilizes a robust SQLite relational database designed for data integrity and cascading updates. Key entities include:
* `Department`, `Doctor`, `Nurse` (Staff mapping)
* `Patient`, `EmergencyContact` (Demographics & Relations)
* `Appointment`, `Room` (Operations & Capacity)
* `MedicalRecord`, `Prescription`, `Prescription_Item` (Clinical Data)
* `Bill` (Financials)
* `AI_Prediction`, `AuditLog` (System Intelligence & Security)

---

## 📂 Project Structure

```text
Smart_Hospital_System/
├── ai_model/                 # AI model training and ML scripts
│   └── train_model.py        # Script to train the predictive model
├── static/                   # Static assets (CSS, JS, Images)
│   ├── css/
│   │   └── style.css         # Main stylesheet (Flexbox/Grid, etc.)
│   ├── img/                  # Image assets
│   │   ├── Doctor_img.jpg
│   │   └── avatar.png
│   └── js/
│       └── main.js           # Frontend JavaScript logic 
├── templates/                # HTML templates for the UI
│   ├── admin/                # Admin-only views (Users, Audit, Depts)
│   │   ├── audit.html
│   │   ├── departments.html
│   │   └── users.html
│   ├── auth/                 # Authentication & User Management
│   │   ├── change_password.html
│   │   ├── login.html
│   │   └── profile.html
│   ├── clinical/             # Clinical records, Prescriptions, AI Prediction
│   │   ├── ai_prediction.html
│   │   ├── patients.html
│   │   ├── prescriptions.html
│   │   └── records.html
│   ├── operations/           # Daily operations (Appointments, Billing, Rooms)
│   │   ├── appointments.html
│   │   ├── billing.html
│   │   └── rooms.html
│   ├── staff/                # Staff management & Schedules
│   │   ├── doctor_schedule.html
│   │   ├── doctors.html
│   │   └── nurses.html
│   ├── base.html             # Main layout and sidebar wrapper
│   └── dashboard.html        # Dynamic role-based dashboard
├── README.md                 # Project documentation
├── app.py                    # Main Flask application & routes
├── database_setup.sql        # SQL schema for database setup (PostgreSQL)
├── init_db.py                # Python script to run the SQL and initialize DB
└── requirements.txt          # Python dependencies

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

## 🔑 Default Credentials (Testing)

To facilitate testing and development, the database is pre-seeded with test accounts across all system roles. 

> **⚠️ Important Note:** The password for **ALL** test accounts below is `123456`.

### 👥 System Users

| Role | Username | Password | Profile Details (From Seed Data) |
| :--- | :--- | :--- | :--- |
| **🛡️ Admin** | `admin` | `123456` | System Administrator (Full Access) |
| **🩺 Doctor** | `dr.magdy` | `123456` | Dr. Magdy Yacoub (Cardiologist, Dept: Cardiology) |
| **🩺 Doctor** | `dr.hisham` | `123456` | Dr. Hisham Sadek (Neurologist, Dept: Neurology) |
| **💉 Nurse** | `nurse.heba` | `123456` | Nurse Heba Sayed (Morning Shift, Dept: Cardiology) |
| **💉 Nurse** | `nurse.amr` | `123456` | Nurse Amr Gamal (Night Shift, Dept: Neurology) |
| **🤒 Patient** | `pt.ahmed` | `123456` | Ahmed Mohamed (DOB: 1985, Blood Type: O+) |
| **🤒 Patient** | `pt.salma` | `123456` | Salma Ibrahim (DOB: 1992, Blood Type: A-) |

> **Note:** You can use the **Admin** account to log in, create doctors, nurses, and patient profiles, and explore the system's full functionality.