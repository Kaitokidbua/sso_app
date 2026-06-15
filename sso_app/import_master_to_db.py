import json
import sqlite3

DB_PATH = "sso_advisor.db"
JSON_PATH = "sso_master.json"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

seen_benefits = set()

def insert_benefit(category, section, plan_no, data_type, detail, min_months=None, max_months=None):
    if not detail:
        return

    key = (
        category,
        section,
        plan_no,
        data_type,
        detail,
        min_months,
        max_months
    )

    if key in seen_benefits:
        return

    seen_benefits.add(key)

    cur.execute("""
    INSERT INTO benefit_details (
        category, section, plan_no, data_type, detail,
        min_months_paid, max_months_paid
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        category,
        section,
        plan_no,
        data_type,
        detail,
        min_months,
        max_months
    ))

for category, sections in data.get("benefit_details", {}).items():
    for section, content in sections.items():

        for item in content.get("benefits", []):
            insert_benefit(category, section, None, "benefit", item)

        for item in content.get("conditions", []):
            insert_benefit(category, section, None, "condition", item)

        for item in content.get("notes", []):
            insert_benefit(category, section, None, "note", item)

        for item in content.get("conditional_benefits", []):
            insert_benefit(
                category,
                section,
                None,
                "benefit",
                item.get("text"),
                item.get("min_months_paid"),
                item.get("max_months_paid")
            )

        for plan_no, items in content.get("benefits_by_plan", {}).items():
            for item in items:
                insert_benefit(
                    category,
                    section,
                    int(plan_no),
                    "benefit",
                    item
                )

        for plan_no, items in content.get("conditions_by_plan", {}).items():
            for item in items:
                insert_benefit(
                    category,
                    section,
                    int(plan_no),
                    "condition",
                    item
                )

        for plan_no, items in content.get("notes_by_plan", {}).items():
            for item in items:
                insert_benefit(
                    category,
                    section,
                    int(plan_no),
                    "note",
                    item
                )

        for plan_no, items in content.get("conditional_benefits_by_plan", {}).items():
            for item in items:
                insert_benefit(
                    category,
                    section,
                    int(plan_no),
                    "benefit",
                    item.get("text"),
                    item.get("min_months_paid"),
                    item.get("max_months_paid")
                )

def insert_contribution_rule(section, year, p, rule_type=None):
    plan_costs = p.get("plan_costs", {})
    government_plan_costs = p.get("government_plan_costs", {})

    cur.execute("""
    INSERT INTO contribution_rules (
        section,
        year,
        start_month,
        end_month,
        employee_rate,
        employer_rate,
        government_rate,
        salary_floor,
        salary_ceiling,
        employee_fixed,
        government_fixed,
        salary_base,
        plan_no,
        plan1_employee_fixed,
        plan2_employee_fixed,
        plan3_employee_fixed,
        plan1_government_fixed,
        plan2_government_fixed,
        plan3_government_fixed,
        plan1_old_age_saving_amount,
        plan2_old_age_saving_amount,
        plan3_old_age_saving_amount,
        description,
        rule_type
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        section,
        int(year),
        p.get("start_month"),
        p.get("end_month"),
        p.get("employee_rate"),
        p.get("employer_rate"),
        p.get("government_rate"),
        p.get("salary_floor"),
        p.get("salary_ceiling"),
        p.get("employee_fixed_contribution"),
        p.get("government_fixed_contribution"),
        p.get("salary_base"),
        p.get("plan_no"),
        plan_costs.get("1"),
        plan_costs.get("2"),
        plan_costs.get("3"),
        government_plan_costs.get("1"),
        government_plan_costs.get("2"),
        government_plan_costs.get("3"),
        m40_old_age_saving.get(1, 0) if section == "m40" else None,
        m40_old_age_saving.get(2, 0) if section == "m40" else None,
        m40_old_age_saving.get(3, 0) if section == "m40" else None,
        p.get("description"),
        rule_type
    ))

