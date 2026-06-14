"""
Snowflake layer — ใช้เก็บข้อมูล analytics สำหรับ Dashboard ประเทศ (หน้า 2)
- @st.cache_resource : เปิด connection ครั้งเดียว reuse ทุก rerun
- @st.cache_data     : cache ผลลัพธ์ query

ถ้ายังไม่ได้ตั้งค่า [snowflake] ใน secrets -> คืน None
แล้ว dashboard จะ fallback ไปใช้ synthetic data เอง (รัน demo ได้)
"""
import streamlit as st

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False


def _cfg():
    """อ่าน config snowflake จาก secrets แบบปลอดภัย"""
    try:
        return dict(st.secrets["snowflake"])
    except Exception:
        return None


@st.cache_resource
def get_connection():
    """เปิด connection ครั้งเดียว แล้ว cache (cache_resource)."""
    if not HAS_SNOWFLAKE:
        return None
    cfg = _cfg()
    if not cfg:
        return None
    try:
        return snowflake.connector.connect(
            account=cfg["account"],
            user=cfg["user"],
            password=cfg["password"],
            warehouse=cfg.get("warehouse"),
            database=cfg.get("database"),
            schema=cfg.get("schema"),
            role=cfg.get("role"),
            client_session_keep_alive=True,
        )
    except Exception:
        return None


def using_snowflake() -> bool:
    return get_connection() is not None


@st.cache_data(ttl=3600)
def query_df(sql: str):
    """รัน query แล้วคืน pandas DataFrame (column เป็นตัวพิมพ์เล็ก). None ถ้าต่อไม่ได้."""
    conn = get_connection()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        cur.execute(sql)
        df = cur.fetch_pandas_all()
        df.columns = [c.lower() for c in df.columns]
        return df
    except Exception:
        return None
    finally:
        cur.close()
