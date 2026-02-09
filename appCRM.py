import json
import os
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from fpdf import FPDF
from fpdf.errors import FPDFException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_TITLE = "Portfolio CRM"
APP_SUBTITLE = "Portfolio company updates, reporting & investor exports"
DATA_DIR = "data"
UPDATES_PATH = os.path.join(DATA_DIR, "company_updates.json")
COMPANIES_PATH = os.path.join(DATA_DIR, "companies.json")
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

# ---------------------------------------------------------------------------
# Custom CSS for professional styling
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* ---- Global ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ---- Header area ---- */
header[data-testid="stHeader"] {
    background: transparent;
}

/* ---- Main container ---- */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}
[data-testid="stSidebar"] hr {
    border-color: #334155;
}

/* ---- Metric cards ---- */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #f8fafc;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 0.6rem 1.25rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: #64748b;
    background: transparent;
    border: none;
    transition: all 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #334155;
    background: #e2e8f0;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ---- Forms & inputs ---- */
.stForm {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stNumberInput > label {
    font-weight: 500 !important;
    color: #334155 !important;
    font-size: 0.875rem !important;
    margin-bottom: 0.25rem !important;
}

.stTextInput input,
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}

/* ---- Buttons ---- */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.01em;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px);
}

.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    border: 1px solid #e2e8f0 !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
}

/* ---- Expanders ---- */
.streamlit-expanderHeader {
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    color: #1e293b !important;
    background: #f8fafc;
    border-radius: 8px;
}

/* ---- Dataframes ---- */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}

/* ---- Alert boxes ---- */
.stAlert {
    border-radius: 10px !important;
}

/* ---- Subheader styling ---- */
h2 {
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 1.35rem !important;
    padding-bottom: 0.25rem;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 1rem !important;
}
h3 {
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
}

/* ---- Divider ---- */
hr {
    border-color: #e2e8f0;
    margin: 1.5rem 0;
}

/* ---- Status badges ---- */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.status-overdue {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
}
.status-upcoming {
    background: #fffbeb;
    color: #d97706;
    border: 1px solid #fde68a;
}
.status-on-track {
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
}

