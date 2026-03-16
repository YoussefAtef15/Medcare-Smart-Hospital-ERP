
-- ========================================================
-- SMART HOSPITAL SYSTEM - DATABASE SCHEMA (SQLITE)
-- ========================================================

-- 1. Departments Table
CREATE TABLE Department (
    DepartmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    DepartmentName TEXT NOT NULL,
    Building TEXT,
    Floor INTEGER,
    Section TEXT
);

-- Department Phones (Multivalued Attribute)
CREATE TABLE Department_Phone (
    DepartmentID INTEGER,
    Phone TEXT,
    PRIMARY KEY (DepartmentID, Phone),
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID) ON DELETE CASCADE
);

-- 2. Patients Table
CREATE TABLE Patient (
    PatientID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender TEXT,
    BloodType TEXT,
    Street TEXT,
    City TEXT,
    ZipCode TEXT
);

-- Patient Phones (Multivalued Attribute)
CREATE TABLE Patient_Phone (
    PatientID INTEGER,
    Phone TEXT,
    PRIMARY KEY (PatientID, Phone),
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE
);

-- Emergency Contact Table
CREATE TABLE EmergencyContact (
    ContactID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    Name TEXT NOT NULL,
    Relation TEXT NOT NULL,
    Phone TEXT NOT NULL,
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE
);

-- Patient Insurance Table
CREATE TABLE Insurance (
    InsuranceID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    Provider TEXT NOT NULL,
    PolicyNumber TEXT UNIQUE NOT NULL,
    Coverage DECIMAL(5, 2), -- Percentage of coverage e.g., 80.00%
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE
);

-- 3. Doctors Table
CREATE TABLE Doctor (
    DoctorID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Gender TEXT,
    Email TEXT UNIQUE,
    Specialization TEXT,
    Salary DECIMAL(10, 2),
    HireDate DATE,
    Street TEXT,
    City TEXT,
    ZipCode TEXT,
    DepartmentID INTEGER,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID) ON DELETE SET NULL
);

-- Doctor Phones (Multivalued Attribute)
CREATE TABLE Doctor_Phone (
    DoctorID INTEGER,
    Phone TEXT,
    PRIMARY KEY (DoctorID, Phone),
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE CASCADE
);

-- Doctor Schedule Table
CREATE TABLE DoctorSchedule (
    ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
    DoctorID INTEGER NOT NULL,
    DayOfWeek TEXT NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE CASCADE
);

-- 4. Nurses Table
CREATE TABLE Nurse (
    NurseID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Gender TEXT,
    Email TEXT UNIQUE,
    Salary DECIMAL(10, 2),
    HireDate DATE,
    Shift TEXT,
    Street TEXT,
    City TEXT,
    ZipCode TEXT,
    DepartmentID INTEGER,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID) ON DELETE SET NULL
);

-- Nurse Phones (Multivalued Attribute)
CREATE TABLE Nurse_Phone (
    NurseID INTEGER,
    Phone TEXT,
    PRIMARY KEY (NurseID, Phone),
    FOREIGN KEY (NurseID) REFERENCES Nurse(NurseID) ON DELETE CASCADE
);

-- 5. Rooms Table (Linked to Patient via Assigned_To)
CREATE TABLE Room (
    RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoomNumber TEXT UNIQUE NOT NULL,
    RoomType TEXT,
    Floor INTEGER,
    Capacity INTEGER,
    Status TEXT,
    PatientID INTEGER, -- Who is currently occupying the room
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE SET NULL
);

-- Room Assignment History Table
CREATE TABLE RoomAssignment (
    AssignmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoomID INTEGER NOT NULL,
    PatientID INTEGER NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE, -- NULL if patient is still in the room
    FOREIGN KEY (RoomID) REFERENCES Room(RoomID) ON DELETE CASCADE,
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE
);

