# 🛡️ SSO Advisor — ผู้ช่วยประกันสังคม

Data-centric Streamlit app + AI add-on (final project / Gemma 4 Good Hackathon)

## โครงสร้าง
```
app.py                  # entry: st.navigation, gate ตาม login
lib/
  db.py                 # MongoDB client (@st.cache_resource) + fallback
  auth.py               # signup/login/profile + session + require_login()
  constants.py          # มาตรา, จังหวัด, โครง profile
views/
  login.py              # หน้า 1A: เข้าสู่ระบบ/สมัคร
  home.py               # หน้า 1B: ฟอร์มโปรไฟล์ + ลิงก์ไปหน้าอื่น
  dashboard.py          # หน้า 2: Plotly + DuckDB + pandas (@st.cache_data)
  check_benefits.py     # หน้า 3 (เพื่อน)
  compare_mattra.py     # หน้า 4 (เพื่อน)
  retirement.py         # หน้า 5 (เพื่อน)
  chatbot.py            # หน้า 6: โหมด AI (Gemma)
```

## ✅ ครบตาม requirement
- Multi-pages (st.navigation/st.Page)
- DuckDB + pandas (dashboard.py)
- External cloud storage: **MongoDB Atlas**
- 2 โหมด: Non-AI (เช็คสิทธิ/เทียบ/เกษียณ) vs AI (chatbot)
- **cache_resource** (db client), **cache_data** (dashboard), **session** (profile ใช้ทุกหน้า)

## รัน local
```bash
pip install -r requirements.txt
streamlit run app.py        # ไม่มี Mongo ก็รันได้ (โหมด demo)
```

## ต่อ MongoDB Atlas
1. สร้าง free cluster (M0) ที่ mongodb.com/cloud/atlas
2. Database Access -> สร้าง user/password
3. Network Access -> Allow 0.0.0.0/0
4. คัดลอก connection string ใส่ใน `.streamlit/secrets.toml` (ดู .example)
5. รันใหม่ -> ข้อมูล user/profile จะถูกเก็บถาวร

## Deploy (Streamlit Cloud)
push ขึ้น GitHub (secrets.toml ถูก .gitignore ไว้แล้ว) -> share.streamlit.io
-> New app -> เลือก repo + `app.py` -> Settings -> Secrets วางเนื้อหาจาก .example
