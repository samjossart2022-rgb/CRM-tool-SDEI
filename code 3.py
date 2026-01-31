
# Streamlit CRM Tool for Portfolio Updates with PDF, CSV, Email, and Report Bundling

import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import smtplib
from email.message import EmailMessage
from PyPDF2 import PdfMerger

DATA_FILE = "company_updates.csv"
PDF_FOLDER = "pdf_outputs"
MERGED_PDF = "Investor_Report_Merged.pdf"
os.makedirs(PDF_FOLDER, exist_ok=True)

INVESTOR_EMAILS = ["investor1@example.com", "investor2@example.com"]
SENDER_EMAIL = "your.email@gmail.com"
SENDER_PASSWORD = "your_app_password"

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

def send_email(subject, body, attachments):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(INVESTOR_EMAILS)
    msg.set_content(body)

    for path in attachments:
        with open(path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

def merge_pdfs():
    merger = PdfMerger()
    pdf_files = sorted([os.path.join(PDF_FOLDER, f) for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")])
    for pdf in pdf_files:
        merger.append(pdf)
    merger.write(MERGED_PDF)
    merger.close()
    return MERGED_PDF

st.title("📄 Portfolio Company Update Form")

menu = st.sidebar.selectbox("Navigation", ["Submit Update", "Admin Dashboard", "Send Reports"])

if menu == "Submit Update":
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

elif menu == "Admin Dashboard":
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        st.subheader("📊 All Company Submissions")
        search = st.text_input("Search Company")
        if search:
            df = df[df["Company Name"].str.contains(search, case=False)]
        st.dataframe(df)
    else:
        st.info("No submissions yet.")

elif menu == "Send Reports":
    st.subheader("📤 Send Merged Report to Investors")
    if st.button("Merge PDFs and Send Email"):
        merged_path = merge_pdfs()
        send_email(
            subject="Quarterly Portfolio Report",
            body="Attached is the combined report for all portfolio companies.",
            attachments=[merged_path]
        )
        st.success("Merged PDF emailed to investors.")
