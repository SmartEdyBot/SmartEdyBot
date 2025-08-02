from fpdf import FPDF

def generate_pdf(text, filename="document.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(190, 10, txt=text)
    pdf.output(filename)