-- 6. Appointments Table (MODIFIED: Added AppointmentType)
CREATE TABLE Appointment (
    AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    DoctorID INTEGER NOT NULL,
    AppointmentDate DATE NOT NULL,
    AppointmentTime TIME NOT NULL,
    EndTime TIME,
    AppointmentType TEXT, -- NEW: Consultation, FollowUp, Emergency
    Status TEXT DEFAULT 'Pending',
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE CASCADE
);

-- 7. AI_Prediction Table (1:1 with Appointment)
CREATE TABLE AI_Prediction (
    PredictionID INTEGER PRIMARY KEY AUTOINCREMENT,
    AppointmentID INTEGER UNIQUE NOT NULL, -- UNIQUE ensures 1:1 relationship
    Symptoms_Input TEXT NOT NULL,
    Predicted_Disease TEXT,
    Confidence_Score DECIMAL(5, 2), -- e.g., 95.50
    Is_Accurate BOOLEAN, -- Doctor's feedback
    FOREIGN KEY (AppointmentID) REFERENCES Appointment(AppointmentID) ON DELETE CASCADE
);

-- 8. Bills Table (MODIFIED: Added AppointmentID)
CREATE TABLE Bill (
    BillID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    AppointmentID INTEGER, -- NEW: Link Bill to Appointment
    BillDate DATE NOT NULL,
    TotalAmount DECIMAL(10, 2) NOT NULL,
    PaidAmount DECIMAL(10, 2) DEFAULT 0.00,
    PaymentStatus TEXT DEFAULT 'Unpaid',
    PaymentMethod TEXT,
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (AppointmentID) REFERENCES Appointment(AppointmentID) ON DELETE SET NULL
);

-- 9. Medical Records Table (MODIFIED: Added AppointmentID)
CREATE TABLE MedicalRecord (
    RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
    PatientID INTEGER NOT NULL,
    DoctorID INTEGER NOT NULL,
    AppointmentID INTEGER, -- NEW: Link MedicalRecord to Appointment
    Diagnosis TEXT,
    Treatment TEXT,
    VisitDate DATE NOT NULL,
    Notes TEXT,
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE CASCADE,
    FOREIGN KEY (AppointmentID) REFERENCES Appointment(AppointmentID) ON DELETE SET NULL
);

-- MedicalRecord Allergies (Multivalued Attribute)
CREATE TABLE MedicalRecord_Allergy (
    RecordID INTEGER,
    Allergy TEXT,
    PRIMARY KEY (RecordID, Allergy),
    FOREIGN KEY (RecordID) REFERENCES MedicalRecord(RecordID) ON DELETE CASCADE
);

