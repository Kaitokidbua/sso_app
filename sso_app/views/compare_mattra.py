import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.auth import require_login
require_login()

import streamlit as st
import pandas as pd
from sso_advisor import SSOMasterAdvisor


@st.cache_resource
def load_advisor():
    return SSOMasterAdvisor(
        db_path="sso_advisor.db"
    )

advisor = load_advisor()

st.title("📊 เปรียบเทียบมาตราประกันสังคม")
st.caption("เปรียบเทียบ ม.33 / ม.39 / ม.40 เพื่อช่วยเลือกมาตราที่เหมาะกับสถานะและเป้าหมายของคุณ")

df = advisor.get_duckdb_comparison_table()

st.subheader("📋 ตารางเปรียบเทียบภาพรวม")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("✅ ตารางสิทธิประโยชน์แบบ Checklist")

checklist_rows = advisor.get_benefit_checklist_from_db()

sections = advisor.get_sections_for_comparison()

table = {}

for section_name, category, display_text in checklist_rows:
    if section_name not in table:
        table[section_name] = {"มาตรา": section_name}

    table[section_name][category] = display_text

checklist_data = list(table.values())

st.dataframe(
    pd.DataFrame(checklist_data),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("🔎 รายละเอียดแต่ละมาตรา")

tabs = st.tabs([item["title"] for item in sections])

for tab, item in zip(tabs, sections):
    title = item["title"]
    section = item["section"]
    plan_no = item["plan_no"]
    
    with tab:
        st.markdown(f"### {title}")

        recommendations = advisor.get_recommendations_from_db(
            section,
            plan_no
        )

        for text, msg_type in recommendations:
            if msg_type == "success":
                st.success(text)
            elif msg_type == "warning":
                st.warning(text)
            else:
                st.info(text)

        st.markdown("**จุดเด่น**")

        highlights = advisor.get_section_highlights(
            section,
            plan_no
        )

        for item in highlights:
            st.markdown(f"- {item}")

st.divider()

st.subheader("🧭 แนะนำมาตราที่เหมาะกับคุณ")

col1, col2 = st.columns(2)

with col1:
    user_status_options = advisor.get_user_status_options()

    user_status = st.selectbox(
        "สถานะของคุณ",
        user_status_options
    )

with col2:
    priority_options = advisor.get_priority_options(user_status)

    if priority_options:
        priority = st.selectbox(
            "สิ่งที่ให้ความสำคัญที่สุด",
            priority_options
        )
    else:
        priority = None

rec = advisor.get_recommendation_by_profile(user_status, priority)

if rec:
    text, msg_type = rec

    if msg_type == "success":
        st.success(text)
    elif msg_type == "warning":
        st.warning(text)
    else:
        st.info(text)