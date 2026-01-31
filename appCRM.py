
import os
from datetime import date
import pandas as pd
import streamlit as st

APP_TITLE = "SDEI Portfolio Updates CRM"
DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "updates.csv")

COLUMNS = [
    "date",
    "company",
    "update_type",
    "headline",
    "details",
    "round_stage",
    "amount",
    "investors",
    "source_url",
    "tags",
]


def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_PATH, index=False)


@st.cache_data
def load_updates() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(DATA_PATH)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def append_update(row: dict):
    df = load_updates()
    new_row = pd.DataFrame([row], columns=COLUMNS)
    out = pd.concat([df, new_row], ignore_index=True)
    out.to_csv(DATA_PATH, index=False)
    st.cache_data.clear()


# ---------- UI ----------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

df = load_updates()

with st.expander("➕ Add an update", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        upd_date = st.date_input("Date", value=date.today())
        company = st.text_input("Company *")
        update_type = st.selectbox(
            "Update Type",
            ["Funding", "Product", "Hiring", "Partnership", "Financials", "Regulatory", "Other"],
        )

    with col2:
        headline = st.text_input("Headline *")
        round_stage = st.text_input("Round/Stage (optional)")
        amount = st.text_input("Amount (optional)")

    with col3:
        investors = st.text_input("Investors (optional)")
        source_url = st.text_input("Source URL (optional)")
        tags = st.text_input("Tags (comma-separated, optional)")

    details = st.text_area("Details / Notes *", height=140)

    submitted = st.button("Save update", type="primary")

    if submitted:
        if not company.strip() or not headline.strip() or not details.strip():
            st.error("Please fill out Company, Headline, and Details.")
        else:
            append_update(
                {
                    "date": str(upd_date),
                    "company": company.strip(),
                    "update_type": update_type,
                    "headline": headline.strip(),
                    "details": details.strip(),
                    "round_stage": round_stage.strip(),
                    "amount": amount.strip(),
                    "investors": investors.strip(),
                    "source_url": source_url.strip(),
                    "tags": tags.strip(),
                }
            )
            st.success("Saved. Reloading…")
            st.rerun()

st.divider()

st.subheader("Updates")

left, right = st.columns([2, 1])

with left:
    search = st.text_input("Search (company/headline/details)")
with right:
    type_filter = st.multiselect(
        "Filter by type",
        sorted([t for t in df["update_type"].dropna().unique()]) if "update_type" in df.columns else [],
        [],
    )

filtered = df.copy()

if search.strip():
    q = search.strip().lower()
    for col in ["company", "headline", "details", "investors", "tags"]:
        if col not in filtered.columns:
            filtered[col] = ""
    mask = (
        filtered["company"].fillna("").str.lower().str.contains(q)
        | filtered["headline"].fillna("").str.lower().str.contains(q)
        | filtered["details"].fillna("").str.lower().str.contains(q)
        | filtered["investors"].fillna("").str.lower().str.contains(q)
        | filtered["tags"].fillna("").str.lower().str.contains(q)
    )
    filtered = filtered[mask]

if type_filter and "update_type" in filtered.columns:
    filtered = filtered[filtered["update_type"].isin(type_filter)]

# sort newest first
if "date" in filtered.columns:
    filtered = filtered.sort_values("date", ascending=False)

# show metrics
st.metric("Total Updates", len(df))
st.metric("Showing", len(filtered))

# display
show_cols = ["date", "company", "update_type", "headline", "round_stage", "amount", "investors", "source_url", "tags"]
for c in show_cols:
    if c not in filtered.columns:
        filtered[c] = None

if "date" in filtered.columns:
    filtered = filtered.assign(date=filtered["date"].dt.date.astype("string"))

st.dataframe(filtered[show_cols], use_container_width=True)

st.download_button(
    "Download updates.csv",
    data=pd.read_csv(DATA_PATH).to_csv(index=False).encode("utf-8"),
    file_name="updates.csv",
    mime="text/csv",
)