-- Medical Tests Table (MODIFIED: Added DoctorID)
CREATE TABLE MedicalTest (
    TestID INTEGER PRIMARY KEY AUTOINCREMENT,
    RecordID INTEGER NOT NULL,
    DoctorID INTEGER, -- NEW: Doctor who requested the test
    TestName TEXT NOT NULL,
    Result TEXT,
    Unit TEXT,
    TestDate DATE NOT NULL,
    FOREIGN KEY (RecordID) REFERENCES MedicalRecord(RecordID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE SET NULL
);

-- 10. Prescriptions Table
CREATE TABLE Prescription (
    PrescriptionID INTEGER PRIMARY KEY AUTOINCREMENT,
    RecordID INTEGER NOT NULL,
    Date DATE NOT NULL,
    FOREIGN KEY (RecordID) REFERENCES MedicalRecord(RecordID) ON DELETE CASCADE
);

-- 11. Prescription_Item Table (Weak Entity)
CREATE TABLE Prescription_Item (
    PrescriptionID INTEGER NOT NULL,
    MedicineName TEXT NOT NULL,
    Dosage TEXT,
    Duration TEXT,
    PRIMARY KEY (PrescriptionID, MedicineName),
    FOREIGN KEY (PrescriptionID) REFERENCES Prescription(PrescriptionID) ON DELETE CASCADE
);

-- 12. User Authentication Table (MODIFIED: Added IsActive and CreatedAt)
CREATE TABLE User (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    PasswordHash TEXT NOT NULL,
    Role TEXT NOT NULL, -- Admin, Doctor, Nurse, Patient
    DoctorID INTEGER,
    NurseID INTEGER,
    PatientID INTEGER,
    IsActive BOOLEAN DEFAULT 1, -- NEW: User account status
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP, -- NEW: Account creation date
    FOREIGN KEY (DoctorID) REFERENCES Doctor(DoctorID) ON DELETE CASCADE,
    FOREIGN KEY (NurseID) REFERENCES Nurse(NurseID) ON DELETE CASCADE,
    FOREIGN KEY (PatientID) REFERENCES Patient(PatientID) ON DELETE CASCADE
);

-- 13. Audit Log Table
CREATE TABLE AuditLog (
    LogID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER,
    Action TEXT NOT NULL,
    TableName TEXT NOT NULL,
    RecordID INTEGER,
    ActionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE SET NULL
);

--------------------------------------------------------

-- ==========================================
-- INSERTING DATA
-- ==========================================

-- 1. Insert Departments
INSERT INTO Department (DepartmentName, Building, Floor, Section) VALUES
('Cardiology', 'Building A', 3, 'Heart Care'),
('Neurology', 'Building A', 4, 'Brain & Nerves'),
('Pediatrics', 'Building B', 1, 'Child Care'),
('General Surgery', 'Building C', 2, 'Surgery Wing'),
('Orthopedics', 'Building B', 2, 'Bone & Joint');

INSERT INTO Department_Phone (DepartmentID, Phone) VALUES
(1, '19001-Ext301'), (2, '19001-Ext401'), (3, '19001-Ext101'), (4, '19001-Ext201');

-- 2. Insert Patients
INSERT INTO Patient (FirstName, LastName, DateOfBirth, Gender, BloodType, Street, City, ZipCode) VALUES
('Ahmed', 'Mohamed', '1985-04-12', 'Male', 'O+', 'Talaat Harb St', 'Cairo', '11511'),
('Salma', 'Ibrahim', '1992-08-25', 'Female', 'A-', 'Abbas El Akkad', 'Cairo', '11765'),
('Karim', 'Hassan', '2001-11-05', 'Male', 'B+', 'El Haram St', 'Giza', '12511'),
('Mona', 'Tariq', '1978-02-14', 'Female', 'O-', 'Zamalek', 'Cairo', '11211'),
('Youssef', 'Adel', '1995-09-30', 'Male', 'AB+', 'Maadi', 'Cairo', '11431'),
('Nour', 'Sherif', '2010-05-20', 'Female', 'A+', 'Dokki', 'Giza', '12311');

INSERT INTO Patient_Phone (PatientID, Phone) VALUES
(1, '01011112222'), (2, '01122223333'), (3, '01233334444'), (4, '01544445555'), (5, '01055556666');

-- 3. Insert Emergency Contacts
INSERT INTO EmergencyContact (PatientID, Name, Relation, Phone) VALUES
(1, 'Ali Mohamed', 'Brother', '01022224444'),
(4, 'Tariq Hassan', 'Father', '01144448888');

-- 4. Insert Insurance
INSERT INTO Insurance (PatientID, Provider, PolicyNumber, Coverage) VALUES
(3, 'Allianz Care', 'ALZ-998877', 80.00),
(5, 'Bupa Egypt', 'BUP-112233', 100.00);

-- 5. Insert Doctors
INSERT INTO Doctor (FirstName, LastName, Gender, Email, Specialization, Salary, HireDate, Street, City, ZipCode, DepartmentID) VALUES
('Magdy', 'Yacoub', 'Male', 'm.yacoub@hospital.com', 'Cardiologist', 80000.00, '2015-01-01', 'Nile Corniche', 'Aswan', '81511', 1),
('Hisham', 'Sadek', 'Male', 'h.sadek@hospital.com', 'Neurologist', 60000.00, '2018-03-15', 'Makram Ebeid', 'Cairo', '11765', 2),
('Rania', 'Farid', 'Female', 'r.farid@hospital.com', 'Pediatrician', 45000.00, '2020-07-01', 'El Hegaz St', 'Cairo', '11361', 3),
('Tarek', 'Wael', 'Male', 't.wael@hospital.com', 'General Surgeon', 75000.00, '2016-11-20', 'Mohandeseen', 'Giza', '12411', 4),
('Laila', 'Kamal', 'Female', 'l.kamal@hospital.com', 'Orthopedic Surgeon', 55000.00, '2021-02-10', 'Heliopolis', 'Cairo', '11341', 5);

INSERT INTO Doctor_Phone (DoctorID, Phone) VALUES
(1, '01099998888'), (2, '01188887777'), (3, '01277776666'), (4, '01566665555'), (5, '01055554444');

-- 6. Insert Doctor Schedule
INSERT INTO DoctorSchedule (DoctorID, DayOfWeek, StartTime, EndTime) VALUES
(1, 'Monday', '09:00:00', '15:00:00'),
(1, 'Wednesday', '09:00:00', '15:00:00'),
(2, 'Tuesday', '10:00:00', '16:00:00'),
(4, 'Sunday', '08:00:00', '14:00:00');

-- 7. Insert Nurses
INSERT INTO Nurse (FirstName, LastName, Gender, Email, Salary, HireDate, Shift, Street, City, ZipCode, DepartmentID) VALUES
('Heba', 'Sayed', 'Female', 'h.sayed@hospital.com', 15000.00, '2022-01-10', 'Morning', 'Shubra St', 'Cairo', '11231', 1),
('Amr', 'Gamal', 'Male', 'a.gamal@hospital.com', 14500.00, '2021-06-05', 'Night', 'Faisal St', 'Giza', '12555', 2),
('Fatma', 'Ali', 'Female', 'f.ali@hospital.com', 16000.00, '2020-09-12', 'Morning', 'Maadi', 'Cairo', '11431', 3);

INSERT INTO Nurse_Phone (NurseID, Phone) VALUES
(1, '01033332222'), (2, '01144443333'), (3, '01255554444');

-- 8. Insert Rooms
INSERT INTO Room (RoomNumber, RoomType, Floor, Capacity, Status, PatientID) VALUES
('101A', 'ICU', 1, 1, 'Available', NULL),
('201B', 'Private', 2, 1, 'Occupied', 4),
('202B', 'Shared', 2, 2, 'Available', NULL),
('301C', 'Private', 3, 1, 'Maintenance', NULL);

-- 9. Insert Room Assignment History
INSERT INTO RoomAssignment (RoomID, PatientID, StartDate, EndDate) VALUES
(2, 4, '2026-03-12', NULL), -- Currently Occupied
(1, 1, '2026-03-01', '2026-03-05'); -- Past Assignment

-- 10. Insert Appointments (MODIFIED: Added AppointmentType)
INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, AppointmentTime, EndTime, AppointmentType, Status) VALUES
(1, 1, '2026-03-01', '10:00:00', '10:30:00', 'Consultation', 'Completed'),
(2, 2, '2026-03-02', '12:30:00', '13:00:00', 'FollowUp', 'Completed'),
(3, 5, '2026-03-10', '09:00:00', '09:45:00', 'Consultation', 'Completed'),
(4, 4, '2026-03-12', '11:00:00', '12:00:00', 'Emergency', 'Completed'),
(5, 1, '2026-03-15', '14:00:00', '14:30:00', 'Consultation', 'Pending'),
(6, 3, '2026-03-16', '10:15:00', '10:45:00', 'FollowUp', 'Canceled');