rules = data.get("contribution_rules", {})

m40_options = data.get("m40", {}).get("options", [])

m40_old_age_saving = {}

for option in m40_options:
    m40_old_age_saving[option["plan"]] = option.get(
        "pension_saving_per_month",
        0
    )

for section, sec_data in rules.items():

    years = sec_data.get("years", {})

    for year, periods in years.items():
        for p in periods:
            insert_contribution_rule(
                section=section,
                year=int(year),
                p=p,
                rule_type=None
            )

    for p in sec_data.get("default_before_2559", []):
        insert_contribution_rule(
            section=section,
            year=2558,
            p=p,
            rule_type="default_before_2559"
        )

    for p in sec_data.get("default_after_2575", []):
        insert_contribution_rule(
            section=section,
            year=2576,
            p=p,
            rule_type="default_after_2575"
        )    

eligibility_rules = [
    ("กรณีประสบอันตรายหรือเจ็บป่วย", "m33", None, 1, 3, 15, None),
    ("กรณีคลอดบุตร", "m33", None, 1, 5, 15, None),
    ("กรณีทุพพลภาพ", "m33", None, 1, 3, 15, None),
    ("กรณีเสียชีวิต", "m33", None, 1, 1, 6, None),
    ("กรณีสงเคราะห์บุตร", "m33", None, 1, 12, 36, None),
    ("กรณีชราภาพ", "m33", None, 1, None, None, 55),
    ("กรณีว่างงาน", "m33", None, 1, 6, 15, None),

    ("กรณีประสบอันตรายหรือเจ็บป่วย", "m39", None, 1, 3, 15, None),
    ("กรณีคลอดบุตร", "m39", None, 1, 5, 15, None),
    ("กรณีทุพพลภาพ", "m39", None, 1, 3, 15, None),
    ("กรณีเสียชีวิต", "m39", None, 1, 1, 6, None),
    ("กรณีสงเคราะห์บุตร", "m39", None, 1, 12, 36, None),
    ("กรณีชราภาพ", "m39", None, 1, None, None, 55),
    ("กรณีว่างงาน", "m39", None, 0, None, None, None),

    ("กรณีประสบอันตรายหรือเจ็บป่วย", "m40", 1, 1, 3, 4, None),
    ("กรณีประสบอันตรายหรือเจ็บป่วย", "m40", 2, 1, 3, 4, None),
    ("กรณีประสบอันตรายหรือเจ็บป่วย", "m40", 3, 1, 3, 4, None),
    ("กรณีคลอดบุตร", "m40", 1, 0, None, None, None),
    ("กรณีคลอดบุตร", "m40", 2, 0, None, None, None),
    ("กรณีคลอดบุตร", "m40", 3, 0, None, None, None),
    ("กรณีทุพพลภาพ", "m40", 1, 1, 6, 10, None),
    ("กรณีทุพพลภาพ", "m40", 2, 1, 6, 10, None),
    ("กรณีทุพพลภาพ", "m40", 3, 1, 6, 10, None),
    ("กรณีเสียชีวิต", "m40", 1, 1, 6, 12, None),
    ("กรณีเสียชีวิต", "m40", 2, 1, 6, 12, None),
    ("กรณีเสียชีวิต", "m40", 3, 1, 6, 12, None),
    ("กรณีสงเคราะห์บุตร", "m40", 1, 0, None, None, None),
    ("กรณีสงเคราะห์บุตร", "m40", 2, 0, None, None, None),
    ("กรณีสงเคราะห์บุตร", "m40", 3, 1, 24, 36, None),
    ("กรณีชราภาพ", "m40", 1, 0, None, None, None),
    ("กรณีชราภาพ", "m40", 2, 1, None, None, 60),
    ("กรณีชราภาพ", "m40", 3, 1, None, None, 60),
    ("กรณีว่างงาน", "m40", 1, 0, None, None, None),
    ("กรณีว่างงาน", "m40", 2, 0, None, None, None),
    ("กรณีว่างงาน", "m40", 3, 0, None, None, None)
]

