import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.auth import require_login
require_login()

import streamlit as st
import plotly.express as px
import pandas as pd
from sso_advisor import SSOMasterAdvisor


@st.cache_resource
def load_advisor():
    return SSOMasterAdvisor(
        db_path="sso_advisor.db"
    )

advisor = load_advisor()

profile = st.session_state.get("profile", {})

section_map = advisor.get_section_label_map()
section_reverse = advisor.get_section_reverse_map()

st.session_state.setdefault("profile", {})

if "app_section" not in st.session_state:
    st.session_state["app_section"] = st.session_state["profile"].get(
        "section",
        profile.get("section", "m33")
    )

if "app_m40_plan" not in st.session_state:
    st.session_state["app_m40_plan"] = int(
        st.session_state["profile"].get(
            "plan_no",
            profile.get("plan_no", 1)
        ) or 1
    )

st.session_state["profile_section"] = section_reverse.get(
    st.session_state["app_section"],
    "มาตรา 33"
)

st.session_state["profile_m40_plan"] = int(
    st.session_state.get("app_m40_plan", 1) or 1
)

def sync_profile_section():
    """Sync section selectbox value to durable shared state."""
    section_label_value = st.session_state.get("profile_section", "มาตรา 33")
    section_code = section_map.get(section_label_value, "m33")

    st.session_state["app_section"] = section_code
    st.session_state.setdefault("profile", {})
    st.session_state["profile"]["section"] = section_code

def sync_profile_m40_plan():
    """Sync m40 plan selectbox value to durable shared state."""
    plan_value = int(st.session_state.get("profile_m40_plan", 1) or 1)

    st.session_state["app_m40_plan"] = plan_value
    st.session_state.setdefault("profile", {})
    st.session_state["profile"]["plan_no"] = plan_value

if "profile_start_salary" not in st.session_state:
        st.session_state["profile_start_salary"] = float(
            profile.get(
                "start_salary",
                advisor.get_app_setting("default_start_salary", 12000)
            )
        )

if "profile_current_salary" not in st.session_state:
    st.session_state["profile_current_salary"] = float(
        profile.get(
            "current_salary",
            advisor.get_app_setting("default_current_salary", 15000)
        )
    )

if "profile_start_year" not in st.session_state:
    st.session_state["profile_start_year"] = int(
        profile.get(
            "start_year",
            advisor.get_app_setting("default_start_year", 2560)
        )
    )

if "profile_age" not in st.session_state:
    st.session_state["profile_age"] = int(
        profile.get(
            "age",
            advisor.get_app_setting("default_age", 30)
        )
    )

if "profile_current_year" not in st.session_state:
    st.session_state["profile_current_year"] = int(
        profile.get(
            "current_year",
            advisor.get_app_setting("default_current_year", 2568)
        )
    )

if "profile_current_month" not in st.session_state:
    st.session_state["profile_current_month"] = int(
        profile.get(
            "current_month",
            advisor.get_app_setting("default_current_month", 1)
        )
    )

st.title("✅ ตรวจสอบสิทธิประโยชน์ที่ตัวเองได้รับ")

st.subheader("👤 กรอกข้อมูลเบื้องต้น")

col1, col2 = st.columns(2)

with col1:
    section_options = ["มาตรา 33", "มาตรา 39", "มาตรา 40"]

    section_label = st.selectbox(
        "มาตราประกันสังคม",
        section_options,
        key="profile_section",
        on_change=sync_profile_section
    )

section = section_map[section_label]

with col2:
    if section == "m40":
        plan_options = [1, 2, 3]

        plan_no = st.selectbox(
            "เลือกทางเลือก ม.40",
            plan_options,
            key="profile_m40_plan",
            on_change=sync_profile_m40_plan
        )

        st.session_state["app_m40_plan"] = int(plan_no)
        st.session_state.setdefault("profile", {})
        st.session_state["profile"]["plan_no"] = int(plan_no)
    else:
        plan_no = None
        st.empty()

col3, col4 = st.columns(2)

with col3:
    start_salary = st.number_input(
        "เงินเดือนเริ่มต้น",
        min_value=0.0,
        step=500.0,
        format="%.2f",
        key="profile_start_salary"
    )
    st.caption(f"💰 {start_salary:,.2f} บาท")

with col4:
    current_salary = st.number_input(
        "เงินเดือนปัจจุบัน",
        min_value=0.0,
        step=500.0,
        format="%.2f",
        key="profile_current_salary"
    )
    st.caption(f"💰 {current_salary:,.2f} บาท")

col5, col6 = st.columns(2)