-- 11. Insert AI Predictions
INSERT INTO AI_Prediction (AppointmentID, Symptoms_Input, Predicted_Disease, Confidence_Score, Is_Accurate) VALUES
(1, 'Chest pain, shortness of breath, left arm numbness', 'Myocardial Infarction', 94.50, 1),
(2, 'Severe chronic headache, blurred vision, dizziness', 'Migraine', 88.00, 0),
(3, 'Knee pain after running, swelling, inability to straighten leg', 'Meniscus Tear', 91.20, 1),
(4, 'Sharp abdominal pain right side, nausea, fever', 'Food Poisoning', 75.50, 0);

-- 12. Insert Bills (MODIFIED: Linked to AppointmentID)
INSERT INTO Bill (PatientID, AppointmentID, BillDate, TotalAmount, PaidAmount, PaymentStatus, PaymentMethod) VALUES
(1, 1, '2026-03-01', 1500.00, 1500.00, 'Paid', 'Credit Card'),
(2, 2, '2026-03-02', 800.00, 400.00, 'Partial', 'Cash'),
(3, 3, '2026-03-10', 1200.00, 1200.00, 'Paid', 'Insurance'),
(4, 4, '2026-03-12', 15000.00, 0.00, 'Unpaid', NULL);

-- 13. Insert Medical Records & Allergies (MODIFIED: Linked to AppointmentID)
INSERT INTO MedicalRecord (PatientID, DoctorID, AppointmentID, Diagnosis, Treatment, VisitDate, Notes) VALUES
(1, 1, 1, 'Mild Angina', 'Rest and medication, avoid stress', '2026-03-01', 'Patient needs follow-up in 2 weeks.'),
(2, 2, 2, 'High Blood Pressure', 'Prescribed antihypertensive drugs', '2026-03-02', 'Monitor blood pressure daily.'),
(3, 5, 3, 'Meniscus Tear', 'Physical therapy and knee brace', '2026-03-10', 'Surgery might be required if no improvement.'),
(4, 4, 4, 'Appendicitis', 'Immediate surgical removal (Appendectomy)', '2026-03-12', 'Patient admitted to room 201B post-surgery.');

