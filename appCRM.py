import os
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from fpdf import FPDF

APP_TITLE = "Visible.PC-style Portfolio CRM"
DATA_DIR = "data"
UPDATES_PATH = os.path.join(DATA_DIR, "company_updates.csv")
COMPANIES_PATH = os.path.join(DATA_DIR, "companies.csv")
PDF_DIR = os.path.join(DATA_DIR, "pdf_exports")

COMPANY_COLUMNS = [
    "company_id",
    "company_name",
    "contact_name",
    "contact_email",
    "portfolio_manager",
    "fund",
    "reporting_cadence",
    "next_due_date",
    "access_token",
    "is_active",
]

UPDATE_COLUMNS = [
    "update_id",
    "submission_date",
    "company_id",
    "company_name",
    "reporting_period",
    "revenue",
    "expenses",
    "cash",
    "runway_months",
    "wins",
    "challenges",
    "asks",
    "investment_update",
    "narrative",
    "meeting_agenda",
    "meeting_minutes",
    "data_warehouse_link",
    "submitted_by",
    "pdf_path",
]


class UpdatePDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(0, 8, "Portfolio Company Update", align="C")
        self.ln(12)

    def add_section(self, title: str, value: str):
        self.set_font("helvetica", "B", 11)
        self.multi_cell(0, 7, title)
        self.set_font("helvetica", "", 10)
        self.multi_cell(0, 6, value if value else "-")
        self.ln(1)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def ensure_storage() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)

    if not os.path.exists(COMPANIES_PATH):
        pd.DataFrame(columns=COMPANY_COLUMNS).to_csv(COMPANIES_PATH, index=False)

    if not os.path.exists(UPDATES_PATH):
        pd.DataFrame(columns=UPDATE_COLUMNS).to_csv(UPDATES_PATH, index=False)


@st.cache_data
def load_companies() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(COMPANIES_PATH)
    if "next_due_date" in df.columns:
        df["next_due_date"] = pd.to_datetime(df["next_due_date"], errors="coerce")
    return df


@st.cache_data
def load_updates() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(UPDATES_PATH)
    if "submission_date" in df.columns:
        df["submission_date"] = pd.to_datetime(df["submission_date"], errors="coerce")
    return df


def save_companies(df: pd.DataFrame) -> None:
    df.to_csv(COMPANIES_PATH, index=False)
    st.cache_data.clear()


def save_updates(df: pd.DataFrame) -> None:
    df.to_csv(UPDATES_PATH, index=False)
    st.cache_data.clear()


def cadence_to_delta(cadence: str) -> timedelta:
    return {
        "Weekly": timedelta(days=7),
        "Biweekly": timedelta(days=14),
        "Monthly": timedelta(days=30),
        "Quarterly": timedelta(days=90),
    }.get(cadence, timedelta(days=30))


def next_due_from_today(cadence: str) -> date:
    return date.today() + cadence_to_delta(cadence)


def add_company(row: dict) -> None:
    companies = load_companies()
    out = pd.concat([companies, pd.DataFrame([row], columns=COMPANY_COLUMNS)], ignore_index=True)
    save_companies(out)


def add_update(row: dict) -> None:
    updates = load_updates()
    out = pd.concat([updates, pd.DataFrame([row], columns=UPDATE_COLUMNS)], ignore_index=True)
    save_updates(out)


def generate_pdf(update_data: dict) -> str:
    company_slug = update_data["company_name"].replace(" ", "_")
    filename = f"update_{company_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(PDF_DIR, filename)

    pdf = UpdatePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    order = [
        ("Company", update_data["company_name"]),
        ("Reporting Period", update_data["reporting_period"]),
        ("Submitted", update_data["submission_date"]),
        ("Submitted By", update_data["submitted_by"]),
        ("Revenue", update_data["revenue"]),
        ("Expenses", update_data["expenses"]),
        ("Cash", update_data["cash"]),
        ("Runway (months)", update_data["runway_months"]),
        ("Wins", update_data["wins"]),
        ("Challenges", update_data["challenges"]),
        ("Asks", update_data["asks"]),
        ("Investment Update", update_data["investment_update"]),
        ("Narrative", update_data["narrative"]),
        ("Meeting Agenda", update_data["meeting_agenda"]),
        ("Meeting Minutes", update_data["meeting_minutes"]),
        ("Data Warehouse Link", update_data["data_warehouse_link"]),
    ]

    for title, value in order:
        pdf.add_section(title, str(value))

    pdf.output(output_path)
    return output_path