with col5:
    start_year = st.number_input(
        "ปี พ.ศ. ที่เริ่มทำงาน / เริ่มส่งสมทบ",
        min_value=2547,
        step=1,
        key="profile_start_year"
    )

with col6:
    age = st.number_input(
        "อายุปัจจุบัน",
        min_value=15,
        max_value=100,
        step=1,
        key="profile_age"
    )

col7, col8 = st.columns(2)

with col7:
    current_year = st.number_input(
        "ปีปัจจุบันที่ต้องการคำนวณ",
        min_value=2547,
        step=1,
        key="profile_current_year"
    )

with col8:
    current_month = st.selectbox(
        "เดือนปัจจุบันที่ต้องการคำนวณ",
        list(range(1, 13)),
        key="profile_current_month"
    )

if int(current_year) < int(start_year):
    st.error("ปีปัจจุบันที่ต้องการคำนวณ ต้องไม่น้อยกว่าปีที่เริ่มทำงาน / เริ่มส่งสมทบ")
    st.stop()

section = section_map[section_label]

months_paid = ((int(current_year) - int(start_year)) * 12) + int(current_month)
months_paid = max(months_paid, 0)

age_months = int(age) * 12

if months_paid > age_months:
    st.error(
        f"ข้อมูลไม่สมเหตุสมผล: จำนวนเดือนที่ส่งสมทบประมาณ {months_paid:,} เดือน "
        f"แต่มากกว่าอายุปัจจุบันประมาณ {age_months:,} เดือน"
    )
    st.stop()

st.session_state.setdefault("profile", {})
previous_is_from_page1 = st.session_state["profile"].get("is_from_page1", False)

st.session_state["profile"].update({
    "section": section,
    "plan_no": plan_no if section == "m40" else st.session_state["profile"].get("plan_no"),
    "start_year": start_year,
    "current_year": current_year,
    "current_month": current_month,
    "start_salary": start_salary,
    "current_salary": current_salary,
    "age": age,
    "months_paid": months_paid,
    "is_from_page1": previous_is_from_page1,
})

st.divider()

if st.button("🔍 วิเคราะห์สิทธิของฉัน", key="analyze_profile"):
    st.session_state["page1_analyzed"] = True
    st.session_state["profile"]["is_from_page1"] = True

