import base64
import io
import json
import os
import uuid
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from fpdf import FPDF
from fpdf.errors import FPDFException
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_TITLE = "Enterprise Institute"
APP_SUBTITLE = "Portfolio Company Updates, Reporting & Investor Exports"
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_SCRIPT_DIR, "assets", "logo.png")

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
]


# ---------------------------------------------------------------------------
# Logo helpers
# ---------------------------------------------------------------------------


def _get_logo_base64() -> str | None:
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def _watermark_css(logo_b64: str | None) -> str:
    if not logo_b64:
        return ""
    return f"""
/* ---- Watermark ---- */
[data-testid="stMain"]::before {{
    content: "";
    position: fixed;
    top: 50%;
    left: 55%;
    transform: translate(-50%, -50%);
    width: 500px;
    height: 500px;
    background-image: url("data:image/png;base64,{logo_b64}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    opacity: 0.035;
    pointer-events: none;
    z-index: 0;
}}
"""


# ---------------------------------------------------------------------------
# Custom CSS for professional styling
# ---------------------------------------------------------------------------

_logo_b64 = _get_logo_base64()

CUSTOM_CSS = f"""
<style>
/* ---- Global ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

/* ---- Header area ---- */
header[data-testid="stHeader"] {{
    background: transparent;
}}

/* ---- Main container ---- */
.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}}
[data-testid="stSidebar"] * {{
    color: #e2e8f0 !important;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label {{
    color: #94a3b8 !important;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}}
[data-testid="stSidebar"] hr {{
    border-color: #334155;
}}

/* ---- Metric cards ---- */
[data-testid="stMetric"] {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}
[data-testid="stMetric"] label {{
    color: #64748b !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600 !important;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: #0f172a !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: #f8fafc;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e2e8f0;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    padding: 0.6rem 1.25rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: #64748b;
    background: transparent;
    border: none;
    transition: all 0.15s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: #334155;
    background: #e2e8f0;
}}
.stTabs [aria-selected="true"] {{
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
.stTabs [data-baseweb="tab-highlight"] {{
    display: none;
}}
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ---- Forms & inputs ---- */
.stForm {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}

.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stNumberInput > label {{
    font-weight: 500 !important;
    color: #334155 !important;
    font-size: 0.875rem !important;
    margin-bottom: 0.25rem !important;
}}

.stTextInput input,
.stTextArea textarea {{
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}}
.stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}}

/* ---- Buttons ---- */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {{
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.01em;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.3) !important;
}}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {{
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px);
}}

.stDownloadButton > button {{
    border-radius: 8px !important;
    font-weight: 500 !important;
    border: 1px solid #e2e8f0 !important;
    transition: all 0.15s ease !important;
}}
.stDownloadButton > button:hover {{
    border-color: #3b82f6 !important;
    color: #3b82f6 !important;
}}

/* ---- Expanders ---- */
.streamlit-expanderHeader {{
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    color: #1e293b !important;
    background: #f8fafc;
    border-radius: 8px;
}}

/* ---- Dataframes ---- */
[data-testid="stDataFrame"] {{
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}}

/* ---- Alert boxes ---- */
.stAlert {{
    border-radius: 10px !important;
}}

/* ---- Subheader styling ---- */
h2 {{
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 1.35rem !important;
    padding-bottom: 0.25rem;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 1rem !important;
}}
h3 {{
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
}}

/* ---- Divider ---- */
hr {{
    border-color: #e2e8f0;
    margin: 1.5rem 0;
}}

/* ---- Status badges ---- */
.status-badge {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}
.status-overdue {{
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
}}
.status-upcoming {{
    background: #fffbeb;
    color: #d97706;
    border: 1px solid #fde68a;
}}
.status-on-track {{
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
}}

/* ---- Empty state ---- */
.empty-state {{
    text-align: center;
    padding: 3rem 2rem;
    color: #94a3b8;
}}
.empty-state h3 {{
    color: #64748b !important;
    margin-bottom: 0.5rem;
}}

{_watermark_css(_logo_b64)}
</style>
"""

# ---------------------------------------------------------------------------
# PDF generation helpers (in-memory, no file storage needed)
# ---------------------------------------------------------------------------


def _normalize_pdf_text(value: str | None) -> str:
    text = str(value) if value is not None else "-"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ").replace("\u00a0", " ")
    text = "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)
    return text or "-"


def _safe_pdf_slug(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw).strip("_") or "company"


