"""
สคริปต์รันครั้งเดียว: สร้างตาราง SSO_STATS + อัปโหลดข้อมูล (ตอนนี้ synthetic) เข้า Snowflake
ใช้: python load_to_snowflake.py
(อ่าน credential จาก .streamlit/secrets.toml ส่วน [snowflake])

พอได้ไฟล์จริงจาก catalog.sso.go.th แค่เปลี่ยน build_df() ให้ pd.read_csv(...)
"""
import numpy as np
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

try:
    import tomllib                       # Python 3.11+
    def _load_toml(p):
        with open(p, "rb") as f:
            return tomllib.load(f)
except ImportError:
    import toml
    def _load_toml(p):
        return toml.load(p)


def build_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    provinces = ["กรุงเทพมหานคร", "นนทบุรี", "ชลบุรี", "เชียงใหม่", "ขอนแก่น",
                 "นครราชสีมา", "สงขลา", "ระยอง", "ภูเก็ต", "สมุทรปราการ"]
    rows = []
    for yr in range(2563, 2569):
        for pv in provinces:
            for mt in ["33", "39", "40"]:
                rows.append({"YEAR": yr, "PROVINCE": pv, "MATTRA": mt,
                             "INSURED": int(rng.integers(20_000, 800_000)),
                             "CLAIMS": int(rng.integers(1_000, 90_000))})
    return pd.DataFrame(rows)


def main():
    cfg = _load_toml(".streamlit/secrets.toml")["snowflake"]
    conn = snowflake.connector.connect(
        account=cfg["account"], user=cfg["user"], password=cfg["password"],
        warehouse=cfg.get("warehouse"), database=cfg.get("database"),
        schema=cfg.get("schema"), role=cfg.get("role"),
    )
    df = build_df()

    db = cfg.get("database", "SSO_DB")
    schema = cfg.get("schema", "PUBLIC")
    wh = cfg.get("warehouse", "COMPUTE_WH")

    # สร้าง + เลือก database/schema/warehouse ให้ session ก่อนอัปโหลด
    cur = conn.cursor()
    cur.execute(f"USE WAREHOUSE {wh}")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
    cur.execute(f"USE DATABASE {db}")
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(f"USE SCHEMA {schema}")
    cur.close()

    write_pandas(conn, df, "SSO_STATS",
                 auto_create_table=True, overwrite=True)
    print(f"✅ อัปโหลด {len(df)} แถวเข้า SSO_STATS เรียบร้อย")
    conn.close()


if __name__ == "__main__":
    main()
