"""
หน้าเข้าสู่ระบบ + สมัครสมาชิก
สมัครเสร็จกรอกข้อมูลโปรไฟล์เบื้องต้นได้เลย -> เก็บลง MongoDB
"""
import streamlit as st
from lib.auth import login, signup, is_logged_in
from lib.db import using_mongo
from lib.constants import MATTRA_OPTIONS, GENDER_OPTIONS, PROVINCES, DEFAULT_PROFILE

st.title("🛡️ SSO Advisor — ผู้ช่วยประกันสังคมของฉัน")
st.caption("เข้าสู่ระบบเพื่อกรอกข้อมูลครั้งเดียว แล้วใช้ได้ทุกหน้า")

if not using_mongo():
    st.info("🧪 กำลังรันโหมด **demo** (ยังไม่ได้ตั้งค่า MongoDB) — ข้อมูลจะหายเมื่อปิดแอป "
            "ดูวิธีต่อ Atlas ที่ README", icon="ℹ️")

tab_login, tab_signup = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก"])

# ---------- LOGIN ----------
with tab_login:
    u = st.text_input("ชื่อผู้ใช้", key="login_u")
    p = st.text_input("รหัสผ่าน", type="password", key="login_p")
    if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
        ok, msg = login(u, p)
        if ok:
            st.success(msg)
            st.rerun()   # รีรันเพื่อให้ st.navigation ปลดล็อกทุกหน้า
        else:
            st.error(msg)

# ---------- SIGN UP ----------
with tab_signup:
    su = st.text_input("ตั้งชื่อผู้ใช้", key="su_u")
    sp = st.text_input("ตั้งรหัสผ่าน", type="password", key="su_p")

    st.markdown("**ข้อมูลเบื้องต้น** (แก้ภายหลังที่หน้าแรกได้)")
    c1, c2 = st.columns(2)
    name   = c1.text_input("ชื่อ-นามสกุล", key="su_name")
    age    = c2.number_input("อายุ", 15, 80, DEFAULT_PROFILE["age"], key="su_age")
    gender = c1.selectbox("เพศ", GENDER_OPTIONS, key="su_gender")
    prov   = c2.selectbox("จังหวัด", PROVINCES, key="su_prov")
    mattra = st.selectbox("มาตรา", list(MATTRA_OPTIONS.keys()),
                          format_func=lambda k: MATTRA_OPTIONS[k], key="su_mat")

    if st.button("สมัครสมาชิก", type="primary", use_container_width=True):
        profile = {
            **DEFAULT_PROFILE,
            "full_name": name, "age": int(age), "gender": gender,
            "province": prov, "mattra": mattra,
        }
        ok, msg = signup(su, sp, profile)
        (st.success if ok else st.error)(msg)