def _format_date(raw) -> str:
    """Turn a datetime/string into a clean 'Month DD, YYYY' date."""
    if raw is None:
        return "N/A"
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%B %d, %Y")
        except ValueError:
            continue
    return text


# Colour palette
_GOLD = (166, 142, 100)
_DARK = (15, 23, 42)
_SLATE = (71, 85, 105)
_LIGHT_GRAY = (241, 245, 249)
_WHITE = (255, 255, 255)
_TABLE_BORDER = (203, 213, 225)


class UpdatePDF(FPDF):
    def header(self):
        # Gold bar across the top
        self.set_fill_color(*_GOLD)
        self.rect(0, 0, self.w, 3, style="F")

        # Logo
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=self.l_margin, y=8, h=14)
            self.set_x(self.l_margin + 28)
        else:
            self.set_xy(self.l_margin, 8)
        self.set_font("helvetica", "B", 16)
        self.set_text_color(*_DARK)
        self.cell(0, 8, "Enterprise Institute", ln=True)
        if os.path.exists(LOGO_PATH):
            self.set_x(self.l_margin + 28)
        self.set_font("helvetica", "", 9)
        self.set_text_color(*_SLATE)
        self.cell(0, 5, "Portfolio Company Update Report", ln=True)
        self.ln(4)
        self.set_draw_color(*_GOLD)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*_GOLD)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("helvetica", "", 7)
        self.set_text_color(*_SLATE)
        self.cell(0, 5, "Enterprise Institute  |  Confidential", align="L")
        self.cell(0, 5, f"Page {self.page_no()}  |  Generated {datetime.now().strftime('%B %d, %Y')}", align="R", ln=True)

    # -- Layout helpers --

    def _section_heading(self, title: str):
        self.ln(2)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(*_DARK)
        self.cell(0, 7, title.upper(), ln=True)
        self.set_draw_color(*_GOLD)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.l_margin + 40, self.get_y())
        self.ln(3)

    def _info_row(self, label: str, value: str):
        w = self.w - self.l_margin - self.r_margin
        self.set_font("helvetica", "B", 9)
        self.set_text_color(*_SLATE)
        self.cell(38, 6, label, ln=False)
        self.set_font("helvetica", "", 10)
        self.set_text_color(*_DARK)
        self.multi_cell(w - 38, 6, _normalize_pdf_text(value), wrapmode="CHAR")

    def _kpi_table(self, rows: list[tuple[str, str]]):
        """Render a 2-column key-value table with alternating row shading."""
        w = self.w - self.l_margin - self.r_margin
        label_w = w * 0.35
        value_w = w * 0.65
        self.set_draw_color(*_TABLE_BORDER)
        self.set_line_width(0.2)
        for i, (label, value) in enumerate(rows):
            if i % 2 == 0:
                self.set_fill_color(*_LIGHT_GRAY)
            else:
                self.set_fill_color(*_WHITE)
            y_before = self.get_y()
            self.set_font("helvetica", "B", 9)
            self.set_text_color(*_SLATE)
            self.cell(label_w, 8, f"  {label}", border="LTB", fill=True)
            self.set_font("helvetica", "", 10)
            self.set_text_color(*_DARK)
            self.cell(value_w, 8, f"  {_normalize_pdf_text(value)}", border="RTB", fill=True, ln=True)

    def _text_block(self, label: str, value: str):
        safe = _normalize_pdf_text(value)
        if not safe or safe == "-":
            return
        w = self.w - self.l_margin - self.r_margin
        self.set_font("helvetica", "B", 9)
        self.set_text_color(*_SLATE)
        self.cell(0, 6, label, ln=True)
        self.set_font("helvetica", "", 10)
        self.set_text_color(*_DARK)
        self.multi_cell(w, 5.5, safe, wrapmode="CHAR")
        self.ln(3)


