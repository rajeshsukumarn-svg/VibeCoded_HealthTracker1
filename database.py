import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "health_data.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # enforce FK constraints
    conn.execute("PRAGMA journal_mode = WAL")  # concurrent reads, safer writes
    conn.execute("PRAGMA busy_timeout = 5000") # wait up to 5s on lock instead of crashing
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                blood_type TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                recorded_at TEXT NOT NULL,
                systolic INTEGER,
                diastolic INTEGER,
                heart_rate INTEGER,
                glucose REAL,
                weight REAL,
                temperature REAL,
                spo2 INTEGER,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                start_date TEXT,
                end_date TEXT,
                active INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS med_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medication_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                taken_at TEXT NOT NULL,
                taken INTEGER DEFAULT 1,
                FOREIGN KEY (medication_id) REFERENCES medications(id) ON DELETE CASCADE,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );

            -- Indexes: every query filters by patient_id; vitals/med_logs also sort by date
            CREATE INDEX IF NOT EXISTS idx_vitals_patient
                ON vitals(patient_id, recorded_at DESC);

            CREATE INDEX IF NOT EXISTS idx_meds_patient
                ON medications(patient_id, active);

            CREATE INDEX IF NOT EXISTS idx_medlogs_patient
                ON med_logs(patient_id, taken_at DESC);

            CREATE INDEX IF NOT EXISTS idx_medlogs_medication
                ON med_logs(medication_id);
        """)


def get_patients():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM patients ORDER BY name").fetchall()


def add_patient(name, age, gender, blood_type):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO patients (name, age, gender, blood_type) VALUES (?,?,?,?)",
            (name, age, gender, blood_type),
        )


def delete_patient(patient_id):
    with get_conn() as conn:
        # ON DELETE CASCADE (+ PRAGMA foreign_keys=ON) removes child rows automatically.
        # Explicit deletes kept as belt-and-suspenders for DBs created before the CASCADE migration.
        conn.execute("DELETE FROM med_logs WHERE patient_id=?", (patient_id,))
        conn.execute("DELETE FROM medications WHERE patient_id=?", (patient_id,))
        conn.execute("DELETE FROM vitals WHERE patient_id=?", (patient_id,))
        conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))


def add_vitals(patient_id, systolic, diastolic, heart_rate, glucose, weight, temperature, spo2, notes, recorded_at=None):
    ts = recorded_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO vitals
               (patient_id, recorded_at, systolic, diastolic, heart_rate, glucose, weight, temperature, spo2, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (patient_id, ts, systolic or None, diastolic or None, heart_rate or None,
             glucose or None, weight or None, temperature or None, spo2 or None, notes),
        )


def get_vitals(patient_id, limit=100):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT ?",
            (patient_id, limit),
        ).fetchall()


def get_latest_vitals(patient_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 1",
            (patient_id,),
        ).fetchone()


def add_medication(patient_id, name, dosage, frequency, start_date, end_date, notes):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO medications (patient_id, name, dosage, frequency, start_date, end_date, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (patient_id, name, dosage, frequency, start_date, end_date, notes),
        )


def get_medications(patient_id, active_only=True):
    with get_conn() as conn:
        q = "SELECT * FROM medications WHERE patient_id=?"
        if active_only:
            q += " AND active=1"
        q += " ORDER BY name"
        return conn.execute(q, (patient_id,)).fetchall()


def toggle_medication(med_id, active):
    with get_conn() as conn:
        conn.execute("UPDATE medications SET active=? WHERE id=?", (active, med_id))


def log_medication_taken(medication_id, patient_id, taken=True):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO med_logs (medication_id, patient_id, taken_at, taken) VALUES (?,?,?,?)",
            (medication_id, patient_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(taken)),
        )


def get_med_logs_today(patient_id):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        return conn.execute(
            """SELECT ml.*, m.name, m.dosage, m.frequency
               FROM med_logs ml JOIN medications m ON ml.medication_id=m.id
               WHERE ml.patient_id=? AND ml.taken_at LIKE ?
               ORDER BY ml.taken_at DESC""",
            (patient_id, f"{today}%"),
        ).fetchall()


def seed_demo_data():
    patients = get_patients()
    if patients:
        return
    add_patient("Arjun Mehta", 62, "Male", "A+")
    add_patient("Priya Sharma", 38, "Female", "O+")
    add_patient("Rajesh Kumar", 45, "Male", "B+")

    patients = get_patients()
    p_arjun  = patients[0]["id"]
    p_priya  = patients[1]["id"]
    p_rajesh = patients[2]["id"]

    import random
    from datetime import timedelta
    base = datetime.now()

    # Rajesh — hypertension + diabetes tendency
    for i in range(30):
        dt = (base - timedelta(days=29 - i)).strftime("%Y-%m-%d %H:%M:%S")
        add_vitals(p_rajesh, random.randint(125, 148), random.randint(82, 96),
                   random.randint(68, 88), random.uniform(105, 148),
                   random.uniform(78, 82), random.uniform(36.5, 37.1),
                   random.randint(96, 99), "", dt)

    add_medication(p_rajesh, "Metformin", "500mg", "Twice daily",
                   "2026-01-01", "2026-12-31", "Take with meals")
    add_medication(p_rajesh, "Amlodipine", "5mg", "Once daily",
                   "2026-01-01", "2026-12-31", "For blood pressure")
    add_medication(p_rajesh, "Aspirin", "75mg", "Once daily",
                   "2026-01-01", "2026-12-31", "After breakfast")

    # Priya — healthy range, mild thyroid
    for i in range(30):
        dt = (base - timedelta(days=29 - i)).strftime("%Y-%m-%d %H:%M:%S")
        add_vitals(p_priya, random.randint(108, 122), random.randint(70, 80),
                   random.randint(62, 78), random.uniform(82, 105),
                   random.uniform(58, 61), random.uniform(36.4, 37.0),
                   random.randint(97, 100), "", dt)

    add_medication(p_priya, "Levothyroxine", "50mcg", "Once daily",
                   "2026-01-01", "2026-12-31", "Take on empty stomach")
    add_medication(p_priya, "Vitamin D3", "1000IU", "Once daily",
                   "2026-01-01", "2026-12-31", "With breakfast")

    # Arjun — senior, higher BP, post-cardiac
    for i in range(30):
        dt = (base - timedelta(days=29 - i)).strftime("%Y-%m-%d %H:%M:%S")
        add_vitals(p_arjun, random.randint(135, 158), random.randint(85, 98),
                   random.randint(58, 75), random.uniform(110, 160),
                   random.uniform(68, 72), random.uniform(36.3, 37.3),
                   random.randint(94, 98), "", dt)

    add_medication(p_arjun, "Atorvastatin", "40mg", "Once daily",
                   "2026-01-01", "2026-12-31", "At bedtime")
    add_medication(p_arjun, "Ramipril", "5mg", "Once daily",
                   "2026-01-01", "2026-12-31", "For blood pressure")
    add_medication(p_arjun, "Clopidogrel", "75mg", "Once daily",
                   "2026-01-01", "2026-12-31", "After breakfast")
    add_medication(p_arjun, "Metoprolol", "25mg", "Twice daily",
                   "2026-01-01", "2026-12-31", "For heart rate control")
