"""
จุดเริ่มของแอป (entry point)  ->  รันด้วย:  streamlit run app.py

ใช้ st.navigation + st.Page (multi-page แบบใหม่)
- ยังไม่ได้ login  -> เห็นแค่หน้า "เข้าสู่ระบบ"
- login แล้ว        -> เห็นทุกหน้า (ข้อมูล profile ใน session ใช้ได้ทุกหน้า)
"""
import streamlit as st
from lib.auth import is_logged_in

st.set_page_config(
    page_title="SSO Advisor — ประกันสังคมของฉัน",
    page_icon="🛡️",
    layout="wide",
)

# ----- นิยามทุกหน้า (เพื่อนในกลุ่มแก้ไฟล์ใน views/ ของตัวเองได้เลย) -----
login_pg   = st.Page("views/login.py",        title="เข้าสู่ระบบ",        icon="🔐")
home_pg    = st.Page("views/home.py",         title="หน้าแรก / โปรไฟล์",  icon="🏠", default=True)
edit_pg    = st.Page("views/edit_profile.py", title="แก้ไขข้อมูลสมาชิก",  icon="📝")
dash_pg    = st.Page("views/dashboard.py",    title="Dashboard ประเทศ",   icon="📊")
check_pg   = st.Page("views/check_benefits.py", title="เช็คสิทธิของฉัน",  icon="✅")
compare_pg = st.Page("views/compare_mattra.py", title="เทียบมาตรา",       icon="⚖️")
retire_pg  = st.Page("views/retirement.py",   title="วางแผนเกษียณ/บำนาญ", icon="🏖️")
ai_pg      = st.Page("views/chatbot.py",      title="AI Chatbot",         icon="🤖")

if is_logged_in():
    pg = st.navigation({
        "เมนูหลัก": [home_pg, edit_pg, dash_pg],
        "เครื่องมือ": [check_pg, compare_pg, retire_pg],
        "ผู้ช่วย AI": [ai_pg],
    })
else:
    pg = st.navigation([login_pg])

pg.run()