def reminder_text(company_name: str, cadence: str, secure_link: str, due_date: str) -> str:
    return (
        f"Hi {company_name} team,\n\n"
        f"Friendly reminder that your {cadence.lower()} update is due on {due_date}.\n"
        "Please submit your structured company update (financial metrics, wins, challenges, asks, "
        "meeting agenda/minutes) using your secure link below:\n"
        f"{secure_link}\n\n"
        "Thanks for helping keep investor reporting consistent."
    )


st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption(
    "Internal CRM for investment teams to onboard companies, collect secure structured updates, "
    "run reminder sequences, and export investor-ready PDFs."
)

ensure_storage()
companies_df = load_companies()
updates_df = load_updates()

stats = st.columns(4)
stats[0].metric("Portfolio Companies", int(len(companies_df)))
stats[1].metric("Total Updates", int(len(updates_df)))
open_requests = (
    int((companies_df["next_due_date"].dt.date <= date.today()).sum())
    if not companies_df.empty and "next_due_date" in companies_df.columns
    else 0
)
stats[2].metric("Updates Due", open_requests)
stats[3].metric("PDFs Exported", len([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]))

onboard_tab, submit_tab, sequences_tab, dashboard_tab = st.tabs(
    ["Onboard Companies", "Submit Company Update", "Reminder Sequences", "Dashboard & PDF Exports"]
)

with onboard_tab:
    st.subheader("1) Onboard portfolio companies")
    with st.form("onboard_company"):
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.text_input("Company name *")
            contact_name = st.text_input("Founder / contact name *")
            contact_email = st.text_input("Contact email *")
        with c2:
            portfolio_manager = st.text_input("Portfolio manager")
            fund = st.text_input("Investment fund")
            cadence = st.selectbox("Reporting cadence", ["Weekly", "Biweekly", "Monthly", "Quarterly"], index=2)

        onboard = st.form_submit_button("Create secure submission link", type="primary")

    if onboard:
        if not company_name.strip() or not contact_name.strip() or not contact_email.strip():
            st.error("Please complete company name, contact name, and contact email.")
        else:
            token = uuid.uuid4().hex[:12]
            row = {
                "company_id": uuid.uuid4().hex,
                "company_name": company_name.strip(),
                "contact_name": contact_name.strip(),
                "contact_email": contact_email.strip(),
                "portfolio_manager": portfolio_manager.strip(),
                "fund": fund.strip(),
                "reporting_cadence": cadence,
                "next_due_date": str(next_due_from_today(cadence)),
                "access_token": token,
                "is_active": True,
            }
            add_company(row)
            st.success("Company onboarded with secure link.")
            st.code(f"https://internal-crm.local/submit?company={company_name.strip()}&token={token}")
            st.rerun()

    if not companies_df.empty:
        preview = companies_df.copy()
        if "next_due_date" in preview.columns:
            preview["next_due_date"] = preview["next_due_date"].dt.date.astype("string")
        st.dataframe(
            preview[
                [
                    "company_name",
                    "contact_name",
                    "contact_email",
                    "portfolio_manager",
                    "fund",
                    "reporting_cadence",
                    "next_due_date",
                    "access_token",
                    "is_active",
                ]
            ],
            use_container_width=True,
        )

