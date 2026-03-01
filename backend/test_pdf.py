import os
import smtplib
from backend.services.pdf_generator import generate_diagnostic_pdf
print("PDF generator imported successfully")
pdf_bytes = generate_diagnostic_pdf(
    report_text="Testing a report \u2014 with an em dash and \u2013 en dash to make sure it doesn't crash.",
    patient_name="Test Patient",
    session_id=123
)
print("PDF generated successfully with em-dashes.")