for row in eligibility_rules:
    cur.execute("""
    INSERT INTO benefit_eligibility_rules (
        category, section, plan_no, is_covered,
        min_months_paid, window_months, min_age
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

benefit_parameters = [
    ("old_age", None, "pension_base_rate", 0.20,
     "อัตราบำนาญเริ่มต้น 20%"),

    ("old_age", None, "pension_increment_rate", 0.015,
     "อัตราเพิ่มบำนาญ 1.5%"),

    ("old_age", None, "increment_period_months", 12,
     "จำนวนเดือนต่อการเพิ่มอัตราบำนาญ"),

    ("old_age", "m40", "bonus_amount", 10000,
     "โบนัสชราภาพ ม.40 ทางเลือก 3"),
]

for row in benefit_parameters:
    cur.execute("""
    INSERT INTO benefit_parameters (
        benefit_type, section, parameter_name, parameter_value, description
    )
    VALUES (?, ?, ?, ?, ?)
    """, row)

app_settings_rows = [
    ("default_start_salary", "12000", "เงินเดือนเริ่มต้น default"),
    ("default_current_salary", "15000", "เงินเดือนปัจจุบัน default"),
    ("default_start_year", "2560", "ปีเริ่มส่งสมทบ default"),
    ("default_age", "30", "อายุปัจจุบัน default"),
    ("default_current_year", "2568", "ปีปัจจุบัน default"),
    ("default_current_month", "1", "เดือนปัจจุบัน default"),
    ("default_retire_age", "60", "อายุเกษียณ default"),
    ("default_salary_growth", "3.0", "อัตราเงินเดือนเพิ่มเฉลี่ยต่อปี default"),
    ("default_extra_saving_m40", "0", "เงินออมเพิ่มเริ่มต้น ม.40"),
    ("max_extra_saving_m40", "1000", "เงินออมเพิ่มสูงสุด ม.40 ชราภาพต่อเดือน"),
    ("default_target_monthly_pension", "10000", "เป้าหมายบำนาญรายเดือน default"),
    ("default_target_lump_sum", "100000", "เป้าหมายบำเหน็จเงินก้อน default"),
]

for row in app_settings_rows:
    cur.execute("""
    INSERT INTO app_settings (setting_key, setting_value, description)
    VALUES (?, ?, ?)
    """, row)

section_summary_rows = [
    ("m33", None, "ม.33", "ลูกจ้างประจำ", "5% ของค่าจ้าง ฐาน 1,650–15,000 บาท", "7 กรณี: เจ็บป่วย, คลอดบุตร, ทุพพลภาพ, เสียชีวิต, สงเคราะห์บุตร, ชราภาพ, ว่างงาน", "บำเหน็จ/บำนาญ"),
    ("m39", None, "ม.39", "อดีตลูกจ้าง ม.33", "432 บาท/เดือน", "6 กรณี: เจ็บป่วย, คลอดบุตร, ทุพพลภาพ, เสียชีวิต, สงเคราะห์บุตร, ชราภาพ", "บำเหน็จ/บำนาญ"),
    ("m40", 1, "ม.40 ทางเลือก 1", "อาชีพอิสระ", "70 บาท/เดือน", "3 กรณี: เจ็บป่วย, ทุพพลภาพ, เสียชีวิต", "ไม่มี"),
    ("m40", 2, "ม.40 ทางเลือก 2", "อาชีพอิสระ", "100 บาท/เดือน", "4 กรณี: เจ็บป่วย, ทุพพลภาพ, เสียชีวิต, ชราภาพ", "บำเหน็จ"),
    ("m40", 3, "ม.40 ทางเลือก 3", "อาชีพอิสระ", "300 บาท/เดือน", "5 กรณี: เจ็บป่วย, ทุพพลภาพ, เสียชีวิต, สงเคราะห์บุตร, ชราภาพ", "บำเหน็จ"),
]

for row in section_summary_rows:
    cur.execute("""
    INSERT INTO section_summary (
        section, plan_no, title, target_group,
        contribution_text, rights_summary, old_age_text
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

checklist_rows = [
    ("m33", None, "เจ็บป่วย/อุบัติเหตุ", 1, "✅"),
    ("m33", None, "คลอดบุตร", 1, "✅"),
    ("m33", None, "ทุพพลภาพ", 1, "✅"),
    ("m33", None, "เสียชีวิต", 1, "✅"),
    ("m33", None, "สงเคราะห์บุตร", 1, "✅"),
    ("m33", None, "ชราภาพ", 1, "✅ บำเหน็จ/บำนาญ"),
    ("m33", None, "ว่างงาน", 1, "✅"),

    ("m39", None, "เจ็บป่วย/อุบัติเหตุ", 1, "✅"),
    ("m39", None, "คลอดบุตร", 1, "✅"),
    ("m39", None, "ทุพพลภาพ", 1, "✅"),
    ("m39", None, "เสียชีวิต", 1, "✅"),
    ("m39", None, "สงเคราะห์บุตร", 1, "✅"),
    ("m39", None, "ชราภาพ", 1, "✅ บำเหน็จ/บำนาญ"),
    ("m39", None, "ว่างงาน", 0, "❌"),

    ("m40", 1, "เจ็บป่วย/อุบัติเหตุ", 1, "✅"),
    ("m40", 1, "คลอดบุตร", 0, "❌"),
    ("m40", 1, "ทุพพลภาพ", 1, "✅"),
    ("m40", 1, "เสียชีวิต", 1, "✅"),
    ("m40", 1, "สงเคราะห์บุตร", 0, "❌"),
    ("m40", 1, "ชราภาพ", 0, "❌"),
    ("m40", 1, "ว่างงาน", 0, "❌"),

    ("m40", 2, "เจ็บป่วย/อุบัติเหตุ", 1, "✅"),
    ("m40", 2, "คลอดบุตร", 0, "❌"),
    ("m40", 2, "ทุพพลภาพ", 1, "✅"),
    ("m40", 2, "เสียชีวิต", 1, "✅"),
    ("m40", 2, "สงเคราะห์บุตร", 0, "❌"),
    ("m40", 2, "ชราภาพ", 1, "✅ บำเหน็จ"),
    ("m40", 2, "ว่างงาน", 0, "❌"),

    ("m40", 3, "เจ็บป่วย/อุบัติเหตุ", 1, "✅"),
    ("m40", 3, "คลอดบุตร", 0, "❌"),
    ("m40", 3, "ทุพพลภาพ", 1, "✅"),
    ("m40", 3, "เสียชีวิต", 1, "✅"),
    ("m40", 3, "สงเคราะห์บุตร", 1, "✅"),
    ("m40", 3, "ชราภาพ", 1, "✅ บำเหน็จ"),
    ("m40", 3, "ว่างงาน", 0, "❌"),
]

for row in checklist_rows:
    cur.execute("""
    INSERT INTO benefit_checklist (
        section, plan_no, category, has_benefit, display_text
    )
    VALUES (?, ?, ?, ?, ?)
    """, row)

recommendation_rows = [
    ("section", "m33", None, None, None, "เหมาะสำหรับลูกจ้างประจำที่มีนายจ้าง", "success"),
    ("section", "m39", None, None, None, "เหมาะสำหรับอดีตลูกจ้าง ม.33 ที่ออกจากงานแล้ว แต่ต้องการรักษาสิทธิประกันสังคม", "info"),
    ("section", "m40", 1, None, None, "เหมาะสำหรับอาชีพอิสระที่ต้องการจ่ายน้อย และเน้นความคุ้มครองพื้นฐาน", "warning"),
    ("section", "m40", 2, None, None, "เหมาะสำหรับอาชีพอิสระที่ต้องการมีเงินชราภาพแบบบำเหน็จ", "info"),
    ("section", "m40", 3, None, None, "เหมาะสำหรับอาชีพอิสระที่ต้องการความคุ้มครองมากที่สุดใน ม.40", "success"),
    ("profile", None, None, "เป็นลูกจ้างประจำ", None, "แนะนำ: มาตรา 33 เพราะคุ้มครองครบที่สุด มีนายจ้างสมทบ และมีสิทธิว่างงาน", "success"),
    ("profile", None, None, "เคยเป็น ม.33 และออกจากงานแล้ว", None, "แนะนำ: มาตรา 39 หากยังอยู่ในเงื่อนไขสมัคร เพราะช่วยรักษาสิทธิหลักและสิทธิชราภาพต่อเนื่อง", "success"),
    ("profile", None, None, "เป็นอาชีพอิสระ", "จ่ายน้อย", "แนะนำ: มาตรา 40 ทางเลือก 1 เพราะเงินสมทบต่ำที่สุด", "success"),
    ("profile", None, None, "เป็นอาชีพอิสระ", "มีเงินชราภาพ", "แนะนำ: มาตรา 40 ทางเลือก 2 หรือ 3", "success"),
    ("profile", None, None, "เป็นอาชีพอิสระ", "มีสงเคราะห์บุตร", "แนะนำ: มาตรา 40 ทางเลือก 3 เพราะเป็นทางเลือกเดียวของ ม.40 ที่มีสิทธิสงเคราะห์บุตร", "success"),
    ("profile", None, None, "เป็นอาชีพอิสระ", "คุ้มครองครบ", "แนะนำ: มาตรา 40 ทางเลือก 3 เพราะคุ้มครองมากที่สุดในกลุ่ม ม.40", "success"),
    ("profile", None, None, "เป็นอาชีพอิสระ", "มีสิทธิว่างงาน", "อาชีพอิสระไม่มีสิทธิว่างงานใน ม.40 หากต้องการสิทธิว่างงานต้องเป็น ม.33", "warning"),
]

for row in recommendation_rows:
    cur.execute("""
    INSERT INTO recommendations (
        recommendation_type, section, plan_no, user_status, priority,
        recommendation, message_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, row)

highlight_rows = [
    ("m33", None, "ได้รับความคุ้มครองครบที่สุด"),
    ("m33", None, "มีนายจ้างสมทบ"),
    ("m33", None, "มีสิทธิว่างงาน"),
    ("m33", None, "มีบำเหน็จหรือบำนาญชราภาพ"),

    ("m39", None, "รักษาสิทธิจาก ม.33 ต่อเนื่อง"),
    ("m39", None, "มีบำเหน็จหรือบำนาญชราภาพ"),
    ("m39", None, "เหมาะกับคนออกจากงานประจำแล้ว"),

    ("m40", 1, "จ่ายเงินสมทบน้อยที่สุด"),
    ("m40", 1, "เหมาะกับผู้เริ่มต้นสมัคร ม.40"),
    ("m40", 1, "ไม่มีสิทธิชราภาพและสงเคราะห์บุตร"),

    ("m40", 2, "มีสิทธิชราภาพแบบเงินก้อน"),
    ("m40", 2, "จ่ายไม่สูงมาก"),
    ("m40", 2, "เหมาะกับผู้ต้องการเริ่มสะสมเงินชราภาพ"),

    ("m40", 3, "คุ้มครองมากที่สุดใน ม.40"),
    ("m40", 3, "มีสิทธิสงเคราะห์บุตร"),
    ("m40", 3, "มีสิทธิชราภาพแบบเงินก้อน"),
]

for row in highlight_rows:
    cur.execute("""
    INSERT INTO section_highlights (
        section, plan_no, detail
    )
    VALUES (?, ?, ?)
    """, row)

conn.commit()
conn.close()

print("Imported master data successfully")