with submit_tab:
    st.subheader("2) Structured company updates")
    if companies_df.empty:
        st.info("Onboard at least one company before collecting updates.")
    else:
        company_lookup = {r["company_name"]: r for _, r in companies_df.iterrows()}
        selected_company = st.selectbox("Company *", sorted(company_lookup.keys()))
        submitted_by = st.text_input("Submitted by (name)")
        reporting_period = st.text_input("Reporting period (e.g., Jan 2026)")

        f1, f2, f3, f4 = st.columns(4)
        revenue = f1.text_input("Revenue")
        expenses = f2.text_input("Expenses")
        cash = f3.text_input("Cash")
        runway_months = f4.number_input("Runway (months)", min_value=0, max_value=60, value=6)

        wins = st.text_area("Wins")
        challenges = st.text_area("Challenges")
        asks = st.text_area("Asks from investors / portfolio managers")
        investment_update = st.text_area("Investment updates (fundraise, cap table, etc.)")
        narrative = st.text_area("Text update narrative (investor-ready summary)")
        meeting_agenda = st.text_area("Meeting agenda")
        meeting_minutes = st.text_area("Meeting minutes")
        data_warehouse_link = st.text_input("Data warehouse link (optional)")

        submit_update = st.button("Save update + generate PDF", type="primary")

        if submit_update:
            if not reporting_period.strip() or not submitted_by.strip():
                st.error("Reporting period and submitted-by are required.")
            else:
                payload = {
                    "update_id": uuid.uuid4().hex,
                    "submission_date": str(date.today()),
                    "company_id": company_lookup[selected_company]["company_id"],
                    "company_name": selected_company,
                    "reporting_period": reporting_period.strip(),
                    "revenue": revenue.strip(),
                    "expenses": expenses.strip(),
                    "cash": cash.strip(),
                    "runway_months": int(runway_months),
                    "wins": wins.strip(),
                    "challenges": challenges.strip(),
                    "asks": asks.strip(),
                    "investment_update": investment_update.strip(),
                    "narrative": narrative.strip(),
                    "meeting_agenda": meeting_agenda.strip(),
                    "meeting_minutes": meeting_minutes.strip(),
                    "data_warehouse_link": data_warehouse_link.strip(),
                    "submitted_by": submitted_by.strip(),
                    "pdf_path": "",
                }
                pdf_path = generate_pdf(payload)
                payload["pdf_path"] = pdf_path
                add_update(payload)

                # advance next due date after successful submission
                companies_mut = companies_df.copy()
                idx = companies_mut.index[companies_mut["company_name"] == selected_company][0]
                cadence = companies_mut.loc[idx, "reporting_cadence"]
                companies_mut.loc[idx, "next_due_date"] = str(next_due_from_today(cadence))
                save_companies(companies_mut)

                st.success("Company update stored and PDF exported.")
                with open(pdf_path, "rb") as f:
                    st.download_button("Download this PDF", data=f, file_name=os.path.basename(pdf_path), mime="application/pdf")
                st.rerun()

with sequences_tab:
    st.subheader("3) Reminder sequences + onboarding emails")
    if companies_df.empty:
        st.info("No companies onboarded yet.")
    else:
        due_sorted = companies_df.sort_values("next_due_date")
        for _, row in due_sorted.iterrows():
            secure_link = f"https://internal-crm.local/submit?company={row['company_name']}&token={row['access_token']}"
            due_date = row["next_due_date"].date() if pd.notna(row["next_due_date"]) else date.today()
            msg = reminder_text(row["company_name"], row["reporting_cadence"], secure_link, str(due_date))
            with st.expander(f"{row['company_name']} • next due {due_date}"):
                st.write(f"Contact: {row['contact_name']} ({row['contact_email']})")
                st.code(msg)

with dashboard_tab:
    st.subheader("4) Investment dashboard + investor exports")
    if updates_df.empty:
        st.info("No updates submitted yet.")
    else:
        search = st.text_input("Search updates (company, narrative, wins, challenges)")
        filtered = updates_df.copy()
        if search.strip():
            query = search.lower().strip()
            mask = (
                filtered["company_name"].fillna("").str.lower().str.contains(query)
                | filtered["narrative"].fillna("").str.lower().str.contains(query)
                | filtered["wins"].fillna("").str.lower().str.contains(query)
                | filtered["challenges"].fillna("").str.lower().str.contains(query)
            )
            filtered = filtered[mask]

        filtered = filtered.sort_values("submission_date", ascending=False)
        filtered["submission_date"] = filtered["submission_date"].dt.date.astype("string")

        st.dataframe(
            filtered[
                [
                    "submission_date",
                    "company_name",
                    "reporting_period",
                    "revenue",
                    "expenses",
                    "cash",
                    "runway_months",
                    "wins",
                    "challenges",
                    "narrative",
                    "pdf_path",
                ]
            ],
            use_container_width=True,
        )

        st.download_button(
            "Download unified updates CSV",
            data=updates_df.to_csv(index=False).encode("utf-8"),
            file_name="unified_company_updates.csv",
            mime="text/csv",
        )
