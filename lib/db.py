"""
Database layer — MongoDB Atlas (external cloud storage).
ใช้ @st.cache_resource เพื่อให้ client connection ถูกสร้างครั้งเดียว
แล้ว reuse ทุก rerun / ทุก session (ไม่ต่อใหม่ทุกครั้งที่กดปุ่ม)

ถ้ายังไม่ได้ตั้งค่า secrets -> ใช้ in-memory store แทน (โหมด demo รันในเครื่องได้)
"""
import streamlit as st

try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

try:
    import certifi
    _CA = certifi.where()
except ImportError:
    _CA = None


def _secret_uri():
    """อ่าน mongo uri จาก secrets แบบปลอดภัย — ถ้าไม่มีไฟล์ secrets เลย ก็คืน None"""
    try:
        return st.secrets["mongo"]["uri"]
    except Exception:
        return None


def _secret_dbname():
    try:
        return st.secrets["mongo"].get("database", "sso_app")
    except Exception:
        return "sso_app"


@st.cache_resource
def get_client():
    """สร้าง Mongo client ครั้งเดียว แล้ว cache ไว้ (cache_resource)."""
    if not HAS_PYMONGO:
        return None
    uri = _secret_uri()
    if not uri:
        return None
    try:
        kwargs = {"serverSelectionTimeoutMS": 5000}
        if _CA:
            kwargs["tlsCAFile"] = _CA      # แก้ SSL handshake บน Windows/Anaconda
        client = MongoClient(uri, **kwargs)
        client.admin.command("ping")          # ทดสอบว่าต่อได้จริง
        return client
    except Exception:
        return None


def get_db():
    """คืน database object หรือ None ถ้าต่อ Mongo ไม่ได้ (จะ fallback)."""
    client = get_client()
    if client is None:
        return None
    return client[_secret_dbname()]


@st.cache_resource
def fallback_store():
    """
    in-memory user store สำหรับโหมด demo (ตอนยังไม่ใส่ Mongo URI)
    ใช้ cache_resource เพื่อให้ dict นี้อยู่ค้างข้าม session / rerun
    """
    return {"users": {}}


def using_mongo() -> bool:
    return get_db() is not None
