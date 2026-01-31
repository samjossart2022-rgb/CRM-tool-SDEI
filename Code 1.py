
# Portfolio Company Update Collection Tool (Backend-Only)
# Note: You will need to integrate this with a web frontend (e.g., Streamlit, Flask form, etc.) and storage (e.g., SQLite, Google Drive, or Sheets)

from fpdf import FPDF
from datetime import datetime  # Optional — remove if unused
# import os                    # Unused — can remove
# import json                  # Unused — can remove

class UpdatePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Portfolio Company Update", ln=True, align="C")
        self.ln(10)

    def add_update(self, update_data):
        self.set_font("Arial", "", 12)
        for key, value in update_data.items():
            self.multi_cell(0, 10, f"{key}:\n{value}\n", align="L")
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_pdf(update_data, output_path="company_update.pdf"):
    pdf = UpdatePDF()
    pdf.add_page()
    pdf.add_update(update_data)
    pdf.output(output_path)
    print(f"✅ PDF generated: {output_path}")

# Example submission (simulate form input)
def example_submission():
    return {
        "Company Name": "TechNova Inc.",
        "Reporting Period": "Q1 2026",
        "Revenue": "$120,000",
        "Burn Rate": "$35,000",
        "Runway": "6 months",
        "Highlights": "Signed 3 new enterprise clients. Released V2 of product.",
        "Challenges": "Delays in hiring senior backend engineer.",
        "Team Updates": "Onboarded new VP of Marketing.",
        "Asks": "Intro to fintech VCs. Help hiring mobile devs.",
        "Upcoming Goals": "Reach $200K MRR by Q3. Expand to EU market."
    }

# Run example
if __name__ == "__main__":
    data = example_submission()
    filename = f"update_{data['Company Name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    generate_pdf(data, filename)