INSERT INTO MedicalRecord_Allergy (RecordID, Allergy) VALUES
(1, 'Penicillin'), (2, 'Peanuts'), (4, 'Latex');

-- 14. Insert Medical Tests (MODIFIED: Added DoctorID)
INSERT INTO MedicalTest (RecordID, DoctorID, TestName, Result, Unit, TestDate) VALUES
(1, 1, 'ECG', 'Normal Sinus Rhythm', 'N/A', '2026-03-01'),
(2, 2, 'Blood Pressure', '140/90', 'mmHg', '2026-03-02'),
(4, 4, 'CBC (WBC Count)', '15,000', 'cells/mcL', '2026-03-12');

-- 15. Insert Prescriptions & Items
INSERT INTO Prescription (RecordID, Date) VALUES
(1, '2026-03-01'), (2, '2026-03-02'), (3, '2026-03-10');

INSERT INTO Prescription_Item (PrescriptionID, MedicineName, Dosage, Duration) VALUES
(1, 'Aspirin', '75mg once daily', '30 Days'),
(1, 'Nitroglycerin', '0.4mg sublingual as needed', 'Ongoing'),
(2, 'Lisinopril', '10mg once daily', '60 Days'),
(3, 'Ibuprofen', '400mg every 8 hours', '7 Days');

-- 16. Insert Users (Auth System Setup - SECURE)
INSERT INTO User (Username, PasswordHash, Role, DoctorID, NurseID, PatientID, IsActive) VALUES
('admin', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Admin', NULL, NULL, NULL, 1),
('dr.magdy', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Doctor', 1, NULL, NULL, 1),
('dr.hisham', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Doctor', 2, NULL, NULL, 1),
('nurse.heba', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Nurse', NULL, 1, NULL, 1),
('pt.ahmed', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Patient', NULL, NULL, 1, 1),
('pt.salma', 'scrypt:32768:8:1$tp9M8SzU6dVHuBwC$249f98bb2bc47868424d7d4de4e14576a59749637f32776f9c87493b32000a97c5aa74daf046ed84d93e7a17d544978d42c361353317c7430176e0a2205ed0ca', 'Patient', NULL, NULL, 2, 1);

-- 17. Insert Audit Logs (NEW)
INSERT INTO AuditLog (UserID, Action, TableName, RecordID) VALUES
(1, 'System Initialized', 'Database', NULL),
(2, 'Created Medical Record', 'MedicalRecord', 1),
(3, 'Updated Appointment Status', 'Appointment', 2);