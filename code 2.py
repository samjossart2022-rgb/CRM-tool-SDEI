
# Portfolio Company Update Collection Tool with Streamlit Frontend and CSV Backend

import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

DATA_FILE = "company_updates.csv"
PDF_FOLDER = "pdf_outputs"
os.makedirs(PDF_FOLDER, exist_ok=True)

class UpdatePDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "Portfolio Company Update", new_x=0, new_y=0, align="C")
        self.ln(10)

    def add_update(self, update_data):
        self.set_font("helvetica", "", 12)
        for key, value in update_data.items():
            self.multi_cell(0, 10, f"{key}:\n{value}\n", align="L")
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", new_x=2, new_y=2, align="C")

def generate_pdf(update_data, filename):
    pdf = UpdatePDF()
    pdf.add_page()
    pdf.add_update(update_data)
    filepath = os.path.join(PDF_FOLDER, filename)
    pdf.output(filepath)
    return filepath

def save_to_csv(update_data):
    df = pd.DataFrame([update_data])
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(DATA_FILE, index=False)

# Streamlit UI
st.title("📄 Portfolio Company Update Form")

with st.form("update_form"):
    company = st.text_input("Company Name")
    period = st.text_input("Reporting Period (e.g., Q1 2026)")
    revenue = st.text_input("Revenue")
    burn = st.text_input("Burn Rate")
    runway = st.text_input("Runway")
    highlights = st.text_area("Highlights")
    challenges = st.text_area("Challenges")
    team = st.text_area("Team Updates")
    asks = st.text_area("Asks")
    goals = st.text_area("Upcoming Goals")

    submitted = st.form_submit_button("Submit Update")

if submitted:
    update = {
        "Company Name": company,
        "Reporting Period": period,
        "Revenue": revenue,
        "Burn Rate": burn,
        "Runway": runway,
        "Highlights": highlights,
        "Challenges": challenges,
        "Team Updates": team,
        "Asks": asks,
        "Upcoming Goals": goals
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"update_{company.replace(' ', '_')}_{timestamp}.pdf"
    pdf_path = generate_pdf(update, filename)
    save_to_csv(update)

    st.success(f"Update saved and PDF generated: {filename}")
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name=filename)