def generate_pdf_bytes(update_data: dict) -> bytes:
    """Generate a professional PDF report in memory and return raw bytes."""
    pdf = UpdatePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    company = str(update_data.get("company_name", ""))
    period = str(update_data.get("reporting_period", ""))
    sub_date = _format_date(update_data.get("submission_date"))
    sub_by = str(update_data.get("submitted_by", ""))

    # ---- Report title block ----
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(*_DARK)
    pdf.cell(0, 10, _normalize_pdf_text(company), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*_SLATE)
    pdf.cell(0, 6, f"{_normalize_pdf_text(period)}   |   {sub_date}   |   Submitted by {_normalize_pdf_text(sub_by)}", ln=True)
    pdf.ln(4)

    # ---- Financial Summary ----
    pdf._section_heading("Financial Summary")
    kpi_rows = [
        ("Revenue", str(update_data.get("revenue", ""))),
        ("Expenses", str(update_data.get("expenses", ""))),
        ("Cash on Hand", str(update_data.get("cash", ""))),
        ("Runway", f"{update_data.get('runway_months', 'N/A')} months"),
    ]
    try:
        pdf._kpi_table(kpi_rows)
    except FPDFException:
        for label, val in kpi_rows:
            pdf._info_row(label, val)
    pdf.ln(4)

    # ---- Progress & Challenges ----
    progress_fields = [
        ("Wins & Highlights", update_data.get("wins", "")),
        ("Challenges & Risks", update_data.get("challenges", "")),
        ("Asks from Investors", update_data.get("asks", "")),
        ("Investment Update", update_data.get("investment_update", "")),
    ]
    has_progress = any(_normalize_pdf_text(str(v)) not in ("", "-") for _, v in progress_fields)
    if has_progress:
        pdf._section_heading("Progress & Challenges")
        for label, val in progress_fields:
            try:
                pdf._text_block(label, str(val))
            except FPDFException:
                pdf._text_block(label, _normalize_pdf_text(str(val)).encode("ascii", "replace").decode("ascii"))

    # ---- Narrative ----
    narrative = str(update_data.get("narrative", ""))
    if _normalize_pdf_text(narrative) not in ("", "-"):
        pdf._section_heading("Investor Narrative")
        try:
            pdf._text_block("", narrative)
        except FPDFException:
            pdf._text_block("", _normalize_pdf_text(narrative).encode("ascii", "replace").decode("ascii"))

    # ---- Meetings ----
    agenda = str(update_data.get("meeting_agenda", ""))
    minutes = str(update_data.get("meeting_minutes", ""))
    has_meetings = any(_normalize_pdf_text(v) not in ("", "-") for v in (agenda, minutes))
    if has_meetings:
        pdf._section_heading("Meetings")
        try:
            pdf._text_block("Agenda", agenda)
            pdf._text_block("Minutes", minutes)
        except FPDFException:
            pass

    # ---- Data link (only if provided) ----
    link = str(update_data.get("data_warehouse_link", "")).strip()
    if link and link != "-":
        pdf.ln(2)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*_SLATE)
        pdf.cell(38, 6, "Data Link", ln=False)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(59, 130, 246)
        pdf.cell(0, 6, link, ln=True)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Supabase data layer
# ---------------------------------------------------------------------------


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def _supabase_query(fn):
    """Run a Supabase query, surfacing the real error on failure."""
    try:
        return fn()
    except Exception as exc:
        st.error(
            f"**Database error:** {exc}\n\n"
            "Check that:\n"
            "1. You ran the SQL migration in Supabase SQL Editor\n"
            "2. Your `[supabase]` secrets (url and key) are correct\n"
            "3. RLS policies were created (see supabase_setup.sql)"
        )
        st.stop()


def load_companies() -> pd.DataFrame:
    sb = get_supabase()
    response = _supabase_query(
        lambda: sb.table("companies").select("*").order("company_name").execute()
    )
    if not response.data:
        return pd.DataFrame(columns=COMPANY_COLUMNS)
    df = pd.DataFrame(response.data)
    if "next_due_date" in df.columns:
        df["next_due_date"] = pd.to_datetime(df["next_due_date"], errors="coerce")
    if "is_active" in df.columns:
        df["is_active"] = df["is_active"].fillna(True)
    return df


def load_updates() -> pd.DataFrame:
    sb = get_supabase()
    response = _supabase_query(
        lambda: sb.table("company_updates").select("*").order("submission_date", desc=True).execute()
    )
    if not response.data:
        return pd.DataFrame(columns=UPDATE_COLUMNS)
    df = pd.DataFrame(response.data)
    if "submission_date" in df.columns:
        df["submission_date"] = pd.to_datetime(df["submission_date"], errors="coerce")
    return df


def add_company(row: dict) -> None:
    sb = get_supabase()
    sb.table("companies").insert(row).execute()


def add_update(row: dict) -> None:
    sb = get_supabase()
    sb.table("company_updates").insert(row).execute()


def update_company_due_date(company_id: str, next_due: str) -> None:
    sb = get_supabase()
    sb.table("companies").update({"next_due_date": next_due}).eq("company_id", company_id).execute()