/* ---- Section cards ---- */
.section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ---- Empty state ---- */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #94a3b8;
}
.empty-state h3 {
    color: #64748b !important;
    margin-bottom: 0.5rem;
}
</style>
"""

# ---------------------------------------------------------------------------
# PDF generation helpers
# ---------------------------------------------------------------------------


def _normalize_pdf_text(value: str | None) -> str:
    text = str(value) if value is not None else "-"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ").replace("\u00a0", " ")
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)
    return text or "-"


def _safe_pdf_slug(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw).strip("_") or "company"


class UpdatePDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(15, 23, 42)
        self.cell(0, 10, "Portfolio Company Update", align="C")
        self.ln(6)
        self.set_draw_color(226, 232, 240)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(8)

    def add_section(self, title: str, value: str):
        safe_title = _normalize_pdf_text(title)
        safe_value = _normalize_pdf_text(value)
        usable_width = max(self.w - self.l_margin - self.r_margin, 10)

        self.set_x(self.l_margin)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(30, 41, 59)
        self.multi_cell(usable_width, 7, safe_title)

        self.set_x(self.l_margin)
        self.set_font("helvetica", "", 10)
        self.set_text_color(71, 85, 105)
        self.multi_cell(usable_width, 6, safe_value, wrapmode="CHAR")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}  |  Generated {datetime.now().strftime('%Y-%m-%d')}", align="C")


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------


def ensure_storage() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    if not os.path.exists(COMPANIES_PATH):
        with open(COMPANIES_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
    if not os.path.exists(UPDATES_PATH):
        with open(UPDATES_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def _json_safe(value):
    if value is None:
        return ""
    if isinstance(value, pd.Timestamp):
        return value.isoformat() if not pd.isna(value) else ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if pd.isna(value):
        return ""
    return value


def _read_json_list(path: str) -> list[dict]:
    ensure_storage()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _write_json_list(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


@st.cache_data
def load_companies() -> pd.DataFrame:
    rows = _read_json_list(COMPANIES_PATH)
    normalized = [{col: row.get(col, "") for col in COMPANY_COLUMNS} for row in rows]
    df = pd.DataFrame(normalized, columns=COMPANY_COLUMNS)
    if "next_due_date" in df.columns:
        df["next_due_date"] = pd.to_datetime(df["next_due_date"], errors="coerce")
    if "is_active" in df.columns:
        df["is_active"] = df["is_active"].fillna(True)
    return df


@st.cache_data
def load_updates() -> pd.DataFrame:
    rows = _read_json_list(UPDATES_PATH)
    normalized = [{col: row.get(col, "") for col in UPDATE_COLUMNS} for row in rows]
    df = pd.DataFrame(normalized, columns=UPDATE_COLUMNS)
    if "submission_date" in df.columns:
        df["submission_date"] = pd.to_datetime(df["submission_date"], errors="coerce")
    return df


def save_companies(df: pd.DataFrame) -> None:
    payload = [{col: _json_safe(row.get(col, "")) for col in COMPANY_COLUMNS} for row in df.to_dict(orient="records")]
    _write_json_list(COMPANIES_PATH, payload)
    st.cache_data.clear()


def save_updates(df: pd.DataFrame) -> None:
    payload = [{col: _json_safe(row.get(col, "")) for col in UPDATE_COLUMNS} for row in df.to_dict(orient="records")]
    _write_json_list(UPDATES_PATH, payload)
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Business logic helpers
# ---------------------------------------------------------------------------


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
    company_slug = _safe_pdf_slug(str(update_data.get("company_name", "company")))
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
        try:
            pdf.add_section(title, str(value))
        except FPDFException:
            pdf.add_section(title, _normalize_pdf_text(value).encode("ascii", "replace").decode("ascii"))

    pdf.output(output_path)
    return output_path


def reminder_text(company_name: str, cadence: str, due_date: str) -> str:
    return (
        f"Hi {company_name} team,\n\n"
        f"Friendly reminder that your {cadence.lower()} update is due on {due_date}.\n\n"
        "Please submit your structured company update including:\n"
        "  - Financial metrics (revenue, expenses, cash, runway)\n"
        "  - Wins and challenges\n"
        "  - Asks from investors / portfolio managers\n"
        "  - Meeting agenda and minutes\n\n"
        "Thanks for helping keep investor reporting consistent and on schedule."
    )


def _due_status(due_date, today) -> str:
    if due_date is None:
        return "unknown"
    diff = (due_date - today).days
    if diff < 0:
        return "overdue"
    elif diff <= 7:
        return "upcoming"
    return "on-track"


def _status_html(status: str) -> str:
    labels = {"overdue": "Overdue", "upcoming": "Due Soon", "on-track": "On Track", "unknown": "No Date"}
    return f'<span class="status-badge status-{status}">{labels.get(status, status)}</span>'


# ---------------------------------------------------------------------------
# Page config & global styles
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="briefcase",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

ensure_storage()
companies_df = load_companies()
updates_df = load_updates()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Portfolio CRM")
    st.caption("Manage portfolio companies, collect structured updates, and generate investor-ready reports.")
    st.divider()

    # Quick stats in sidebar
    total_companies = len(companies_df)
    total_updates = len(updates_df)
    overdue_count = (
        int((companies_df["next_due_date"].dt.date <= date.today()).sum())
        if not companies_df.empty and "next_due_date" in companies_df.columns
        else 0
    )

    st.markdown(f"**Companies:** {total_companies}")
    st.markdown(f"**Updates:** {total_updates}")
    if overdue_count > 0:
        st.markdown(f"**Overdue:** :red[{overdue_count}]")
    else:
        st.markdown("**Overdue:** 0")

    st.divider()
    st.caption("Built with Streamlit. Data stored locally as JSON.")

# ---------------------------------------------------------------------------
# Top metrics bar
# ---------------------------------------------------------------------------

st.markdown(f"## {APP_TITLE}")
st.caption(APP_SUBTITLE)

pdf_count = len([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Portfolio Companies", total_companies)
m2.metric("Total Updates", total_updates)
m3.metric("Updates Overdue", overdue_count, delta=f"-{overdue_count}" if overdue_count else None, delta_color="inverse")
m4.metric("PDFs Exported", pdf_count)

st.markdown("")  # spacer

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

onboard_tab, submit_tab, sequences_tab, dashboard_tab = st.tabs(
    ["Onboard Companies", "Submit Update", "Reminders", "Dashboard"]
)

# ---- TAB 1: Onboard Companies ----
with onboard_tab:
    st.subheader("Onboard a New Company")
    st.markdown("Register portfolio companies to begin collecting structured updates and generating reports.")

    with st.form("onboard_company", clear_on_submit=True):
        st.markdown("### Company Details")
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.text_input("Company Name", placeholder="e.g. Acme Inc.")
            contact_name = st.text_input("Founder / Primary Contact", placeholder="e.g. Jane Smith")
            contact_email = st.text_input("Contact Email", placeholder="e.g. jane@acme.com")
        with c2:
            portfolio_manager = st.text_input("Portfolio Manager", placeholder="e.g. John Doe")
            fund = st.text_input("Investment Fund", placeholder="e.g. Fund III")
            cadence = st.selectbox(
                "Reporting Cadence",
                ["Weekly", "Biweekly", "Monthly", "Quarterly"],
                index=2,
                help="How often this company should submit updates.",
            )

        st.markdown("")
        onboard = st.form_submit_button("Onboard Company", type="primary", use_container_width=True)

    if onboard:
        if not company_name.strip() or not contact_name.strip() or not contact_email.strip():
            st.error("Company name, contact name, and contact email are required.")
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
            st.success(f"**{company_name.strip()}** has been onboarded successfully.")
            st.info(f"Access token: `{token}` — Share this securely with the company contact.")
            st.rerun()

    # Companies table
    if not companies_df.empty:
        st.markdown("")
        st.subheader("Portfolio Companies")

        display_df = companies_df.copy()
        if "next_due_date" in display_df.columns:
            display_df["next_due_date"] = display_df["next_due_date"].dt.strftime("%Y-%m-%d")
        display_df["is_active"] = display_df["is_active"].map({True: "Active", False: "Inactive"})

        st.dataframe(
            display_df[
                [
                    "company_name",
                    "contact_name",
                    "contact_email",
                    "portfolio_manager",
                    "fund",
                    "reporting_cadence",
                    "next_due_date",
                    "is_active",
                ]
            ].rename(
                columns={
                    "company_name": "Company",
                    "contact_name": "Contact",
                    "contact_email": "Email",
                    "portfolio_manager": "PM",
                    "fund": "Fund",
                    "reporting_cadence": "Cadence",
                    "next_due_date": "Next Due",
                    "is_active": "Status",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown(
            '<div class="empty-state"><h3>No companies onboarded yet</h3>'
            "<p>Use the form above to register your first portfolio company.</p></div>",
            unsafe_allow_html=True,
        )

# ---- TAB 2: Submit Company Update ----
with submit_tab:
    st.subheader("Submit a Company Update")

    if companies_df.empty:
        st.info("Onboard at least one company in the **Onboard Companies** tab before submitting updates.")
    else:
        company_lookup = {r["company_name"]: r for _, r in companies_df.iterrows()}

        st.markdown("### General Information")
        g1, g2, g3 = st.columns(3)
        with g1:
            selected_company = st.selectbox("Company", sorted(company_lookup.keys()))
        with g2:
            reporting_period = st.text_input("Reporting Period", placeholder="e.g. January 2026")
        with g3:
            submitted_by = st.text_input("Submitted By", placeholder="e.g. Jane Smith")

        st.markdown("---")
        st.markdown("### Financial Metrics")
        f1, f2, f3, f4 = st.columns(4)
        revenue = f1.text_input("Revenue", placeholder="e.g. $150,000")
        expenses = f2.text_input("Expenses", placeholder="e.g. $120,000")
        cash = f3.text_input("Cash on Hand", placeholder="e.g. $500,000")
        runway_months = f4.number_input("Runway (months)", min_value=0, max_value=60, value=6)

        st.markdown("---")
        st.markdown("### Progress & Challenges")
        p1, p2 = st.columns(2)
        with p1:
            wins = st.text_area("Wins & Highlights", placeholder="Key achievements this period...", height=120)
            asks = st.text_area(
                "Asks from Investors",
                placeholder="Introductions, advice, or resources needed...",
                height=120,
            )
        with p2:
            challenges = st.text_area(
                "Challenges & Risks", placeholder="Current obstacles or concerns...", height=120
            )
            investment_update = st.text_area(
                "Investment Update",
                placeholder="Fundraise status, cap table changes...",
                height=120,
            )

        st.markdown("---")
        st.markdown("### Narrative & Meetings")
        narrative = st.text_area(
            "Investor-Ready Narrative",
            placeholder="A concise summary suitable for LP reporting...",
            height=140,
        )
        n1, n2 = st.columns(2)
        with n1:
            meeting_agenda = st.text_area("Meeting Agenda", placeholder="Topics for the next board meeting...", height=120)
        with n2:
            meeting_minutes = st.text_area("Meeting Minutes", placeholder="Notes from the last meeting...", height=120)

        data_warehouse_link = st.text_input("Data Warehouse Link", placeholder="https://...")

        st.markdown("")
        submit_update = st.button("Save Update & Generate PDF", type="primary", use_container_width=True)

        if submit_update:
            if not reporting_period.strip() or not submitted_by.strip():
                st.error("**Reporting period** and **Submitted by** are required fields.")
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

                # Update next due date
                companies_mut = companies_df.copy()
                idx = companies_mut.index[companies_mut["company_name"] == selected_company][0]
                comp_cadence = companies_mut.loc[idx, "reporting_cadence"]
                companies_mut.loc[idx, "next_due_date"] = str(next_due_from_today(comp_cadence))
                save_companies(companies_mut)

                st.success(f"Update for **{selected_company}** saved successfully. PDF generated.")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF Report",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True,
                    )
                st.rerun()

# ---- TAB 3: Reminder Sequences ----
with sequences_tab:
    st.subheader("Reminder Sequences")
    st.markdown("Review upcoming deadlines and draft reminder emails for portfolio companies.")

    if companies_df.empty:
        st.info("No companies onboarded yet. Head to the **Onboard Companies** tab to get started.")
    else:
        today = date.today()
        due_sorted = companies_df.sort_values("next_due_date")

        # Summary cards
        overdue_list = []
        upcoming_list = []
        on_track_list = []

        for _, row in due_sorted.iterrows():
            due_date = row["next_due_date"].date() if pd.notna(row["next_due_date"]) else None
            status = _due_status(due_date, today)
            if status == "overdue":
                overdue_list.append(row)
            elif status == "upcoming":
                upcoming_list.append(row)
            else:
                on_track_list.append(row)

        s1, s2, s3 = st.columns(3)
        s1.markdown(f"**:red[Overdue]** — {len(overdue_list)} companies")
        s2.markdown(f"**:orange[Due Soon]** — {len(upcoming_list)} companies")
        s3.markdown(f"**:green[On Track]** — {len(on_track_list)} companies")

        st.markdown("---")

        # Show all companies with status
        for _, row in due_sorted.iterrows():
            due_date = row["next_due_date"].date() if pd.notna(row["next_due_date"]) else today
            status = _due_status(due_date, today)
            status_label = _status_html(status)

            with st.expander(f"{row['company_name']}  —  Due: {due_date}  ({status.replace('-', ' ').title()})"):
                info_col, action_col = st.columns([2, 1])
                with info_col:
                    st.markdown(f"**Contact:** {row['contact_name']} ({row['contact_email']})")
                    st.markdown(f"**Portfolio Manager:** {row['portfolio_manager']}")
                    st.markdown(f"**Cadence:** {row['reporting_cadence']}  |  **Fund:** {row['fund']}")
                with action_col:
                    st.markdown(status_label, unsafe_allow_html=True)

                st.markdown("**Draft Reminder Email:**")
                msg = reminder_text(row["company_name"], row["reporting_cadence"], str(due_date))
                st.code(msg, language=None)

# ---- TAB 4: Dashboard & PDF Exports ----
with dashboard_tab:
    st.subheader("Investment Dashboard")

    if updates_df.empty:
        st.info("No updates have been submitted yet. Use the **Submit Update** tab to add your first report.")
    else:
        # Search and filter controls
        filter_col1, filter_col2 = st.columns([3, 1])
        with filter_col1:
            search = st.text_input(
                "Search updates",
                placeholder="Search by company, narrative, wins, or challenges...",
                label_visibility="collapsed",
            )
        with filter_col2:
            if not companies_df.empty:
                company_filter = st.selectbox(
                    "Filter by company",
                    ["All Companies"] + sorted(companies_df["company_name"].unique().tolist()),
                    label_visibility="collapsed",
                )
            else:
                company_filter = "All Companies"

        filtered = updates_df.copy()

        # Apply company filter
        if company_filter != "All Companies":
            filtered = filtered[filtered["company_name"] == company_filter]

        # Apply text search
        if search.strip():
            query = search.lower().strip()
            mask = (
                filtered["company_name"].fillna("").str.lower().str.contains(query, regex=False)
                | filtered["narrative"].fillna("").str.lower().str.contains(query, regex=False)
                | filtered["wins"].fillna("").str.lower().str.contains(query, regex=False)
                | filtered["challenges"].fillna("").str.lower().str.contains(query, regex=False)
            )
            filtered = filtered[mask]

        filtered = filtered.sort_values("submission_date", ascending=False)

        st.markdown(f"Showing **{len(filtered)}** of **{len(updates_df)}** updates")
        st.markdown("")

        # Display table
        display_updates = filtered.copy()
        display_updates["submission_date"] = display_updates["submission_date"].dt.strftime("%Y-%m-%d")

        st.dataframe(
            display_updates[
                [
                    "submission_date",
                    "company_name",
                    "reporting_period",
                    "revenue",
                    "expenses",
                    "cash",
                    "runway_months",
                    "submitted_by",
                ]
            ].rename(
                columns={
                    "submission_date": "Date",
                    "company_name": "Company",
                    "reporting_period": "Period",
                    "revenue": "Revenue",
                    "expenses": "Expenses",
                    "cash": "Cash",
                    "runway_months": "Runway (mo)",
                    "submitted_by": "Submitted By",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        # Detail view for each update
        if not filtered.empty:
            st.markdown("---")
            st.markdown("### Update Details")

            for _, row in filtered.iterrows():
                sub_date = row["submission_date"].strftime("%Y-%m-%d") if pd.notna(row["submission_date"]) else "N/A"
                with st.expander(f"{row['company_name']} — {row['reporting_period']} ({sub_date})"):
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Revenue:** {row['revenue'] or 'N/A'}")
                        st.markdown(f"**Expenses:** {row['expenses'] or 'N/A'}")
                        st.markdown(f"**Cash:** {row['cash'] or 'N/A'}")
                        st.markdown(f"**Runway:** {row['runway_months']} months")
                    with d2:
                        st.markdown(f"**Submitted By:** {row['submitted_by']}")
                        st.markdown(f"**Date:** {sub_date}")
                        if row.get("data_warehouse_link"):
                            st.markdown(f"**Data Link:** {row['data_warehouse_link']}")

                    if row.get("wins"):
                        st.markdown(f"**Wins:** {row['wins']}")
                    if row.get("challenges"):
                        st.markdown(f"**Challenges:** {row['challenges']}")
                    if row.get("asks"):
                        st.markdown(f"**Asks:** {row['asks']}")
                    if row.get("narrative"):
                        st.markdown(f"**Narrative:** {row['narrative']}")

                    # PDF download if available
                    if row.get("pdf_path") and os.path.exists(row["pdf_path"]):
                        with open(row["pdf_path"], "rb") as f:
                            st.download_button(
                                "Download PDF",
                                data=f,
                                file_name=os.path.basename(row["pdf_path"]),
                                mime="application/pdf",
                                key=f"pdf_{row['update_id']}",
                            )

        # Export section
        st.markdown("---")
        st.markdown("### Export Data")
        e1, e2 = st.columns(2)
        with e1:
            st.download_button(
                "Download All Updates (JSON)",
                data=json.dumps(_read_json_list(UPDATES_PATH), indent=2).encode("utf-8"),
                file_name="portfolio_updates.json",
                mime="application/json",
                use_container_width=True,
            )
        with e2:
            csv_data = updates_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download All Updates (CSV)",
                data=csv_data,
                file_name="portfolio_updates.csv",
                mime="text/csv",
                use_container_width=True,
            )
