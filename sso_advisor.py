import json
import sqlite3
import duckdb
from typing import Any, Dict, List, Optional

class SSOMasterAdvisor:

    def __init__(self, json_path: str = None, db_path: str = "sso_advisor.db"):
            self.db_path = db_path
            self.db = {}

    def _connect_db(self):
            return sqlite3.connect(self.db_path)

    def _section_key(self, section: str) -> str:
            mapping = {
                "33": "m33",
                "39": "m39",
                "40": "m40",
                "ม33": "m33",
                "ม39": "m39",
                "ม40": "m40",
                "มาตรา 33": "m33",
                "มาตรา 39": "m39",
                "มาตรา 40": "m40",
                "m33": "m33",
                "m39": "m39",
                "m40": "m40",
            }
            key = mapping.get(str(section).strip().lower(), str(section).strip().lower())
            if key not in ("m33", "m39", "m40"):
                raise ValueError("section ต้องเป็น m33, m39 หรือ m40")
            return key
    
    def get_section_label_map(self):
            return {
                "มาตรา 33": "m33",
                "มาตรา 39": "m39",
                "มาตรา 40": "m40",
            }

    def get_section_reverse_map(self):
            section_map = self.get_section_label_map()
            return {v: k for k, v in section_map.items()}

    def get_app_setting(self, key, default=None):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT setting_value
                FROM app_settings
                WHERE setting_key = ?
            """, (key,))

            row = cur.fetchone()
            conn.close()

            if row is None:
                return default

            return row[0]

    def get_salary_ceiling(self, section: str, year: int) -> float:
            section = self._section_key(section)
            year = int(year)

            conn = self._connect_db()
            cur = conn.cursor()

            if year < 2559:
                cur.execute("""
                    SELECT salary_ceiling
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_before_2559'
                    AND salary_ceiling IS NOT NULL
                    LIMIT 1
                """, (section,))
            elif year > 2575:
                cur.execute("""
                    SELECT salary_ceiling
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_after_2575'
                    AND salary_ceiling IS NOT NULL
                    LIMIT 1
                """, (section,))
            else:
                cur.execute("""
                    SELECT salary_ceiling
                    FROM contribution_rules
                    WHERE section = ?
                    AND year = ?
                    AND salary_ceiling IS NOT NULL
                    LIMIT 1
                """, (section, year))

            row = cur.fetchone()
            conn.close()

            if row:
                return float(row[0])

            raise ValueError(f"ไม่พบ salary_ceiling ของ {section} ปี {year} ใน Database")

    def get_benefit_parameter(
            self,
            benefit_type,
            parameter_name,
            section=None
        ):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
            SELECT parameter_value
            FROM benefit_parameters
            WHERE benefit_type = ?
            AND parameter_name = ?
            AND (section = ? OR section IS NULL)
            ORDER BY section DESC
            LIMIT 1
            """, (
                benefit_type,
                parameter_name,
                section
            ))

            row = cur.fetchone()
            conn.close()

            if row:
                return float(row[0])

            return None
    
    def get_min_months_for_benefit(self, category, section, plan_no=None):
            section = self._section_key(section)

            conn = self._connect_db()
            cur = conn.cursor()

            if plan_no is None:
                cur.execute("""
                    SELECT MAX(min_months_paid)
                    FROM benefit_details
                    WHERE category = ?
                    AND section = ?
                    AND min_months_paid IS NOT NULL
                """, (category, section))
            else:
                cur.execute("""
                    SELECT MAX(min_months_paid)
                    FROM benefit_details
                    WHERE category = ?
                    AND section = ?
                    AND (plan_no IS NULL OR plan_no = ?)
                    AND min_months_paid IS NOT NULL
                """, (category, section, int(plan_no)))

            row = cur.fetchone()
            conn.close()

            if row and row[0] is not None:
                return int(row[0])

            return None

    def _get_contribution_periods(self, section: str, year: int) -> List[Dict[str, Any]]:
            section = self._section_key(section)
            year = int(year)

            conn = self._connect_db()
            cur = conn.cursor()

            if year < 2559:
                cur.execute("""
                    SELECT *
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_before_2559'
                    ORDER BY start_month
                """, (section,))

            elif year > 2575:
                cur.execute("""
                    SELECT *
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_after_2575'
                    ORDER BY start_month
                """, (section,))

            else:
                cur.execute("""
                    SELECT *
                    FROM contribution_rules
                    WHERE section = ?
                    AND year = ?
                    ORDER BY start_month
                """, (section, year))

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            conn.close()

            periods = []

            for row in rows:
                r = dict(zip(columns, row))

                period = {
                    "start_month": r.get("start_month"),
                    "end_month": r.get("end_month"),
                    "employee_rate": r.get("employee_rate"),
                    "employer_rate": r.get("employer_rate"),
                    "government_rate": r.get("government_rate"),
                    "employee_fixed_contribution": r.get("employee_fixed"),
                    "employer_fixed_contribution": r.get("employer_fixed"),
                    "government_fixed_contribution": r.get("government_fixed"),
                    "salary_base": r.get("salary_base"),
                    "salary_floor": r.get("salary_floor"),
                    "salary_ceiling": r.get("salary_ceiling"),
                    "plan_no": r.get("plan_no"),
                    "description": r.get("description"),
                }

                if section == "m40":
                    period["calculation_method"] = "plan_fixed"
                    period["plan_costs"] = {
                        "1": r.get("plan1_employee_fixed"),
                        "2": r.get("plan2_employee_fixed"),
                        "3": r.get("plan3_employee_fixed"),
                    }
                    period["government_plan_costs"] = {
                        "1": r.get("plan1_government_fixed"),
                        "2": r.get("plan2_government_fixed"),
                        "3": r.get("plan3_government_fixed"),
                    }

                elif r.get("employee_fixed") is not None:
                    period["calculation_method"] = "fixed"

                else:
                    period["calculation_method"] = "rate"

                periods.append(period)

            return periods

    def _get_contribution_period(self, section: str, year: int, month: int) -> Dict[str, Any]:
            if not 1 <= int(month) <= 12:
                raise ValueError("month ต้องอยู่ระหว่าง 1 ถึง 12")

            periods = self._get_contribution_periods(section, year)

            for period in periods:
                start_month = int(period.get("start_month") or 1)
                end_month = int(period.get("end_month") or 12)

                if start_month <= int(month) <= end_month:
                    return period

            raise ValueError(
                f"ไม่พบกติกาเงินสมทบของ {section} ปี {year} เดือน {month}"
            )
    
    def calculate_monthly_contribution(
            self,
            section: str,
            salary: float = 0,
            year: int = 2568,
            month: int = 1,
            plan_no: Optional[int] = None,
        ) -> Dict[str, Any]:
            key = self._section_key(section)
            period = self._get_contribution_period(key, year, month)
            method = period.get("calculation_method", "rate")

            result: Dict[str, Any] = {
                "section": key,
                "year": int(year),
                "month": int(month),
                "period": period,
                "description": period.get("description", ""),
                "salary_input": float(salary or 0),
                "salary_base": 0.0,
                "employee_contribution": 0.0,
                "employer_contribution": 0.0,
                "government_contribution": 0.0,
                "total_contribution": 0.0,
            }

            if method == "rate":
                if period.get("salary_floor") is None:
                    raise ValueError("ไม่พบ salary_floor ใน contribution_rules")

                floor = float(period["salary_floor"])
                if period.get("salary_ceiling") is None:
                    raise ValueError(
                        f"ไม่พบ salary_ceiling ของ {key} ปี {year} เดือน {month} "
                        "กรุณาเพิ่มข้อมูลใน contribution_rules"
                    )
                ceiling = float(period["salary_ceiling"])
                base = min(max(float(salary or 0), floor), ceiling)
                employee_rate = float(period.get("employee_rate", 0))
                employer_rate = float(period.get("employer_rate", employee_rate))
                employee = base * employee_rate
                employer = base * employer_rate
                government_rate = float(period.get("government_rate", 0))
                government = base * government_rate
                if period.get("employee_max_contribution") is not None:
                    employee = min(employee, float(period["employee_max_contribution"]))
                if period.get("employer_max_contribution") is not None:
                    employer = min(employer, float(period["employer_max_contribution"]))
                if period.get("government_max_contribution") is not None:
                    government = min(government, float(period["government_max_contribution"]))
                result.update({
                    "calculation_method": "rate",
                    "salary_base": base,
                    "salary_floor": floor,
                    "salary_ceiling": ceiling,
                    "employee_rate": employee_rate,
                    "employer_rate": employer_rate,
                    "government_rate": government_rate,
                    "employee_contribution": employee,
                    "employer_contribution": employer,
                    "government_contribution": government,
                    "total_contribution": employee + employer + government,
                })
                return result

            if method == "fixed":
                employee = float(period.get("employee_fixed_contribution") or 0)
                employer = float(period.get("employer_fixed_contribution") or 0)

                if period.get("government_fixed_contribution") is not None:
                    government = float(period.get("government_fixed_contribution") or 0)
                else:
                    salary_base = float(period.get("salary_base") or 0)
                    government_rate = float(period.get("government_rate") or 0)
                    government = salary_base * government_rate

                result.update({
                    "calculation_method": "fixed",
                    "employee_contribution": employee,
                    "employer_contribution": employer,
                    "government_contribution": government,
                    "government_rate": float(period.get("government_rate") or 0),
                    "salary_base": float(
                        period.get("salary_base") or 0
                    ),
                    "total_contribution": employee + employer + government,
                })
                return result

            if method == "plan_fixed":
                if plan_no is None:
                    plan_no = 1
                costs = period.get("plan_costs", {})
                government_costs = period.get("government_plan_costs", {})
                employee = float(costs.get(str(plan_no), 0))
                government = float(government_costs.get(str(plan_no), 0))
                result.update({
                    "calculation_method": "plan_fixed",
                    "plan_no": int(plan_no),
                    "employee_contribution": employee,
                    "employer_contribution": 0.0,
                    "government_contribution": government,
                    "total_contribution": employee + government,
                })
                return result

            raise ValueError(f"ไม่รู้จัก calculation_method: {method}")

    def calculate_contribution_range_linear_annual(
            self,
            section: str,
            start_salary: float,
            current_salary: float,
            start_year: int,
            end_year: int,
            end_month: int = 12,
            start_month: int = 1,
            plan_no: Optional[int] = None,
        ) -> Dict[str, Any]:
            start_year = int(start_year)
            end_year = int(end_year)
            start_month = int(start_month)
            end_month = int(end_month)
            if end_year < start_year or (end_year == start_year and end_month < start_month):
                return {
                    "section": self._section_key(section),
                    "rows": [],
                    "months": 0,
                    "employee_total": 0.0,
                    "employer_total": 0.0,
                    "government_total": 0.0,
                    "total_contribution": 0.0,
                }

            span_years = max(end_year - start_year, 0)
            salary_by_year: Dict[int, float] = {}
            for year in range(start_year, end_year + 1):
                if span_years == 0:
                    salary_by_year[year] = float(current_salary)
                else:
                    progress = (year - start_year) / span_years
                    salary_by_year[year] = float(start_salary) + (float(current_salary) - float(start_salary)) * progress

            rows: List[Dict[str, Any]] = []
            y, m = start_year, start_month
            while (y, m) <= (end_year, end_month):
                salary_for_month = salary_by_year[y]
                row = self.calculate_monthly_contribution(section, salary_for_month, y, m, plan_no)
                row["estimated_salary"] = salary_for_month
                rows.append(row)
                m += 1
                if m > 12:
                    m = 1
                    y += 1

            employee_total = sum(r["employee_contribution"] for r in rows)
            employer_total = sum(r["employer_contribution"] for r in rows)
            government_total = sum(r.get("government_contribution", 0) for r in rows)
            return {
                "section": self._section_key(section),
                "rows": rows,
                "months": len(rows),
                "employee_total": employee_total,
                "employer_total": employer_total,
                "government_total": government_total,
                "total_contribution": employee_total + employer_total + government_total,
            }
    
    def get_old_age_saving_amount(self, section, year, plan_no=None):
            section = self._section_key(section)

            if section != "m40" or plan_no is None:
                return 0

            col_map = {
                1: "plan1_old_age_saving_amount",
                2: "plan2_old_age_saving_amount",
                3: "plan3_old_age_saving_amount",
            }

            column = col_map.get(int(plan_no))
            if column is None:
                return 0

            year = int(year)

            conn = self._connect_db()
            cur = conn.cursor()

            if year < 2559:
                cur.execute(f"""
                    SELECT {column}
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_before_2559'
                    AND {column} IS NOT NULL
                    LIMIT 1
                """, (section,))
            elif year > 2575:
                cur.execute(f"""
                    SELECT {column}
                    FROM contribution_rules
                    WHERE section = ?
                    AND rule_type = 'default_after_2575'
                    AND {column} IS NOT NULL
                    LIMIT 1
                """, (section,))
            else:
                cur.execute(f"""
                    SELECT {column}
                    FROM contribution_rules
                    WHERE section = ?
                    AND year = ?
                    AND {column} IS NOT NULL
                    LIMIT 1
                """, (section, year))

            row = cur.fetchone()
            conn.close()

            return float(row[0]) if row and row[0] is not None else 0

    def estimate_old_age_gratuity(self, future_rows):
            total = 0.0

            for r in future_rows:
                total += float(r.get("employee_contribution", 0))
                total += float(r.get("employer_contribution", 0))

            return total

    def get_benefit_categories(self):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT DISTINCT category
                FROM benefit_details
                ORDER BY id
            """)

            rows = [r[0] for r in cur.fetchall()]
            conn.close()

            return rows

    def get_benefit_details_from_db(
            self,
            category,
            section,
            data_type,
            plan_no=None,
            months_paid=None
        ):
            conn = self._connect_db()
            cur = conn.cursor()

            paid = int(months_paid or 0)

            if plan_no is None:
                cur.execute("""
                    SELECT detail
                    FROM benefit_details
                    WHERE category = ?
                    AND section = ?
                    AND data_type = ?
                    AND (min_months_paid IS NULL OR ? >= min_months_paid)
                    AND (max_months_paid IS NULL OR ? <= max_months_paid)
                """, (category, section, data_type, paid, paid))
            else:
                cur.execute("""
                    SELECT detail
                    FROM benefit_details
                    WHERE category = ?
                    AND section = ?
                    AND data_type = ?
                    AND (plan_no IS NULL OR plan_no = ?)
                    AND (min_months_paid IS NULL OR ? >= min_months_paid)
                    AND (max_months_paid IS NULL OR ? <= max_months_paid)
                """, (category, section, data_type, int(plan_no), paid, paid))

            rows = [r[0] for r in cur.fetchall()]
            conn.close()
            return rows

    def get_benefit_benefits(
            self,
            category,
            section,
            plan_no=None,
            months_paid=None,
            age=None
        ):
            section = self._section_key(section)

            return self.get_benefit_details_from_db(
                category=category,
                section=section,
                data_type="benefit",
                plan_no=plan_no,
                months_paid=months_paid
            )

    def get_benefit_conditions(
            self,
            category,
            section,
            plan_no=None,
            months_paid=None,
            age=None
        ):
            section = self._section_key(section)

            return self.get_benefit_details_from_db(
                category=category,
                section=section,
                data_type="condition",
                plan_no=plan_no,
                months_paid=months_paid
            )

    def get_benefit_notes(
            self,
            category,
            section,
            plan_no=None,
            months_paid=None,
            age=None
        ):
            section = self._section_key(section)

            return self.get_benefit_details_from_db(
                category=category,
                section=section,
                data_type="note",
                plan_no=plan_no,
                months_paid=months_paid
            )

    def get_eligibility_rule_from_db(self, category, section, plan_no=None):
            section = self._section_key(section)
            conn = self._connect_db()
            cur = conn.cursor()

            if plan_no is None:
                cur.execute("""
                    SELECT is_covered, min_months_paid, window_months, min_age
                    FROM benefit_eligibility_rules
                    WHERE category = ?
                    AND section = ?
                    AND plan_no IS NULL
                    LIMIT 1
                """, (category, section))
            else:
                cur.execute("""
                    SELECT is_covered, min_months_paid, window_months, min_age
                    FROM benefit_eligibility_rules
                    WHERE category = ?
                    AND section = ?
                    AND plan_no = ?
                    LIMIT 1
                """, (category, section, int(plan_no)))

            row = cur.fetchone()
            conn.close()

            if not row:
                return None

            return {
                "is_covered": bool(row[0]),
                "min_months_paid": row[1],
                "window_months": row[2],
                "min_age": row[3],
            }

    def check_benefit_eligibility(
            self,
            category,
            section,
            months_paid,
            plan_no=None,
            age=None
        ):
            section = self._section_key(section)
            months_paid = int(months_paid or 0)
            age_value = None if age is None else int(age)

            rule = self.get_eligibility_rule_from_db(
                category=category,
                section=section,
                plan_no=plan_no
            )

            if not rule:
                return {
                    "required": None,
                    "eligible": False,
                    "status": "no_rule",
                    "message": "ไม่พบเงื่อนไขสิทธิประโยชน์ในฐานข้อมูล",
                }

            if not rule.get("is_covered"):
                return {
                    "required": None,
                    "eligible": False,
                    "status": "not_covered",
                    "message": f"{section} ไม่มีสิทธิประโยชน์{category}",
                }

            required_months = rule.get("min_months_paid")
            window_months = rule.get("window_months")
            min_age = rule.get("min_age")

            if category == "กรณีชราภาพ" and section in ("m33", "m39"):
                pension_months = self.get_min_months_for_benefit(
                    category=category,
                    section=section,
                    plan_no=plan_no
                )

                if pension_months is not None:
                    required_months = pension_months

            if min_age is not None and age_value is not None and age_value < int(min_age):
                return {
                    "required": required_months,
                    "eligible": False,
                    "status": "waiting_age",
                    "message": f"ยังไม่ถึงเกณฑ์อายุ ต้องอายุครบ {int(min_age)} ปี",
                }

            if required_months is not None and months_paid < int(required_months):
                if window_months is not None:
                    message = (
                        f"ยังไม่มีสิทธิ ต้องส่งเงินสมทบอย่างน้อย "
                        f"{int(required_months)} เดือน ภายใน {int(window_months)} เดือน"
                    )
                else:
                    message = (
                        f"ยังไม่มีสิทธิ ต้องส่งเงินสมทบอย่างน้อย "
                        f"{int(required_months)} เดือน"
                    )

                return {
                    "required": int(required_months),
                    "eligible": False,
                    "status": "not_enough_months",
                    "message": message,
                }

            return {
                "required": required_months,
                "eligible": True,
                "status": "eligible",
                "message": "มีสิทธิตามเกณฑ์เบื้องต้น",
            }

    def get_sections_for_comparison(self):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT section, plan_no, title
                FROM section_summary
                ORDER BY
                    CASE section
                        WHEN 'm33' THEN 1
                        WHEN 'm39' THEN 2
                        WHEN 'm40' THEN 3
                        ELSE 9
                    END,
                    COALESCE(plan_no, 0)
            """)

            rows = cur.fetchall()
            conn.close()

            return [
                {
                    "section": row[0],
                    "plan_no": row[1],
                    "title": row[2]
                }
                for row in rows
            ]
    
    def get_section_summary_from_db(self):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    section,
                    plan_no,
                    title,
                    target_group,
                    contribution_text,
                    rights_summary,
                    old_age_text
                FROM section_summary
                ORDER BY id
            """)

            rows = cur.fetchall()
            conn.close()

            return [
                {
                    "มาตรา": r[2],
                    "กลุ่มเป้าหมาย": r[3],
                    "เงินสมทบ": r[4],
                    "สิทธิหลัก": r[5],
                    "ชราภาพ": r[6],
                }
                for r in rows
            ]

    def get_benefit_checklist_from_db(self):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    CASE
                        WHEN section='m33' THEN 'ม.33'
                        WHEN section='m39' THEN 'ม.39'
                        WHEN section='m40' AND plan_no=1 THEN 'ม.40 ทางเลือก 1'
                        WHEN section='m40' AND plan_no=2 THEN 'ม.40 ทางเลือก 2'
                        WHEN section='m40' AND plan_no=3 THEN 'ม.40 ทางเลือก 3'
                    END AS section_name,
                    category,
                    display_text
                FROM benefit_checklist
                ORDER BY section, plan_no, id
            """)

            rows = cur.fetchall()
            conn.close()

            return rows

    def get_duckdb_comparison_table(self):
            con = duckdb.connect()

            con.execute("INSTALL sqlite;")
            con.execute("LOAD sqlite;")

            df = con.execute(f"""
                WITH coverage AS (
                    SELECT
                        section,
                        plan_no,
                        COUNT(*) AS total_cases,
                        SUM(has_benefit) AS covered_cases,
                        ROUND(SUM(has_benefit) * 100.0 / COUNT(*), 2) AS coverage_percent
                    FROM sqlite_scan('{self.db_path}', 'benefit_checklist')
                    GROUP BY section, plan_no
                )
                SELECT
                    s.title AS มาตรา,
                    s.target_group AS กลุ่มเป้าหมาย,
                    s.contribution_text AS เงินสมทบ,
                    CAST(c.covered_cases AS VARCHAR) || ' กรณี' AS จำนวนสิทธิที่คุ้มครอง,
                    printf('%.2f%%', c.coverage_percent) AS ความคุ้มครอง,
                    s.old_age_text AS ชราภาพ
                FROM sqlite_scan('{self.db_path}', 'section_summary') s
                LEFT JOIN coverage c
                    ON s.section = c.section
                AND (
                        (s.plan_no IS NULL AND c.plan_no IS NULL)
                        OR s.plan_no = c.plan_no
                )
                ORDER BY s.id
            """).df()

            con.close()
            return df

    def get_recommendations_from_db(
            self,
            section,
            plan_no=None
        ):
            conn = self._connect_db()
            cur = conn.cursor()

            if plan_no is None:
                cur.execute("""
                    SELECT recommendation, message_type
                    FROM recommendations
                    WHERE recommendation_type = 'section'
                        AND section = ?
                        AND plan_no IS NULL
                """, (section,))
            else:
                cur.execute("""
                    SELECT recommendation, message_type
                    FROM recommendations
                    WHERE recommendation_type = 'section'
                        AND section = ?
                        AND plan_no = ?
                """, (section, int(plan_no)))

            rows = cur.fetchall()
            conn.close()

            return rows
    
    def get_recommendation_by_profile(self, user_status, priority=None):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT recommendation, message_type
                FROM recommendations
                WHERE recommendation_type = 'profile'
                    AND user_status = ?
                    AND (priority = ? OR priority IS NULL)
                ORDER BY
                    CASE WHEN priority = ? THEN 0 ELSE 1 END,
                    id
                LIMIT 1
            """, (user_status, priority, priority))

            row = cur.fetchone()
            conn.close()

            return row
    
    def get_user_status_options(self):
            conn = self._connect_db()
            cur = conn.cursor()

            cur.execute("""
                SELECT DISTINCT user_status
                FROM recommendations
                WHERE recommendation_type = 'profile'
                AND user_status IS NOT NULL
                ORDER BY id
            """)

            rows = [r[0] for r in cur.fetchall()]
            conn.close()

            return rows

    def get_priority_options(self, user_status=None):
            conn = self._connect_db()
            cur = conn.cursor()

            if user_status:
                cur.execute("""
                    SELECT DISTINCT priority
                    FROM recommendations
                    WHERE recommendation_type = 'profile'
                    AND priority IS NOT NULL
                    AND user_status = ?
                    ORDER BY id
                """, (user_status,))
            else:
                cur.execute("""
                    SELECT DISTINCT priority
                    FROM recommendations
                    WHERE recommendation_type = 'profile'
                    AND priority IS NOT NULL
                    ORDER BY id
                """)

            rows = [r[0] for r in cur.fetchall()]
            conn.close()

            return rows

    def get_section_highlights(
            self,
            section,
            plan_no=None
        ):
            conn = self._connect_db()
            cur = conn.cursor()

            if plan_no is None:
                cur.execute("""
                    SELECT detail
                    FROM section_highlights
                    WHERE section = ?
                    AND plan_no IS NULL
                """, (section,))
            else:
                cur.execute("""
                    SELECT detail
                    FROM section_highlights
                    WHERE section = ?
                    AND plan_no = ?
                """, (section, int(plan_no)))

            rows = [r[0] for r in cur.fetchall()]

            conn.close()

            return rows
