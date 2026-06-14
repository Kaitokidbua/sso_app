"""
หน้า Dashboard ภาพรวมประเทศ (หน้าที่ 2)
- ข้อมูลเก็บใน Snowflake (ตาราง SSO_STATS) ; ถ้ายังไม่ตั้งค่า -> synthetic
- ดึงข้อมูลดิบจาก Snowflake -> มารวมยอดด้วย DuckDB + pandas (ตาม requirement)
- ใช้ @st.cache_data กับการโหลด/รวมข้อมูล
"""
import numpy as np
import pandas as pd
import duckdb
import plotly.express as px
import streamlit as st

from lib.auth import require_login, get_profile
from lib.snowflake_db import query_df, using_snowflake

require_login()
st.title("📊 Dashboard ภาพรวมประกันสังคมทั้งประเทศ")


@st.cache_data(ttl=3600)
def _synthetic() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    provinces = ["กรุงเทพมหานคร", "นนทบุรี", "ชลบุรี", "เชียงใหม่", "ขอนแก่น",
                 "นครราชสีมา", "สงขลา", "ระยอง", "ภูเก็ต", "สมุทรปราการ"]
    rows = []
    for yr in range(2563, 2569):
        for pv in provinces:
            for mt in ["33", "39", "40"]:
                rows.append({"year": yr, "province": pv, "mattra": mt,
                             "insured": int(rng.integers(20_000, 800_000)),
                             "claims": int(rng.integers(1_000, 90_000))})
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_data():
    """ดึงจาก Snowflake ก่อน ถ้าไม่ได้ค่อย fallback synthetic. คืน (df, source)."""
    if using_snowflake():
        df = query_df("SELECT year, province, mattra, insured, claims FROM sso_stats")
        if df is not None and not df.empty:
            return df, "Snowflake"
    return _synthetic(), "synthetic (demo)"


@st.cache_data(ttl=3600)
def aggregate(df: pd.DataFrame, year: int) -> dict:
    """รวมยอดด้วย DuckDB บน pandas DataFrame โดยตรง."""
    con = duckdb.connect()
    con.register("t", df)
    by_prov = con.execute(f"""
        SELECT province, SUM(insured) AS insured, SUM(claims) AS claims
        FROM t WHERE year = {year}
        GROUP BY province ORDER BY insured DESC
    """).df()
    by_mat = con.execute(f"""
        SELECT mattra, SUM(insured) AS insured
        FROM t WHERE year = {year} GROUP BY mattra ORDER BY mattra
    """).df()
    trend = con.execute("""
        SELECT year, SUM(insured) AS insured FROM t GROUP BY year ORDER BY year
    """).df()
    con.close()
    return {"by_prov": by_prov, "by_mat": by_mat, "trend": trend}


df, source = load_data()
prof = get_profile()

if source == "Snowflake":
    st.caption("🟢 ข้อมูลจาก **Snowflake**")
else:
    st.caption("🧪 ข้อมูล **synthetic (demo)** — ตั้งค่า [snowflake] ใน secrets เพื่อใช้ข้อมูลจริง")

year = st.slider("เลือกปี (พ.ศ.)", int(df.year.min()), int(df.year.max()),
                 int(df.year.max()))
agg = aggregate(df, year)

k1, k2, k3 = st.columns(3)
k1.metric("ผู้ประกันตนรวม", f"{int(agg['by_prov']['insured'].sum()):,}")
k2.metric("การใช้สิทธิรวม", f"{int(agg['by_prov']['claims'].sum()):,}")
k3.metric("จังหวัดของคุณ", prof.get("province", "-"))

c1, c2 = st.columns([2, 1])
with c1:
    fig = px.bar(agg["by_prov"], x="province", y="insured",
                 title="ผู้ประกันตนรายจังหวัด", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig2 = px.pie(agg["by_mat"], names="mattra", values="insured",
                  title="สัดส่วนตามมาตรา", template="plotly_white", hole=0.45)
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(agg["trend"], x="year", y="insured", markers=True,
               title="แนวโน้มผู้ประกันตนรายปี", template="plotly_white")
st.plotly_chart(fig3, use_container_width=True)

with st.expander("ดูข้อมูลดิบ"):
    st.dataframe(df[df.year == year], use_container_width=True)
