import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.auth import require_login
require_login()

import math
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from sso_advisor import SSOMasterAdvisor


tab1, tab2 = st.tabs([
    "📈 ประมาณการเกษียณ",
    "🎯 เป้าหมายเกษียณ"
])

with tab1:
    @st.cache_resource
    def load_advisor():
        return SSOMasterAdvisor(
            db_path="sso_advisor.db"
        )

    advisor = load_advisor()

    profile = st.session_state.get("profile", {})

    section_options = ["มาตรา 33", "มาตรา 39", "มาตรา 40"]
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

    if "app_retire_age" not in st.session_state:
        st.session_state["app_retire_age"] = int(
            st.session_state["profile"].get(
                "retire_age",
                profile.get(
                    "retire_age",
                    advisor.get_app_setting("default_retire_age", 60)
                )
            ) or advisor.get_app_setting("default_retire_age", 60)
        )

    if "extra_saving_m40_value" not in st.session_state:
        st.session_state["extra_saving_m40_value"] = float(
            profile.get(
                "extra_saving_per_month",
                advisor.get_app_setting("default_extra_saving_m40", 0)
            ) or 0
        )

    if "target_monthly_pension_value" not in st.session_state:
        st.session_state["target_monthly_pension_value"] = float(
            profile.get(
                "target_monthly_pension",
                advisor.get_app_setting("default_target_monthly_pension", 10000)
            )
        )

    if "target_lump_sum_value" not in st.session_state:
        st.session_state["target_lump_sum_value"] = float(
            profile.get(
                "target_lump_sum",
                advisor.get_app_setting("default_target_lump_sum", 100000)
            )
        )

    if "retire_age" not in st.session_state:
        st.session_state["retire_age"] = int(st.session_state["app_retire_age"])

    st.title("📈 วางแผนเกษียณ")

    profile = st.session_state.get("profile", {})

    if not profile.get("is_from_page1", False):
        st.warning(
            """
    ⚠️ กรุณากรอกข้อมูลในหน้า "ตรวจสอบสิทธิประโยชน์" ก่อน เพื่อให้ระบบทราบข้อมูลพื้นฐานของผู้ประกันตน
    """
        )

    if "retire_salary_growth" not in st.session_state:
        st.session_state["retire_salary_growth"] = float(
            profile.get(
                "salary_growth",
                advisor.get_app_setting("default_salary_growth", 3.0)
            ) or 3.0
        )

    st.subheader("👤 กรอกข้อมูลเพื่อวางแผน")

    col1, col2 = st.columns(2)

    with col1:
        page1_section = st.session_state.get(
            "app_section",
            st.session_state.get("profile", {}).get("section", "m33")
        )
        section_label = section_reverse.get(page1_section, "มาตรา 33")

        st.selectbox(
            "มาตราประกันสังคม",
            section_options,
            index=section_options.index(section_label),
            disabled=True
        )

    section = page1_section

    with col2:
        if section == "m40":
            # Page 2 อ่านทางเลือก ม.40 จาก Page 1 เท่านั้น
            plan_no = int(
                st.session_state.get(
                    "app_m40_plan",
                    st.session_state.get("profile", {}).get("plan_no", 1)
                ) or 1
            )

            st.selectbox(
                "เลือกทางเลือก ม.40",
                [1, 2, 3],
                index=[1, 2, 3].index(plan_no),
                disabled=True
            )
        else:
            plan_no = None
            st.empty()

    col3, col4 = st.columns(2)

    with col3:
        current_age = st.number_input(
            "อายุปัจจุบัน",
            min_value=15,
            max_value=100,
            value=int(profile.get("age", 35)),
            step=1,
            key="retire_current_age",
            disabled=True
        )

    with col4:
        retire_age = st.number_input(
            "อายุที่ต้องการเกษียณ",
            min_value=30,
            max_value=100,
            step=1,
            key="retire_age"
        )

        st.session_state["app_retire_age"] = int(retire_age)
        st.session_state.setdefault("profile", {})
        st.session_state["profile"]["retire_age"] = int(retire_age)

    col5, col6 = st.columns(2)

    with col5:
        start_year = st.number_input(
            "ปี พ.ศ. ที่เริ่มคำนวณ",
            min_value=2547,
            value=int(profile.get("current_year", datetime.now().year + 543)),
            step=1,
            key="retire_start_year",
            disabled=True
        )

    with col6:
        start_month_default = int(profile.get("current_month", datetime.now().month))

        start_month = st.selectbox(
            "เดือนที่เริ่มคำนวณ",
            list(range(1, 13)),
            index=start_month_default - 1,
            key="retire_start_month",
            disabled=True
        )

    col_paid1, col_paid2 = st.columns(2)

    with col_paid1:
        current_months_paid = st.number_input(
            "จำนวนเดือนที่ส่งเงินสมทบมาแล้ว",
            min_value=0,
            value=int(profile.get("months_paid", 0)),
            step=1,
            key="retire_current_months_paid",
            disabled=True
        )

    with col_paid2:
        st.caption("ใช้สำหรับประเมินบำเหน็จ/บำนาญ และโบนัส ม.40 ให้รวมกับเดือนที่จะส่งในอนาคต")

    col7, col8 = st.columns(2)

    with col7:
        current_salary = st.number_input(
            "เงินเดือนปัจจุบัน",
            min_value=0.0,
            value=float(profile.get("current_salary", 15000.0)),
            step=500.0,
            format="%.2f",
            key="retire_current_salary",
            disabled=True
        )
        st.caption(f"💰 {current_salary:,.2f} บาท")

    with col8:
        salary_growth = st.number_input(
            "เงินเดือนเพิ่มเฉลี่ยต่อปี (%)",
            min_value=0.0,
            max_value=30.0,
            step=0.5,
            format="%.2f",
            key="retire_salary_growth"
        )

    max_extra_saving_m40 = float(
    advisor.get_app_setting("max_extra_saving_m40", 1000) or 1000
)

    if section == "m40" and plan_no in (2, 3):
        current_extra_value = min(
            float(st.session_state.get("extra_saving_m40_value", 0) or 0),
            max_extra_saving_m40
        )

        extra_saving_per_month = st.number_input(
            "เงินออมเพิ่มต่อเดือนสำหรับ ม.40 ชราภาพ",
            min_value=0.0,
            max_value=max_extra_saving_m40,
            value=current_extra_value,
            step=100.0,
            format="%.2f",
            key="extra_saving_m40_input"
        )

        st.session_state["extra_saving_m40_value"] = float(extra_saving_per_month)
        st.caption(f"💰 เงินออมเพิ่ม {extra_saving_per_month:,.2f} บาท/เดือน")

    elif section == "m40":
        extra_saving_per_month = 0.0
        st.info("ม.40 ทางเลือกที่ 1 ไม่มีการสมทบเงินออมเพิ่ม")

    else:
        extra_saving_per_month = 0.0

    st.session_state["saved_extra_saving_m40"] = float(extra_saving_per_month)

    st.session_state.setdefault("profile", {})
    st.session_state["profile"].update({
        "retire_age": int(retire_age),
        "salary_growth": float(salary_growth),
        "extra_saving_per_month": float(extra_saving_per_month),
        "age": int(current_age),
        "current_salary": float(current_salary),
        "current_year": int(start_year),
        "current_month": int(start_month),
        "months_paid": int(current_months_paid),
    })

    st.divider()

    def money_format(x):
        try:
            if pd.isna(x) or x == "":
                return ""
            return f"{float(x):,.2f}"
        except Exception:
            return x

    def build_styled_dataframe(df: pd.DataFrame):
        numeric_cols = [
            "เงินเดือนประมาณการ",
            "ฐานคำนวณ",
            "ผู้ประกันตนจ่าย",
            "นายจ้างสมทบ",
            "รัฐบาลสมทบ",
            "รวมเงินสมทบ",
        ]

        styled_df = (
            df.style
            .format({
                col: money_format
                for col in numeric_cols
                if col in df.columns
            })
            .set_properties(
                subset=[col for col in numeric_cols if col in df.columns],
                **{"text-align": "right"}
            )
            .set_table_styles([
                {"selector": "th", "props": [("text-align", "center")]}
            ])
        )

        return styled_df

    if st.button("📊 คำนวณแผนเกษียณ", key="calculate_retirement"):
        st.session_state["retirement_analyzed"] = True

    if st.session_state.get("retirement_analyzed", False):

        if retire_age <= current_age:
            st.error("อายุเกษียณต้องมากกว่าอายุปัจจุบัน")
            st.stop()

        years_left = int(retire_age - current_age)
        months_left = years_left * 12

        start_year_int = int(start_year)
        start_month_int = int(start_month)

        end_year = start_year_int + years_left
        end_month = start_month_int - 1

        if end_month == 0:
            end_month = 12
            end_year -= 1

        future_salary = float(current_salary) * (
            (1 + float(salary_growth) / 100) ** years_left
        )

        result = advisor.calculate_contribution_range_linear_annual(
            section=section,
            start_salary=float(current_salary),
            current_salary=float(future_salary),
            start_year=start_year_int,
            start_month=start_month_int,
            end_year=end_year,
            end_month=end_month,
            plan_no=plan_no
        )

        st.session_state["retirement_result"] = result

        rows = result["rows"]

        employee_total = float(result["employee_total"])
        employer_total = float(result["employer_total"])
        government_total = float(result["government_total"])
        total_contribution = float(result["total_contribution"])

        st.subheader("📌 สรุปแผนเกษียณ")

        col1, col2, col3, col4 = st.columns(4)

        total_months_future = len(rows)
        total_months_combined = current_months_paid + total_months_future

        col1.metric(
            "ระยะเวลาถึงเกษียณ",
            f"{months_left:,} เดือน"
        )

        col2.metric(
            "เงินเดือนปีสุดท้าย",
            f"{future_salary:,.2f} บาท"
        )

        col3.metric(
            "เดือนสมทบรวม",
            f"{total_months_combined:,} เดือน"
        )

        col4.metric(
            "อายุเกษียณ",
            f"{retire_age} ปี"
        )

        st.subheader("📊 สัดส่วนเงินสมทบจนถึงเกษียณ")

        chart_data = pd.DataFrame({
            "ประเภท": ["ผู้ประกันตน", "นายจ้าง", "รัฐบาล"],
            "ยอดสะสม": [employee_total, employer_total, government_total],
        })

        chart_data = chart_data[chart_data["ยอดสะสม"] > 0]

        if not chart_data.empty:
            fig = px.pie(
                chart_data,
                names="ประเภท",
                values="ยอดสะสม",
                hole=0.48,
                color="ประเภท",
                color_discrete_map={
                    "นายจ้าง": "#BDECCF",
                    "ผู้ประกันตน": "#F8D5D5",
                    "รัฐบาล": "#FFF4B8",
                },
            )

            fig.update_traces(
                textinfo="percent",
                textfont=dict(
                    size=30,
                    color="black"
                ),
                marker=dict(line=dict(color="white", width=2)),
            )

            fig.update_layout(
                height=420,
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
                        font=dict(size=14, color="#111827"),
                        showarrow=False,
                    )
                ],
            )

            col_left, col_right = st.columns([1.05, 1.25], gap="large")

            with col_left:
                st.markdown(
                    f'''
                    <div style="
                        background-color:#F0F7FF;
                        padding:28px;
                        border-radius:14px;
                        border:1px solid #D7E8FF;
                        min-height:360px;
                        color:#003B7A;
                        font-size:20px;
                        line-height:2.1;
                    ">
                        <b>คำนวณถึงอายุ {int(retire_age)} ปี</b><br>
                        ระยะเวลาสะสมเพิ่ม: <b>{months_left:,} เดือน</b>
                        <hr style="border:0; border-top:1px solid #D1D5DB;">
                        ผู้ประกันตนจ่ายสะสม: <b>{employee_total:,.2f} บาท</b><br>
                        นายจ้างสมทบสะสม: <b>{employer_total:,.2f} บาท</b><br>
                        รัฐบาลสมทบสะสม: <b>{government_total:,.2f} บาท</b>
                        <hr style="border:0; border-top:1px solid #D1D5DB;">
                        รวมเงินสมทบทั้งหมด: <b style="font-size:26px;">{total_contribution:,.2f} บาท</b>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

            with col_right:
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="retirement_pie_chart"
                )
        else:
            st.warning("ไม่มีข้อมูลเงินสมทบสำหรับสร้างกราฟ")

        st.subheader("👴 ประมาณการสิทธิชราภาพ")

        total_months_future = len(rows)
        total_months_combined = int(current_months_paid) + total_months_future

        if section in ("m33", "m39"):
            rule = advisor.get_eligibility_rule_from_db(
                category="กรณีชราภาพ",
                section=section,
                plan_no=None
            )

            minimum_claim_age = (
                int(rule["min_age"])
                if rule and rule["min_age"] is not None
                else 55
            )

            minimum_pension_months = advisor.get_min_months_for_benefit(
                category="กรณีชราภาพ",
                section=section,
                plan_no=None
            )

            if minimum_pension_months is None:
                minimum_pension_months = 180

            if section == "m39":
                latest_row = advisor.calculate_monthly_contribution(
                    section="m39",
                    salary=0,
                    year=end_year,
                    month=12
                )
                salary_ceiling = latest_row.get("salary_base", 4800)
            else:
                salary_ceiling = advisor.get_salary_ceiling(section, end_year)

            avg_salary_60m = min(float(future_salary), salary_ceiling)

            if total_months_combined >= minimum_pension_months:

                pension_base_rate = (
                    advisor.get_benefit_parameter("old_age", "pension_base_rate")
                    or 0.20
                )

                pension_increment_rate = (
                    advisor.get_benefit_parameter("old_age", "pension_increment_rate")
                    or 0.015
                )

                increment_period_months = int(
                    advisor.get_benefit_parameter("old_age", "increment_period_months")
                    or 12
                )

                increment_period_months = int(increment_period_months)

                extra_years = max(
                    0,
                    (total_months_combined - minimum_pension_months) // increment_period_months
                )

                pension_rate = pension_base_rate + (extra_years * pension_increment_rate)
                monthly_pension = avg_salary_60m * pension_rate

                result_text = (
                    f"มีแนวโน้มได้รับ **บำนาญชราภาพ**\n\n"
                    f"- คำนวณถึงอายุที่ต้องการเกษียณ: {retire_age} ปี\n"
                    f"- เดือนสมทบที่เคยส่งมาแล้ว: {int(current_months_paid):,} เดือน\n"
                    f"- เดือนสมทบในอนาคตที่คำนวณเพิ่ม: {total_months_future:,} เดือน\n"
                    f"- เดือนสมทบรวม ณ อายุเกษียณที่ต้องการ: {total_months_combined:,} เดือน\n"
                    f"- เกณฑ์บำนาญขั้นต่ำ: {minimum_pension_months:,} เดือน\n"
                    f"- อายุรับสิทธิขั้นต่ำ: {minimum_claim_age} ปี\n"
                    f"- ฐานเงินเดือนที่ใช้ประมาณการ: {avg_salary_60m:,.2f} บาท\n"
                    f"- อัตราบำนาญประมาณการ: {pension_rate * 100:.2f}%\n"
                    f"- ประมาณการบำนาญรายเดือน: {monthly_pension:,.2f} บาท/เดือน\n\n"
                    f"หมายเหตุ: แม้คำนวณถึงอายุ {retire_age} ปี แต่จะเริ่มรับเงินได้เมื่อถึงอายุรับสิทธิขั้นต่ำ {minimum_claim_age} ปี"
                )

                if retire_age < minimum_claim_age:
                    st.info(result_text)
                else:
                    st.success(result_text)

            else:
                estimated_lump_sum = advisor.estimate_old_age_gratuity(rows)

                st.info(
                    f"มีแนวโน้มได้รับ **บำเหน็จชราภาพแบบเงินก้อน**\n\n"
                    f"- คำนวณถึงอายุที่ต้องการเกษียณ: {retire_age} ปี\n"
                    f"- เดือนสมทบที่เคยส่งมาแล้ว: {int(current_months_paid):,} เดือน\n"
                    f"- เดือนสมทบในอนาคตที่คำนวณเพิ่ม: {total_months_future:,} เดือน\n"
                    f"- เดือนสมทบรวม ณ อายุเกษียณที่ต้องการ: {total_months_combined:,} เดือน\n"
                    f"- เกณฑ์บำนาญขั้นต่ำ: {minimum_pension_months:,} เดือน\n"
                    f"- อายุรับสิทธิขั้นต่ำ: {minimum_claim_age} ปี\n"
                    f"- ประมาณการบำเหน็จเบื้องต้น: {estimated_lump_sum:,.2f} บาท\n\n"
                    f"หมายเหตุ: แม้คำนวณถึงอายุ {retire_age} ปี แต่จะรับบำเหน็จได้เมื่อถึงอายุรับสิทธิขั้นต่ำ {minimum_claim_age} ปี"
                )

        elif section == "m40":

            rule = advisor.get_eligibility_rule_from_db(
                category="กรณีชราภาพ",
                section="m40",
                plan_no=plan_no
            )

            minimum_age = (
                int(rule["min_age"])
                if rule and rule["min_age"] is not None
                else 60
            )

            minimum_months = advisor.get_min_months_for_benefit(
                category="กรณีชราภาพ",
                section="m40",
                plan_no=plan_no
            ) or 0

            pension_saving = advisor.get_old_age_saving_amount(
                section="m40",
                year=end_year,
                plan_no=plan_no
            )

            if pension_saving <= 0:
                st.warning(
                    f"""
                    ม.40 ทางเลือกที่ {plan_no} ไม่มีเงินสะสมชราภาพ
                    ดังนั้น ทางเลือกนี้ไม่มีสิทธิรับบำเหน็จชราภาพ
                    """
                )

            else:

                retirement_lump_sum = (
                    pension_saving + float(extra_saving_per_month)
                ) * total_months_combined

                bonus_amount = (
                    advisor.get_benefit_parameter(
                        "old_age",
                        "bonus_amount",
                        "m40"
                    ) or 0
                )

                bonus = 0

                if (
                    plan_no == 3
                    and minimum_months > 0
                    and total_months_combined >= minimum_months
                ):
                    bonus = bonus_amount

                result_text = (
                    f"ประมาณการบำเหน็จชราภาพ ม.40 ทางเลือกที่ {plan_no}\n\n"
                    f"- คำนวณถึงอายุที่ต้องการเกษียณ: {retire_age} ปี\n"
                    f"- อายุรับสิทธิขั้นต่ำ: {minimum_age} ปี\n"
                    f"- เงินสะสมชราภาพจากเงินสมทบ: {pension_saving:,.2f} บาท/เดือน\n"
                    f"- เงินออมเพิ่ม: {extra_saving_per_month:,.2f} บาท/เดือน\n"
                    f"- เดือนสมทบที่เคยส่งมาแล้ว: {int(current_months_paid):,} เดือน\n"
                    f"- เดือนสมทบในอนาคตที่คำนวณเพิ่ม: {total_months_future:,} เดือน\n"
                    f"- รวมเดือนสมทบทั้งหมดโดยประมาณ: {total_months_combined:,} เดือน\n"
                    f"- เงินบำเหน็จประมาณการ: {retirement_lump_sum:,.2f} บาท\n"
                )

                if plan_no == 3:
                    result_text += (
                        f"- เกณฑ์รับเงินเพิ่ม: {minimum_months:,} เดือน\n"
                        f"- เงินเพิ่มกรณีครบเกณฑ์: {bonus:,.2f} บาท\n"
                    )

                result_text += (
                    f"\nรวมประมาณการเบื้องต้น: "
                    f"{retirement_lump_sum + bonus:,.2f} บาท\n\n"
                    f"หมายเหตุ: แม้คำนวณถึงอายุ {retire_age} ปี "
                    f"แต่จะสามารถรับเงินได้เมื่อมีอายุครบ "
                    f"{minimum_age} ปีบริบูรณ์"
                )

                if retire_age < minimum_age:
                    st.info(result_text)
                else:
                    st.success(result_text)

        with st.expander("ดูรายละเอียดเงินสมทบรายเดือนจนถึงเกษียณ", expanded=False):
            df = pd.DataFrame([
                {
                    "ปี": r["year"],
                    "เดือน": r["month"],
                    "เงินเดือนประมาณการ": r.get("estimated_salary", 0),
                    "ฐานคำนวณ": r.get("salary_base", 0),
                    "ผู้ประกันตนจ่าย": r["employee_contribution"],
                    "นายจ้างสมทบ": r["employer_contribution"],
                    "รัฐบาลสมทบ": r["government_contribution"],
                    "รวมเงินสมทบ": r["total_contribution"],
                    "อัตราเงินสมทบ": r["description"],
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
                "อัตราเงินสมทบ": "",
            }

            df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
            df = df.replace({None: "", "None": ""}).fillna("")

            styled_df = build_styled_dataframe(df)

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )

with tab2:

    st.subheader("🎯 วางแผนตามเป้าหมายเงินเกษียณ")

    profile = st.session_state.get("profile", {})

    if not profile.get("is_from_page1", False):
        st.warning(
            """
    ⚠️ กรุณากรอกข้อมูลในหน้า "ตรวจสอบสิทธิประโยชน์" ก่อน เพื่อให้ระบบทราบข้อมูลพื้นฐานของผู้ประกันตน
    """
        )

    if "retirement_result" not in st.session_state:
        st.info(
            """
    ℹ️ แนะนำให้ตรวจสอบค่าประมาณการใน Tab "📈 ประมาณการเกษียณ" ก่อน

    โดยเฉพาะ:
    - อายุปัจจุบัน
    - อายุที่ต้องการเกษียณ
    - เงินเดือนปัจจุบัน
    - เงินเดือนเพิ่มเฉลี่ยต่อปี (%)
    - จำนวนเดือนที่ส่งเงินสมทบมาแล้ว

    เพื่อให้การวิเคราะห์เป้าหมายเกษียณแม่นยำขึ้น
    """
        )

    goal_col1, goal_col2 = st.columns(2)

    with goal_col1:
        if section in ("m33", "m39"):
            target_retirement_amount = st.number_input(
                "ต้องการบำนาญประมาณเดือนละ",
                min_value=0.0,
                value=st.session_state["target_monthly_pension_value"],
                step=1000.0,
                format="%.2f",
                key="target_monthly_pension_input"
            )

            st.session_state["target_monthly_pension_value"] = float(target_retirement_amount)

        else:
            target_retirement_amount = st.number_input(
                "ต้องการบำเหน็จเงินก้อนประมาณ",
                min_value=0.0,
                value=st.session_state["target_lump_sum_value"],
                step=10000.0,
                format="%.2f",
                key="target_lump_sum_input"
            )

            st.session_state["target_lump_sum_value"] = float(target_retirement_amount)
            
        st.caption(f"💰 {target_retirement_amount:,.2f} บาท")

    with goal_col2:
        st.info("จะประเมินจากอายุขั้นต่ำที่ได้รับสิทธิตามมาตราที่เลือก")

    st.session_state["goal_target_retirement_amount"] = float(target_retirement_amount)

    st.session_state.setdefault("profile", {})

    if section in ("m33", "m39"):
        st.session_state["profile"]["target_monthly_pension"] = float(target_retirement_amount)
    else:
        st.session_state["profile"]["target_lump_sum"] = float(target_retirement_amount)

    if st.button("🎯 วิเคราะห์เป้าหมายเกษียณ", key="analyze_retirement_goal"):
        st.session_state["goal_analyzed"] = True

    if st.session_state.get("goal_analyzed", False):

        current_months_paid_int = int(current_months_paid)

        rule = advisor.get_eligibility_rule_from_db(
            category="กรณีชราภาพ",
            section=section,
            plan_no=plan_no
        )

        min_old_age_claim_age = (
            int(rule["min_age"])
            if rule and rule["min_age"] is not None
            else 55 if section in ("m33", "m39") else 60
        )

        claim_age = min_old_age_claim_age

        months_until_claim_age = max(
            0,
            int(claim_age - current_age) * 12
        )

        possible_total_months_at_claim_age = (
            current_months_paid_int + months_until_claim_age
        )

        if section in ("m33", "m39"):

            current_year = int(st.session_state["profile"]["current_year"])
            current_age = int(st.session_state["profile"]["age"])
            claim_year = current_year + (claim_age - current_age)

            if section == "m39":
                latest_row = advisor.calculate_monthly_contribution(
                    section="m39",
                    salary=0,
                    year=claim_year,
                    month=12
                )
                salary_ceiling = latest_row.get("salary_base", 4800)
            else:
                salary_ceiling = advisor.get_salary_ceiling(section, claim_year)

            minimum_pension_months = advisor.get_min_months_for_benefit(
                category="กรณีชราภาพ",
                section=section,
                plan_no=None
            )

            if minimum_pension_months is None:
                minimum_pension_months = 180

            pension_base_rate = (
                advisor.get_benefit_parameter("old_age", "pension_base_rate")
                or 0.20
            )

            pension_increment_rate = (
                advisor.get_benefit_parameter("old_age", "pension_increment_rate")
                or 0.015
            )

            increment_period_months = int(
                advisor.get_benefit_parameter("old_age", "increment_period_months")
                or 12
            )

            target_pension = float(target_retirement_amount)

            if target_pension <= 0:
                st.warning("กรุณากรอกเป้าหมายบำนาญมากกว่า 0 บาท")
            else:
                required_rate = target_pension / salary_ceiling

                if required_rate <= pension_base_rate:
                    required_total_months = minimum_pension_months
                else:
                    required_extra_periods = math.ceil(
                        (required_rate - pension_base_rate) / pension_increment_rate
                    )
                    required_total_months = (
                        minimum_pension_months
                        + required_extra_periods * increment_period_months
                    )

                required_total_months = max(
                    minimum_pension_months,
                    required_total_months
                )

                months_needed_more = max(
                    0,
                    required_total_months - current_months_paid_int
                )

                years_needed_more = months_needed_more / 12
                required_age = float(current_age) + years_needed_more

                possible_extra_periods = max(
                    0,
                    (
                        possible_total_months_at_claim_age
                        - minimum_pension_months
                    ) // increment_period_months
                )

                possible_rate = (
                    pension_base_rate
                    + (possible_extra_periods * pension_increment_rate)
                    if possible_total_months_at_claim_age >= minimum_pension_months
                    else 0
                )

                possible_pension = salary_ceiling * possible_rate

                if possible_total_months_at_claim_age >= minimum_pension_months:
                    required_salary_for_goal = (
                        target_pension / possible_rate
                        if possible_rate > 0
                        else 0
                    )
                else:
                    required_salary_for_goal = 0

                st.markdown(f"""
                ต้องการบำนาญประมาณ: **{target_pension:,.2f} บาท/เดือน**

                เพดานฐานค่าจ้างที่ใช้ประเมินในปีที่คาดว่าจะได้รับสิทธิ ({claim_year}): **{salary_ceiling:,.2f} บาท**

                จากเพดานฐานค่าจ้างนี้ หากต้องการบำนาญ {target_pension:,.2f} บาท/เดือน  
                ต้องใช้อัตราบำนาญประมาณ **{required_rate * 100:.2f}%**

                ตามสูตรบำนาญชราภาพ:
                - ส่งครบ {minimum_pension_months:,} เดือน ได้อัตราบำนาญเริ่มต้น {pension_base_rate * 100:.2f}%
                - หลังจากนั้น ส่งเพิ่มครบทุก {increment_period_months:,} เดือน อัตราบำนาญเพิ่มอีก {pension_increment_rate * 100:.2f}%

                จึงต้องมีเดือนสมทบรวมประมาณ **{required_total_months:,} เดือน**

                ตอนนี้ส่งมาแล้ว **{current_months_paid_int:,} เดือน**  
                จึงต้องส่งเพิ่มอีกประมาณ **{months_needed_more:,} เดือน**

                เมื่อเทียบกับอายุปัจจุบัน {current_age:.0f} ปี  
                จะต้องส่งต่อไปจนถึงอายุประมาณ **{required_age:.1f} ปี**
                เพื่อให้มีจำนวนเดือนสมทบเพียงพอกับเป้าหมายบำนาญนี้
                """)

                if required_age <= claim_age:
                    st.success(
                        f"เป้าหมายนี้มีแนวโน้มทำได้ภายในอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                        f"หากส่งสมทบต่อเนื่องและฐานค่าจ้างถึง {salary_ceiling:,.2f} บาท"
                    )
                else:
                    st.error(
                        f"เป้าหมายนี้อาจทำไม่ทันภายในอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                        f"เพราะจำนวนเดือนสมทบไม่เพียงพอ "
                        f"จึงต้องส่งต่อถึงอายุประมาณ {required_age:.1f} ปี"
                    )

                if possible_total_months_at_claim_age >= minimum_pension_months:
                    st.info(
                        f"ถ้าประเมินถึงอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                        f"จะมีเดือนสมทบรวมประมาณ {possible_total_months_at_claim_age:,} เดือน "
                        f"อัตราบำนาญประมาณ {possible_rate * 100:.2f}% "
                        f"และบำนาญประมาณ {possible_pension:,.2f} บาท/เดือน"
                    )

                    if required_salary_for_goal > salary_ceiling:
                        st.warning(
                            f"เพื่อให้ได้บำนาญ {target_pension:,.2f} บาท/เดือน "
                            f"ภายในอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                            f"ต้องมีฐานค่าจ้างเฉลี่ยประมาณ {required_salary_for_goal:,.2f} บาท "
                            f"แต่เพดานฐานค่าจ้างที่ใช้ประเมินอยู่ที่ {salary_ceiling:,.2f} บาท "
                            f"จึงอาจไม่สามารถบรรลุเป้าหมายดังกล่าวได้"
                        )
                    else:
                        st.success(
                            f"ฐานค่าจ้างเฉลี่ยที่ต้องมีเพื่อให้ได้บำนาญ "
                            f"{target_pension:,.2f} บาท/เดือน "
                            f"คือประมาณ {required_salary_for_goal:,.2f} บาท "
                            f"ซึ่งยังไม่เกินเพดานฐานค่าจ้าง {salary_ceiling:,.2f} บาท "
                            f"จึงมีความเป็นไปได้ที่จะบรรลุเป้าหมายภายในอายุขั้นต่ำที่ได้รับสิทธิ {claim_age} ปี"
                        )
                else:
                    retirement_result = st.session_state.get("retirement_result", {})
                    rows = retirement_result.get("rows", [])

                    estimated_lump_sum = advisor.estimate_old_age_gratuity(rows)

                    st.warning(
                        f"ถ้าประเมินถึงอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                        f"จะมีเดือนสมทบรวมเพียง {possible_total_months_at_claim_age:,} เดือน "
                        f"ยังไม่ครบ {minimum_pension_months:,} เดือน สำหรับการได้รับสิทธิบำนาญ"
                    )

                    st.info(
                        f"""
                        เนื่องจากยังไม่ครบ {minimum_pension_months:,} เดือน จึงยังไม่มีสิทธิรับบำนาญรายเดือน  
                        แต่มีแนวโน้มได้รับ **บำเหน็จชราภาพแบบเงินก้อน**

                        ประมาณการบำเหน็จเบื้องต้น: **{estimated_lump_sum:,.2f} บาท**

                        หมายเหตุ: จำนวนนี้เป็นการประเมินเบื้องต้นจากเงินสมทบฝ่ายผู้ประกันตนและนายจ้างที่คำนวณได้ ยังไม่รวมผลประโยชน์ตอบแทนตามที่สำนักงานประกันสังคมประกาศ
                        """
                    )

        elif section == "m40":

            if plan_no == 1:
                st.warning("ม.40 ทางเลือกที่ 1 ไม่มีสิทธิชราภาพ จึงไม่สามารถวางแผนบำเหน็จชราภาพได้")

            else:
                target_lump_sum = float(target_retirement_amount)

                pension_saving = advisor.get_old_age_saving_amount(
                    section="m40",
                    year=int(start_year),
                    plan_no=plan_no
                )

                monthly_saving = pension_saving + float(extra_saving_per_month)

                if monthly_saving <= 0:
                    st.warning("เงินสะสมต่อเดือนต้องมากกว่า 0 บาท")
                else:
                    m40_rule = advisor.get_eligibility_rule_from_db(
                        category="กรณีชราภาพ",
                        section="m40",
                        plan_no=plan_no
                    )

                    m40_min_months = (
                        int(m40_rule["min_months_paid"])
                        if m40_rule and m40_rule["min_months_paid"] is not None
                        else 0
                    )

                    m40_min_age = (
                        int(m40_rule["min_age"])
                        if m40_rule and m40_rule["min_age"] is not None
                        else min_old_age_claim_age
                    )

                    bonus_amount = (
                        advisor.get_benefit_parameter(
                            "old_age",
                            "bonus_amount",
                            "m40"
                        )
                        or 0
                    )

                    required_months = math.ceil(target_lump_sum / monthly_saving)

                    bonus = 0

                    if (
                        plan_no == 3
                        and m40_min_months > 0
                        and required_months >= m40_min_months
                    ):
                        bonus = bonus_amount
                        adjusted_target = max(0, target_lump_sum - bonus)
                        required_months = math.ceil(adjusted_target / monthly_saving)
                        required_months = max(required_months, m40_min_months)

                    months_needed_more = max(
                        0,
                        required_months - current_months_paid_int
                    )

                    years_needed_more = months_needed_more / 12
                    required_age = float(current_age) + years_needed_more

                    possible_lump_sum = (
                        monthly_saving
                        * possible_total_months_at_claim_age
                    )

                    if (
                        plan_no == 3
                        and m40_min_months > 0
                        and possible_total_months_at_claim_age >= m40_min_months
                    ):
                        possible_lump_sum += bonus_amount

                    st.markdown(f"""
                        ### ผลวิเคราะห์เป้าหมายบำเหน็จ ม.40

                        ต้องการบำเหน็จเงินก้อน: **{target_lump_sum:,.2f} บาท**

                        ทางเลือก ม.40: **ทางเลือกที่ {plan_no}**

                        เงินสะสมชราภาพจากเงินสมทบ: **{pension_saving:,.2f} บาท/เดือน**

                        เงินออมเพิ่ม: **{extra_saving_per_month:,.2f} บาท/เดือน**

                        รวมเงินสะสมต่อเดือน: **{monthly_saving:,.2f} บาท/เดือน**

                        ต้องมีเดือนสมทบรวมประมาณ: **{required_months:,} เดือน**

                        ส่งมาแล้ว: **{current_months_paid_int:,} เดือน**

                        ต้องส่งเพิ่มประมาณ: **{months_needed_more:,} เดือน**

                        คิดเป็นต้องส่งต่อจนถึงอายุประมาณ: **{required_age:.1f} ปี**
                        """
                    )

                    if required_age <= claim_age:
                        st.success(
                            f"หากยังคงส่งเงินตามสมมติฐานปัจจุบัน "
                            f"มีโอกาสบรรลุเป้าหมายเงินก้อน {target_lump_sum:,.0f} บาท "
                            f"ได้ภายในอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ"
                        )
                    else:
                        st.error(
                            f"หากยังคงส่งเงินในอัตราปัจจุบัน "
                            f"อาจยังไม่เพียงพอต่อเป้าหมายเงินก้อนที่ตั้งไว้ "
                            f"เพราะต้องส่งต่อถึงอายุประมาณ {required_age:.1f} ปี "
                            f"จึงควรพิจารณาเพิ่มเงินออมรายเดือน ลดเป้าหมายเงินก้อน "
                            f"หรือขยายอายุเกษียณ"
                        )

                    st.info(
                        f"ถ้าประเมินถึงอายุ {claim_age} ปี ที่เป็นอายุขั้นต่ำในการรับสิทธิ "
                        f"จะมีเดือนสมทบรวมประมาณ {possible_total_months_at_claim_age:,} เดือน "
                        f"และมีบำเหน็จประมาณ {possible_lump_sum:,.2f} บาท"
                    )