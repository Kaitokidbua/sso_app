import sqlite3

DB_PATH = "sso_advisor.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS benefit_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    section TEXT,
    plan_no INTEGER,
    data_type TEXT,
    detail TEXT,
    min_months_paid INTEGER,
    max_months_paid INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS contribution_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    year INTEGER,
    start_month INTEGER,
    end_month INTEGER,

    employee_rate REAL,
    employer_rate REAL,
    government_rate REAL,
            
    salary_floor REAL,
    salary_ceiling REAL,

    employee_fixed REAL,
    government_fixed REAL,
    salary_base REAL,
            
    rule_type TEXT,

    plan_no INTEGER,
            
    plan1_employee_fixed REAL,
    plan2_employee_fixed REAL,
    plan3_employee_fixed REAL,
    plan1_government_fixed REAL,
    plan2_government_fixed REAL,
    plan3_government_fixed REAL,
            
    plan1_old_age_saving_amount REAL,
    plan2_old_age_saving_amount REAL,
    plan3_old_age_saving_amount REAL,

    description TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS benefit_eligibility_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    section TEXT,
    plan_no INTEGER,
    is_covered INTEGER,
    min_months_paid INTEGER,
    window_months INTEGER,
    min_age INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS benefit_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benefit_type TEXT,
    section TEXT,
    parameter_name TEXT,
    parameter_value REAL,
    description TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT,
    description TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS section_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    plan_no INTEGER,
    title TEXT,
    target_group TEXT,
    contribution_text TEXT,
    rights_summary TEXT,
    old_age_text TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS benefit_checklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    plan_no INTEGER,
    category TEXT,
    has_benefit INTEGER,
    display_text TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_type TEXT,
    section TEXT,
    plan_no INTEGER,
    user_status TEXT,
    priority TEXT,
    recommendation TEXT,
    message_type TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS section_highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT,
    plan_no INTEGER,
    detail TEXT
)
""")

conn.commit()
conn.close()

print("Database initialized successfully")