def delete_company(company_id: str) -> None:
    """Remove a company and all its updates (cascade via DB foreign key)."""
    sb = get_supabase()
    sb.table("companies").delete().eq("company_id", company_id).execute()


def delete_update(update_id: str) -> None:
    """Remove a single update."""
    sb = get_supabase()
    sb.table("company_updates").delete().eq("update_id", update_id).execute()


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


def reminder_text(company_name: str, cadence: str, due_date: str) -> str:
    return (
        f"Hi {company_name} team,\n\n"
        f"Friendly reminder that your {cadence.lower()} update is due on {due_date}.\n\n"
        "Please submit your structured company update including:\n"
        "  - Financial metrics (revenue, expenses, cash, runway)\n"
        "  - Wins and challenges\n"
        "  - Asks from investors / portfolio managers\n"
        "  - Meeting agenda and minutes\n\n"
        "Thanks for helping keep investor reporting consistent and on schedule.\n\n"
        "— Enterprise Institute"
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


def _avg_runway(updates: pd.DataFrame) -> float:
    valid = pd.to_numeric(updates["runway_months"], errors="coerce").dropna()
    return round(valid.mean(), 1) if not valid.empty else 0


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

companies_df = load_companies()
updates_df = load_updates()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # Logo
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("### Enterprise Institute")
    st.caption("Portfolio company updates, reporting & investor exports.")
    st.divider()

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
    st.markdown(f"**Avg Runway:** {_avg_runway(updates_df)} months")

    # Recent activity
    if not updates_df.empty:
        st.divider()
        st.markdown("**Recent Activity**")
        recent = updates_df.head(3)
        for _, r in recent.iterrows():
            sub_d = r["submission_date"].strftime("%b %d") if pd.notna(r["submission_date"]) else "?"
            st.caption(f"{sub_d} — {r['company_name']}")

    st.divider()
    st.caption(f"Data stored in Supabase. Today is {date.today().strftime('%B %d, %Y')}.")

# ---------------------------------------------------------------------------
# Top metrics bar
# ---------------------------------------------------------------------------

st.markdown(f"## {APP_TITLE}")
st.caption(APP_SUBTITLE)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Portfolio Companies", total_companies)
m2.metric("Total Updates", total_updates)
m3.metric("Updates Overdue", overdue_count, delta=f"-{overdue_count}" if overdue_count else None, delta_color="inverse")
m4.metric("Avg Runway", f"{_avg_runway(updates_df)} mo")

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
            st.toast(f"{company_name.strip()} onboarded successfully!", icon="✅")
            st.rerun()

    # Companies list with delete
    if not companies_df.empty:
        st.markdown("")
        st.subheader(f"Portfolio Companies ({total_companies})")

        for _, comp_row in companies_df.iterrows():
            due_str = comp_row["next_due_date"].strftime("%Y-%m-%d") if pd.notna(comp_row["next_due_date"]) else "N/A"
            active_label = "Active" if comp_row["is_active"] else "Inactive"
            cid = comp_row["company_id"]

            with st.expander(f"{comp_row['company_name']}  —  {comp_row['reporting_cadence']}  |  Next due: {due_str}"):
                ic1, ic2 = st.columns(2)
                with ic1:
                    st.markdown(f"**Contact:** {comp_row['contact_name']} ({comp_row['contact_email']})")
                    st.markdown(f"**Portfolio Manager:** {comp_row['portfolio_manager']}")
                with ic2:
                    st.markdown(f"**Fund:** {comp_row['fund']}")
                    st.markdown(f"**Status:** {active_label}  |  **Token:** `{comp_row['access_token']}`")

                confirm_key = f"confirm_del_company_{cid}"
                if st.session_state.get(confirm_key):
                    st.warning(f"Are you sure you want to delete **{comp_row['company_name']}** and all its updates?")
                    yes_col, no_col, _ = st.columns([1, 1, 4])
                    if yes_col.button("Yes, delete", key=f"yes_del_{cid}", type="primary"):
                        delete_company(cid)
                        st.session_state.pop(confirm_key, None)
                        st.toast(f"{comp_row['company_name']} deleted.", icon="🗑️")
                        st.rerun()
                    if no_col.button("Cancel", key=f"no_del_{cid}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                else:
                    if st.button("Delete company", key=f"del_{cid}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
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
        runway_months = f4.number_input("Runway (months)", min_value=0, max_value=120, value=6)

        if runway_months <= 3:
            st.warning("Runway is critically low (3 months or less).")
        elif runway_months <= 6:
            st.info("Runway is below 6 months. Consider flagging for discussion.")

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
                }
                add_update(payload)

                comp_cadence = company_lookup[selected_company]["reporting_cadence"]
                update_company_due_date(
                    company_lookup[selected_company]["company_id"],
                    str(next_due_from_today(comp_cadence)),
                )

                st.toast(f"Update for {selected_company} saved!", icon="✅")

                pdf_bytes = generate_pdf_bytes(payload)
                slug = _safe_pdf_slug(selected_company)
                st.download_button(
                    "Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"update_{slug}_{date.today().isoformat()}.pdf",
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
        s1.metric("Overdue", len(overdue_list))
        s2.metric("Due Soon", len(upcoming_list))
        s3.metric("On Track", len(on_track_list))

        st.markdown("---")

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
        # ---- Analytics section ----
        st.markdown("### Portfolio Analytics")

        # Update frequency chart
        chart_df = updates_df.copy()
        chart_df["month"] = chart_df["submission_date"].dt.to_period("M").astype(str)
        monthly_counts = chart_df.groupby("month").size().reset_index(name="Updates")

        if len(monthly_counts) >= 2:
            freq_chart = (
                alt.Chart(monthly_counts)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#3b82f6")
                .encode(
                    x=alt.X("month:N", title="Month", sort=None),
                    y=alt.Y("Updates:Q", title="Updates Submitted"),
                    tooltip=["month", "Updates"],
                )
                .properties(height=220)
            )
            st.altair_chart(freq_chart, use_container_width=True)

        # Runway distribution
        runway_vals = pd.to_numeric(updates_df["runway_months"], errors="coerce").dropna()
        if not runway_vals.empty:
            r1, r2, r3 = st.columns(3)
            r1.metric("Avg Runway", f"{runway_vals.mean():.1f} mo")
            r2.metric("Min Runway", f"{runway_vals.min():.0f} mo")
            r3.metric("Max Runway", f"{runway_vals.max():.0f} mo")

        st.markdown("---")

        # ---- Search and filter controls ----
        st.markdown("### Update History")
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

        if company_filter != "All Companies":
            filtered = filtered[filtered["company_name"] == company_filter]

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
                uid = row["update_id"]
                sub_date = row["submission_date"].strftime("%Y-%m-%d") if pd.notna(row["submission_date"]) else "N/A"
                with st.expander(f"{row['company_name']} — {row['reporting_period']} ({sub_date})"):
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Revenue:** {row['revenue'] or 'N/A'}")
                        st.markdown(f"**Expenses:** {row['expenses'] or 'N/A'}")
                        st.markdown(f"**Cash:** {row['cash'] or 'N/A'}")
                        runway_val = int(row['runway_months']) if row['runway_months'] else 0
                        if runway_val <= 3:
                            st.markdown(f"**Runway:** :red[{runway_val} months]")
                        elif runway_val <= 6:
                            st.markdown(f"**Runway:** :orange[{runway_val} months]")
                        else:
                            st.markdown(f"**Runway:** :green[{runway_val} months]")
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

                    # Actions row: PDF download + delete
                    act1, act2, _ = st.columns([1, 1, 2])
                    with act1:
                        pdf_data = row.to_dict()
                        pdf_bytes = generate_pdf_bytes(pdf_data)
                        slug = _safe_pdf_slug(str(row.get("company_name", "company")))
                        st.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name=f"update_{slug}_{sub_date}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{uid}",
                            use_container_width=True,
                        )
                    with act2:
                        confirm_key = f"confirm_del_update_{uid}"
                        if st.session_state.get(confirm_key):
                            st.warning("Delete this update?")
                            y_col, n_col = st.columns(2)
                            if y_col.button("Yes", key=f"yes_del_u_{uid}", type="primary"):
                                delete_update(uid)
                                st.session_state.pop(confirm_key, None)
                                st.toast("Update deleted.", icon="🗑️")
                                st.rerun()
                            if n_col.button("No", key=f"no_del_u_{uid}"):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                        else:
                            if st.button("Delete update", key=f"del_u_{uid}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()

        # Export section
        st.markdown("---")
        st.markdown("### Export Data")
        e1, e2 = st.columns(2)
        with e1:
            json_export = updates_df.to_dict(orient="records")
            st.download_button(
                "Download All Updates (JSON)",
                data=json.dumps(json_export, indent=2, default=str).encode("utf-8"),
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
