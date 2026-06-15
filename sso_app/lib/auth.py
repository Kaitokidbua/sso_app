"""
Auth + Session layer
- รหัสผ่าน hash ด้วย bcrypt (ไม่เก็บ plain text)
- หลัง login: เก็บ user + profile ลง st.session_state -> ใช้ได้ทุกหน้า
- require_login(): การ์ดกันหน้าที่ต้อง login ก่อน
"""
import streamlit as st
from datetime import datetime
import bcrypt

from lib.db import get_db, fallback_store, using_mongo


# ---------- password helpers ----------
def _hash_pw(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())


def _check_pw(pw: str, hashed) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed)
    except Exception:
        return False


# ---------- CRUD ----------
def _find_user(username: str):
    db = get_db()
    if db is not None:
        return db.users.find_one({"username": username})
    return fallback_store()["users"].get(username)


def signup(username: str, password: str, profile: dict):
    if not username or not password:
        return False, "กรอกชื่อผู้ใช้และรหัสผ่านให้ครบ"
    if _find_user(username):
        return False, "มีชื่อผู้ใช้นี้แล้ว ลองชื่ออื่น"

    doc = {
        "username": username,
        "password": _hash_pw(password),
        "profile": profile,
        "created_at": datetime.utcnow(),
    }
    db = get_db()
    if db is not None:
        db.users.insert_one(doc)
    else:
        fallback_store()["users"][username] = doc
    return True, "สมัครสมาชิกสำเร็จ ✅ เข้าสู่ระบบได้เลย"


def login(username: str, password: str):
    user = _find_user(username)
    if not user:
        return False, "ไม่พบชื่อผู้ใช้นี้"
    if not _check_pw(password, user["password"]):
        return False, "รหัสผ่านไม่ถูกต้อง"

    # >>> หัวใจของโจทย์: เก็บลง session ให้ทุกหน้าใช้ร่วมกัน <<<
    st.session_state["user"] = username
    st.session_state["profile"] = user.get("profile", {})
    from lib.profile_sync import sync_profile
    sync_profile()                      # มิเรอร์ให้หน้าเพื่อนอ่านได้
    return True, f"ยินดีต้อนรับ {username} 🎉"


def update_profile(profile: dict):
    """อัปเดต profile ทั้งใน DB และใน session"""
    username = st.session_state.get("user")
    if not username:
        return False, "ยังไม่ได้เข้าสู่ระบบ"

    db = get_db()
    if db is not None:
        db.users.update_one({"username": username}, {"$set": {"profile": profile}})
    else:
        fallback_store()["users"][username]["profile"] = profile

    st.session_state["profile"] = profile
    from lib.profile_sync import sync_profile
    sync_profile()                      # มิเรอร์ให้หน้าเพื่อนอ่านได้
    return True, "บันทึกข้อมูลแล้ว ✅ ทุกหน้าจะใช้ข้อมูลนี้"


# ---------- session helpers ----------
def is_logged_in() -> bool:
    return bool(st.session_state.get("user"))


def get_profile() -> dict:
    return st.session_state.get("profile", {}) or {}


def logout():
    for k in ("user", "profile"):
        st.session_state.pop(k, None)


def require_login():
    """เรียกบรรทัดแรกของทุกหน้าที่ต้อง login ก่อน"""
    if not is_logged_in():
        st.warning("⚠️ กรุณาเข้าสู่ระบบที่หน้า **เข้าสู่ระบบ** ก่อนใช้งานหน้านี้")
        st.stop()
