"""
หน้า 1.2 — แก้ไขข้อมูลสมาชิก
กรอกข้อมูลละเอียด (ใช้สำหรับวางแผนเกษียณ/บำนาญ) ครั้งเดียว
-> บันทึกลง session + DB -> ทุกหน้าดึงไปใช้
"""
import streamlit as st
from lib.auth import require_login, get_profile, update_profile
from lib.constants import (MATTRA_OPTIONS, M40_CHOICES, GENDER_OPTIONS,
                           PROVINCES, MONTHS_TH, DEFAULT_PROFILE)

require_login()
prof = {**DEFAULT_PROFILE, **get_profile()}

st.title("📝 แก้ไขข้อมูลสมาชิก")
st.caption("กรอกข้อมูลเพื่อวางแผน — กรอกที่นี่ครั้งเดียว ทุกหน้าจะใช้ข้อมูลชุดนี้")

with st.form("member_form"):
    # ---------- ข้อมูลทั่วไป ----------
    st.subheader("ข้อมูลทั่วไป")
    g1, g2, g3 = st.columns(3)
    name   = g1.text_input("ชื่อ-นามสกุล", prof["full_name"])
    gender = g2.selectbox("เพศ", GENDER_OPTIONS,
                          index=GENDER_OPTIONS.index(prof["gender"])
                          if prof["gender"] in GENDER_OPTIONS else 2)
    prov   = g3.selectbox("จังหวัด", PROVINCES,
                          index=PROVINCES.index(prof["province"])
                          if prof["province"] in PROVINCES else 0)

    # ---------- สถานะประกันสังคม ----------
    st.subheader("สถานะประกันสังคม")
    c1, c2 = st.columns(2)
    mattra = c1.selectbox("มาตราประกันสังคม", list(MATTRA_OPTIONS.keys()),
                          index=list(MATTRA_OPTIONS.keys()).index(prof["mattra"]),
                          format_func=lambda k: MATTRA_OPTIONS[k])
    m40 = c2.selectbox("เลือกทางเลือก ม.40", list(M40_CHOICES.keys()),
                       index=list(M40_CHOICES.keys()).index(prof["m40_choice"]),
                       format_func=lambda k: M40_CHOICES[k],
                       help="ใช้เฉพาะผู้ประกันตนมาตรา 40")

    c3, c4 = st.columns(2)
    age    = c3.number_input("อายุปัจจุบัน", 15, 80, int(prof["age"]))
    retire = c4.number_input("อายุที่ต้องการเกษียณ", 50, 80, int(prof["retire_age"]))

    c5, c6 = st.columns(2)
    year   = c5.number_input("ปี พ.ศ. ที่เริ่มคำนวณ", 2560, 2600,
                             int(prof["start_year_be"]))
    month  = c6.selectbox("เดือนที่เริ่มคำนวณ", list(range(1, 13)),
                          index=int(prof["start_month"]) - 1,
                          format_func=lambda m: MONTHS_TH[m])

    months = st.number_input("จำนวนเดือนที่ส่งเงินสมทบมาแล้ว", 0, 600,
                             int(prof["months_contributed"]),
                             help="ใช้ประเมินบำเหน็จ/บำนาญ และโบนัส ม.40 "
                                  "ให้รวมกับเดือนที่จะส่งในอนาคต")

    # ---------- การเงิน ----------
    st.subheader("ข้อมูลการเงิน")
    f1, f2 = st.columns(2)
    salary = f1.number_input("เงินเดือนปัจจุบัน", 0, 200000,
                             int(prof["salary"]), step=500)
    f1.caption(f"💰 {salary:,.2f} บาท")
    growth = f2.number_input("เงินเดือนเพิ่มเฉลี่ยต่อปี (%)", 0.0, 20.0,
                             float(prof["salary_growth_pct"]), step=0.5)

    extra = st.number_input("เงินออมเพิ่มต่อเดือนสำหรับ ม.40 ชราภาพ", 0.0, 50000.0,
                            float(prof["extra_saving_m40"]), step=100.0)
    st.caption(f"💰 เงินออมเพิ่ม {extra:,.2f} บาท/เดือน")

    # ---------- PDPA consent ----------
    st.divider()
    consent = st.checkbox("ยินยอมให้จัดเก็บข้อมูลข้างต้นเพื่อใช้คำนวณสิทธิ "
                          "(ตาม PDPA — แก้ไข/ลบได้ทุกเมื่อ)",
                          value=bool(prof["consent"]))

    if st.form_submit_button("💾 บันทึกข้อมูล", type="primary"):
        if not consent:
            st.warning("กรุณายินยอมให้จัดเก็บข้อมูลก่อนบันทึก")
        else:
            ok, msg = update_profile({
                "full_name": name, "gender": gender, "province": prov,
                "mattra": mattra, "m40_choice": m40,
                "age": int(age), "retire_age": int(retire),
                "start_year_be": int(year), "start_month": int(month),
                "months_contributed": int(months),
                "salary": int(salary), "salary_growth_pct": float(growth),
                "extra_saving_m40": float(extra), "consent": True,
            })
            if ok:
                st.success(msg)
                st.page_link("views/home.py", label="⬅️ กลับหน้าแรก")
            else:
                st.error(msg)