if st.session_state.get("page1_analyzed", False):

    st.subheader("📊 เงินสมทบสะสมทั้งหมด")

    result = advisor.calculate_contribution_range_linear_annual(
        section=section,
        start_salary=float(start_salary),
        current_salary=float(current_salary),
        start_year=int(start_year),
        start_month=1,
        end_year=int(current_year),
        end_month=int(current_month),
        plan_no=plan_no
    )

    rows = result["rows"]

    employee_total = float(result["employee_total"])
    employer_total = float(result["employer_total"])
    government_total = float(result["government_total"])
    total_contribution = float(result["total_contribution"])
    months_total = int(result["months"])

    st.session_state["page1_analysis"] = {
        "rows": rows,
        "employee_total": employee_total,
        "employer_total": employer_total,
        "government_total": government_total,
        "total_contribution": total_contribution,
        "months_total": months_total,
    }

    chart_data = pd.DataFrame({
        "ประเภท": ["ผู้ประกันตน", "นายจ้าง", "รัฐบาล"],
        "ยอดสะสม": [employee_total, employer_total, government_total],
    })

    fig = px.pie(
        chart_data,
        names="ประเภท",
        values="ยอดสะสม",
        hole=0.48,
        color="ประเภท",
        color_discrete_map={
            "นายจ้าง": "#D0F4DE",
            "ผู้ประกันตน": "#FADCDC",
            "รัฐบาล": "#FCF6BD",
        },
    )

    fig.update_traces(
        textinfo="percent",
        textfont_size=30,
        textfont_color="black",
        marker=dict(line=dict(color="white", width=2)),
    )

    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=16),
        ),
        annotations=[
            dict(
                text=(
                    f"<b>รวมทั้งหมด</b><br>"
                    f"<span style='font-size:20px'><b>{total_contribution:,.2f}</b></span><br>"
                    f"บาท"
                ),
                x=0.5,
                y=0.5,
                font=dict(size=14, color="#1f2937"),
                showarrow=False,
            )
        ],
    )

    col_left, col_right = st.columns([1.05, 1.25], gap="large")

    with col_left:
        st.markdown(
            f"""
            <div style="
                background-color:#F0F7FF;
                padding:28px;
                border-radius:14px;
                border:1px solid #D7E8FF;
                min-height:390px;
                color:#003B7A;
                font-size:20px;
                line-height:2.1;
            ">
                <b>ส่งสมทบโดยประมาณทั้งหมด {months_total:,} เดือน</b>
                <hr style="border:0; border-top:1px solid #D1D5DB;">
                ผู้ประกันตนจ่ายสะสม: <b>{employee_total:,.2f} บาท</b><br>
                นายจ้างสมทบสะสม: <b>{employer_total:,.2f} บาท</b><br>
                รัฐบาลสมทบสะสม: <b>{government_total:,.2f} บาท</b>
                <hr style="border:0; border-top:1px solid #D1D5DB;">
                รวมเงินสมทบทั้งหมด: <b style="font-size:26px;">{total_contribution:,.2f} บาท</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.plotly_chart(
            fig,
            use_container_width=True,
            key="contribution_pie_chart"
        )

    with st.expander("ดูรายละเอียดเงินเดือนและเงินสมทบรายเดือน", expanded=False):
        df = pd.DataFrame([
            {
                "ปี": r["year"],
                "เดือน": r["month"],
                "เงินเดือนประมาณการ": r["estimated_salary"],
                "ฐานคำนวณ": r["salary_base"],
                "ผู้ประกันตนจ่าย": r["employee_contribution"],
                "นายจ้างสมทบ": r["employer_contribution"],
                "รัฐบาลสมทบ": r["government_contribution"],
                "รวมเงินสมทบ": r["total_contribution"],
                "รายละเอียด": r["description"],
            }
            for r in rows
        ])

        total_row = {
            "ปี": "รวม",
            "เดือน": "",
            "เงินเดือนประมาณการ": "",
            "ฐานคำนวณ": "",
            "ผู้ประกันตนจ่าย": employee_total,
            "นายจ้างสมทบ": employer_total,
            "รัฐบาลสมทบ": government_total,
            "รวมเงินสมทบ": total_contribution,
            "รายละเอียด": "",
        }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        df = df.replace({None: "", "None": ""}).fillna("")

        numeric_cols = [
            "เงินเดือนประมาณการ",
            "ฐานคำนวณ",
            "ผู้ประกันตนจ่าย",
            "นายจ้างสมทบ",
            "รัฐบาลสมทบ",
            "รวมเงินสมทบ",
        ]

        def money_format(x):
            try:
                if pd.isna(x) or x == "":
                    return ""
                return f"{float(x):,.2f}"
            except:
                return x

        styled_df = (
            df.style
            .format({
                col: money_format
                for col in numeric_cols
            })
            .set_properties(
                subset=numeric_cols,
                **{"text-align": "right"}
            )
            .set_table_styles([
                {"selector": "th", "props": [("text-align", "center")]}
            ])
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("🎁 สิทธิประโยชน์ที่ได้รับ ณ ปัจจุบัน")

    categories = advisor.get_benefit_categories()

    has_any_benefit = False

    for category in categories:
        benefits = advisor.get_benefit_benefits(
            category, section, plan_no=plan_no, months_paid=months_paid
        )
        conditions = advisor.get_benefit_conditions(
            category, section, plan_no=plan_no, months_paid=months_paid
        )
        notes = advisor.get_benefit_notes(
            category, section, plan_no=plan_no, months_paid=months_paid
        )
        if not benefits and not conditions:
            continue

        eligibility = advisor.check_benefit_eligibility(
            category=category,
            months_paid=months_paid,
            age=age,
            section=section,
            plan_no=plan_no
        )

        icon = "✅" if eligibility["eligible"] else "🔒"
        title = f"{icon} {category}"

        with st.expander(title):
            if eligibility["eligible"]:
                st.success(eligibility["message"])
            else:
                st.warning(eligibility["message"])

            if benefits:
                st.markdown("#### ✅ ประโยชน์ที่ได้รับ")
                for item in benefits:
                    st.write(item)

            if conditions:
                st.markdown("#### 🧾 เงื่อนไข")
                for item in conditions:
                    st.write(item)

            if notes:
                st.markdown("#### 📝 หมายเหตุ")
                for item in notes:
                    st.write(item)

st.divider()

st.subheader("📌 หมายเหตุ")

st.warning("""
จำนวนเงินที่ได้รับจากสิทธิประโยชน์จะถูกคิดตามสัดส่วนของฐานเงินเดือนเฉลี่ยในช่วงเวลาที่ส่งเงินสมทบ และจำนวนเดือนที่ส่งเงินสมทบ 
ซึ่งอาจแตกต่างกันไปในแต่ละกรณี และอาจมีการเปลี่ยนแปลงตามกฎหมายและประกาศของสำนักงานประกันสังคม
""")