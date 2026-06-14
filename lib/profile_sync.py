"""
Bridge เชื่อม profile ของบัว <-> ของเพื่อน
- หน้าบัว เก็บ: mattra, m40_choice, salary, start_year_be, age, retire_age, extra_saving_m40
- หน้าเพื่อน อ่าน: section (m33/m39/m40), plan_no, current_salary, start_salary,
                  start_year, age, retire_age, extra_saving_m40
                  + ตัว durable: app_section, app_m40_plan, app_retire_age

เรียก sync_profile() ทุกครั้งหลัง login / หลังบันทึกข้อมูล
แล้วหน้าเพื่อนจะอ่านข้อมูลเดียวกันได้ทันที โดยไม่ต้องแก้โค้ดเพื่อน
"""
import streamlit as st

_MATTRA_TO_SECTION = {"33": "m33", "39": "m39", "40": "m40"}


def sync_profile():
    """มิเรอร์ค่าจาก profile ของบัว -> เป็น key ที่หน้าเพื่อนอ่าน (ใน profile เดียวกัน)."""
    p = st.session_state.get("profile")
    if not p:
        return

    section = _MATTRA_TO_SECTION.get(str(p.get("mattra", "33")), "m33")
    plan_no = int(p.get("m40_choice", 1) or 1)
    salary = float(p.get("salary", 15000) or 15000)
    start_year = int(p.get("start_year_be", 2560) or 2560)
    age = int(p.get("age", 30) or 30)
    retire_age = int(p.get("retire_age", 55) or 55)
    extra = float(p.get("extra_saving_m40", 0) or 0)

    # --- key ที่หน้าเพื่อนอ่าน ---
    p["section"] = section
    p["plan_no"] = plan_no
    p["current_salary"] = salary
    p.setdefault("start_salary", salary)   # บัวไม่มี start_salary -> ใช้เท่าปัจจุบัน (แก้ได้ในหน้าเกษียณ)
    p["start_year"] = start_year
    p["age"] = age
    p["retire_age"] = retire_age
    p["extra_saving_m40"] = extra

    # --- durable top-level keys ที่หน้าเพื่อนใช้ ---
    st.session_state["app_section"] = section
    st.session_state["app_m40_plan"] = plan_no
    st.session_state["app_retire_age"] = retire_age
    st.session_state["profile"] = p
