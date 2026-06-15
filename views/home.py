"""
หน้าแรก (หลัง login) — ดีไซน์ตาม mockup เว็บ สปส. (light theme)
1) การ์ดสรุปส่วนตัว 3 ใบ  (คำนวณจาก profile ใน session)
2) การ์ดบริการ 4 ใบ        (ลิงก์ไปหน้าอื่น)
3) ข่าวสาร / ประกาศ
4) การ์ด CTA วางแผนเกษียณ
"""
import streamlit as st
from lib.auth import require_login, get_profile, update_profile, logout
from lib.constants import MATTRA_OPTIONS, GENDER_OPTIONS, PROVINCES, DEFAULT_PROFILE

require_login()
prof = {**DEFAULT_PROFILE, **get_profile()}

RETIRE_AGE = int(prof.get("retire_age", 55))   # อายุเกษียณ (จาก profile)
PENSION_MONTHS = 180             # ต้องส่งสมทบครบ 180 เดือนจึงมีสิทธิบำนาญ

# ---------- ค่าที่คำนวณจาก profile ----------
months = int(prof["months_contributed"])
pct = min(100, round(months / PENSION_MONTHS * 100))
years_left = max(0, RETIRE_AGE - int(prof["age"]))
care = {"33": "ใช้สิทธิได้", "39": "ใช้สิทธิได้",
        "40": "ตามทางเลือกที่สมัคร"}.get(prof["mattra"], "-")
retire_txt = "ถึงเกณฑ์แล้ว 🎉" if years_left == 0 else f"อีก {years_left} ปี"

# ---------- CSS (light) ----------
st.markdown("""
<style>
.sso-grid{display:flex;gap:16px;flex-wrap:wrap;margin:6px 0 10px;}
.sso-card{flex:1;min-width:190px;border-radius:18px;padding:20px 22px;text-align:center;
  box-shadow:0 1px 4px rgba(20,30,60,.05);}
.sso-card .lab{font-size:.9rem;color:#5b6478;margin-bottom:8px;font-weight:600;}
.sso-card .big{font-size:2rem;font-weight:800;line-height:1.1;}
.sso-card .sub{font-size:.8rem;color:#8a93a6;margin-top:8px;}
.c-blue{background:#eef3ff;} .c-blue .big{color:#2563eb;}
.c-green{background:#eafaf0;} .c-green .big{color:#16a34a;}
.c-mint{background:#e9f7f5;} .c-mint .big{color:#0ea5a4;}
.bar{height:7px;background:#dbe5ff;border-radius:99px;margin-top:10px;overflow:hidden;}
.bar>i{display:block;height:100%;background:#2563eb;border-radius:99px;}
.news{background:#fafbff;border:1px solid #eef1f7;border-radius:18px;padding:18px 22px;}
.news h4{margin:0 0 12px;font-size:1rem;color:#1a1f36;}
.news .row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px dashed #eceff5;font-size:.9rem;}
.news .row:last-child{border:none;} .news .dt{color:#9aa3b5;font-size:.82rem;white-space:nowrap;padding-left:12px;}
.cta{background:linear-gradient(135deg,#e8f0ff,#eafaf6);border-radius:18px;padding:24px;height:100%;}
.cta h3{margin:0 0 6px;color:#1a3b8b;} .cta p{margin:0;color:#5b6478;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

# ---------- header ----------
h1, h2 = st.columns([4, 1])
h1.title(f"สวัสดี {prof.get('full_name') or st.session_state['user']} 👋")
h1.caption("ภาพรวมสิทธิประกันสังคมของคุณ")
if h2.button("ออกจากระบบ"):
    logout(); st.rerun()

# ---------- 1) summary cards ----------
st.markdown(f"""
<div class="sso-grid">
  <div class="sso-card c-blue">
    <div class="lab">เดือนที่ส่งเงินสมทบ</div>
    <div class="big">{months} เดือน</div>
    <div class="bar"><i style="width:{pct}%"></i></div>
    <div class="sub">จากเกณฑ์ {PENSION_MONTHS} เดือน (รับบำนาญ)</div>
  </div>
  <div class="sso-card c-green">
    <div class="lab">สิทธิการรักษาพยาบาล</div>
    <div class="big" style="font-size:1.4rem">โรงพยาบาลตามสิทธิ</div>
    <div class="sub">มาตรา {prof['mattra']} — {care}</div>
  </div>
  <div class="sso-card c-mint">
    <div class="lab">คาดว่าจะเกษียณ</div>
    <div class="big">{retire_txt}</div>
    <div class="sub">เมื่ออายุ {RETIRE_AGE} ปี (ปัจจุบัน {prof['age']} ปี)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- 2) service cards (clickable) ----------
st.subheader("บริการ")
s1, s2, s3, s4 = st.columns(4)
with s1:
    with st.container(border=True):
        st.markdown("### 🔍"); st.page_link("views/check_benefits.py", label="เช็คสิทธิของฉัน")
with s2:
    with st.container(border=True):
        st.markdown("### 🎁"); st.page_link("views/compare_mattra.py", label="สิทธิประโยชน์ / เทียบมาตรา")
with s3:
    with st.container(border=True):
        st.markdown("### 📊"); st.page_link("views/retirement.py", label="วางแผนเกษียณ")
with s4:
    with st.container(border=True):
        st.markdown("### 💬"); st.page_link("views/chatbot.py", label="แชทกับ AI")

# ---------- 3) news + 4) CTA ----------
news = [
    ("ปรับเพิ่มสิทธิประโยชน์ค่าคลอดบุตร เริ่ม 1 ม.ค. 2567", "20 พ.ค. 2567"),
    ("มาตรการช่วยเหลือผู้ประกันตน ม.33 และ ม.39", "15 พ.ค. 2567"),
    ("ตรวจสอบสิทธิการรักษาพยาบาลประจำปี 2567", "10 พ.ค. 2567"),
]
rows = "".join(f'<div class="row"><span>• {t}</span><span class="dt">{d}</span></div>'
               for t, d in news)
left, right = st.columns([2, 1])
with left:
    st.markdown(f'<div class="news"><h4>ข่าวสาร / ประกาศล่าสุด</h4>{rows}</div>',
                unsafe_allow_html=True)
with right:
    st.markdown("""<div class="cta"><h3>รู้สิทธิ รู้ก่อน ได้เปรียบ 👵👴</h3>
                <p>วางแผนอนาคต ให้ชีวิตมั่นคง</p></div>""", unsafe_allow_html=True)
    st.page_link("views/retirement.py", label="เริ่มวางแผนเลย →")

# ---------- edit profile link ----------
st.divider()
st.page_link("views/edit_profile.py",
             label="✏️ แก้ไขข้อมูลสมาชิก (อายุเกษียณ, เงินเดือน, ม.40 ฯลฯ)")
