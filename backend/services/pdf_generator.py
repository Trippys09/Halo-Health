"""
HALO Health - Medical PDF Report Generator

Produces a hospital-grade PDF with:
  - Letterhead with HALO Health branding
  - Patient / session metadata block
  - Embedded scan image (if provided)
  - Full structured report with highlighted findings
  - Colour-coded severity and section headers
  - Signature/disclaimer block
"""
import io
import textwrap
import base64
from datetime import datetime

from fpdf import FPDF

# ?? Colour Palette ????????????????????????????????????????????????????????????
BLUE_DARK  = (0, 70, 127)    # HALO Health primary navy
BLUE_MID   = (0, 120, 212)   # Section headers
BLUE_LIGHT = (215, 235, 255) # Shaded rows
RED        = (196, 43, 28)   # Critical / urgent
ORANGE     = (210, 105, 30)
YELLOW_BG  = (255, 252, 220) # Highlighted finding background
GREEN      = (16, 124, 16)
GREY_TEXT  = (96, 96, 96)
GREY_LINE  = (200, 200, 200)
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)


class MedicalReportPDF(FPDF):
    """Hospital-grade FPDF layout for HALO Health diagnostic reports."""

    # Stored per-instance for header/footer use
    _patient_name: str = "Unknown"
    _session_id: int = 0
    _report_date: str = ""

    def header(self):
        """Full letterhead with institution name, horizontal rule, and date."""
        # Top bar background
        self.set_fill_color(*BLUE_DARK)
        self.rect(0, 0, 216, 20, style="F")

        # Logo / institution
        self.set_y(4)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.cell(0, 8, "HALO Health  .  AI Clinical Reporting System", align="C",
                  new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BLUE_LIGHT)
        self.cell(0, 5, "Preliminary Report -- For Clinical Review Only",
                  align="C", new_x="LMARGIN", new_y="NEXT")

        # Patient info strip
        self.set_fill_color(*BLUE_LIGHT)
        self.rect(0, 22, 216, 10, style="F")
        self.set_y(24)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*BLUE_DARK)
        self.cell(70, 6, f"  Patient: {self._patient_name}")
        self.cell(70, 6, f"Session ID: {self._session_id}", align="C")
        self.cell(0,  6, f"Date: {self._report_date}", align="R",
                  new_x="LMARGIN", new_y="NEXT")

        # Divider
        self.set_draw_color(*BLUE_MID)
        self.set_line_width(0.8)
        self.line(10, 34, 200, 34)
        self.ln(8)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*GREY_LINE)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY_TEXT)
        self.cell(
            0, 5,
            "HALO Health AI Report -- Not a substitute for professional clinical evaluation  |"
            f"Page {self.page_no()}",
            align="C",
        )


# ?? Markdown helpers ??????????????????????????????????????????????????????????

def _clean(line: str) -> str:
    """Strip markdown syntax and common emojis for plain PDF rendering.
    # Baseline cleaning for non-Latin characters (FPDF Helvetica limitation)
    """
    line = line.replace("─", "-").replace("—", "-").replace("–", "-").replace("⭐", "*").replace("👁️", "").replace("🔬", "").replace("🟢", "OK").replace("🟡", "!").replace("🟠", "!!").replace("🔴", "!!!")
    res = (
        line.replace("**", "")
           .replace("##", "")
           .replace("###", "")
           .replace("#", "")
           .replace("`", "")
           .replace("*", "")
           .replace("??", "(HALO)")
           .replace("?", "(HALO)")
           .replace("?", "[LAB]")
           .replace("??", "[!]")
           .replace("?", "[!]")
           .replace("?", "[OK]")
           .replace("?", "[~]")
           .replace("?", "[!]")
           .replace("?", "[!!]")
           .replace("?", "[EMERGENCY]")
           .replace("?", "")
           .replace("????", "[DOCTOR]")
           .replace("?", "[RX]")
           .replace("?", "[HOSPITAL]")
           .strip()
    )
    return _safe(res)


def _safe(text: str) -> str:
    """Encode text to latin-1 safe string ? strips any character outside latin-1 range.
    This is required because fpdf2 built-in fonts (Helvetica) only support latin-1.
    """
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def _severity_colour(line: str):
    """Return (R,G,B) for severity indicator lines."""
    l = line.lower()
    if "severe" in l or "?" in l or "emergency" in l or "urgent" in l or "[!!]" in l:
        return RED
    if "moderate" in l or "?" in l or "[!]" in l:
        return ORANGE
    if "mild" in l or "?" in l or "[~]" in l:
        return (180, 130, 0)
    if "normal" in l or "?" in l or "[ok]" in l:
        return GREEN
    return None


def _is_critical_finding(text: str) -> bool:
    return any(kw in text.lower() for kw in [
        "critical", "concerning", "significant", "urgent", "abnormal",
        "mass", "lesion", "fracture", "opacity", "infiltrate", "consolidation",
        "effusion", "carcinoma", "malignant", "metastasis", "hemorrhage", "bleed",
        "[!]",
    ])


# ?? Main generator ????????????????????????????????????????????????????????????

def generate_diagnostic_pdf(
    report_text: str,
    patient_name: str = "Unknown",
    session_id: int = 0,
    image_data: bytes = None,
    image_mime: str = "image/jpeg",
) -> bytes:
    """
    Render a hospital-grade diagnostic report PDF.

    Args:
        report_text:  Markdown report text from PRISM agent.
        patient_name: Patient's full name for the header.
        session_id:   Session ID for tracking reference.
        image_data:   Raw bytes of the uploaded medical scan (optional).
        image_mime:   MIME type of the image (image/jpeg, image/png, etc.).

    Returns:
        PDF file content as bytes.
    """
    report_date = datetime.now().strftime("%B %d, %Y  %I:%M %p")

    pdf = MedicalReportPDF()
    pdf._patient_name = patient_name[:50]
    pdf._session_id = session_id
    pdf._report_date = report_date
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    pdf.set_text_color(*BLACK)

    # ?? Scan Image ??????????????????????????????????????????????????????????
    if image_data:
        try:
            # Determine extension
            ext_map = {
                "image/jpeg": "jpg", "image/jpg": "jpg",
                "image/png": "png", "image/bmp": "bmp",
                "image/tiff": "tiff",
            }
            ext = ext_map.get(image_mime, "jpg")

            # Write image to temp buffer
            img_buf = io.BytesIO(image_data)

            # Section label
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*BLUE_MID)
            pdf.cell(0, 7, "Medical Scan Image", new_x="LMARGIN", new_y="NEXT")

            # Thin border box
            img_x = 30
            img_w = 150
            img_y = pdf.get_y()
            pdf.set_draw_color(*BLUE_MID)
            pdf.set_line_width(0.5)
            pdf.image(img_buf, x=img_x, y=img_y, w=img_w)
            # Re-position after image (estimate height)
            pdf.set_y(img_y + (img_w * 0.75) + 4)

            # Caption
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*GREY_TEXT)
            pdf.cell(0, 5, "Figure 1 -- Submitted medical scan for analysis",
                     align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        except Exception as e:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*RED)
            pdf.cell(0, 6, f"[Image could not be embedded: {str(e)[:60]}]",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Separator
        pdf.set_draw_color(*BLUE_MID)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

    # ?? Report Body ?????????????????????????????????????????????????????????
    pdf.set_text_color(*BLACK)
    in_findings_section = False
    in_table = False
    table_col_count = 0

    for raw_line in report_text.split("\n"):
        line = raw_line.rstrip()
        cleaned = _clean(line)

        # Skip triple-backtick code fences
        if line.strip().startswith("```"):
            continue

        # Horizontal rule
        if line.startswith("---") or line.startswith("==="):
            pdf.set_draw_color(*GREY_LINE)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            continue

        # H2 section heading
        if line.startswith("## "):
            in_findings_section = "finding" in line.lower() or "key finding" in line.lower()
            pdf.ln(3)
            # Blue banner
            pdf.set_fill_color(*BLUE_MID)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*WHITE)
            pdf.rect(10, pdf.get_y(), 190, 8, style="F")
            pdf.set_x(12)
            pdf.cell(186, 8, cleaned.lstrip("# "), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*BLACK)
            pdf.ln(2)
            continue

        # H3 subsection
        if line.startswith("### "):
            in_findings_section = "finding" in line.lower() or "key finding" in line.lower()
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*BLUE_DARK)
            pdf.cell(0, 7, cleaned.lstrip("# "), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*BLUE_MID)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.set_text_color(*BLACK)
            pdf.ln(2)
            continue

        # H4 or bold heading
        if line.startswith("#### ") or (line.startswith("**") and line.endswith("**") and len(line) < 80):
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*BLUE_DARK)
            pdf.cell(0, 6, cleaned, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*BLACK)
            continue

        # Table row
        if "|" in line and line.strip().startswith("|"):
            # Skip separator rows (|---|---|)
            if all(c in "| -" for c in line.replace("---", "")):
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if not cells:
                continue

            table_col_count = len(cells)
            col_w = min(55, 186 // max(table_col_count, 1))
            is_header_row = any(kw in line.lower() for kw in [
                "diagnosis", "nutrient", "medication", "rank", "plan", "meal"
            ]) and raw_line.count("|") > 2 and in_table is False

            if is_header_row:
                in_table = True
                pdf.set_fill_color(*BLUE_DARK)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*WHITE)
                for cell in cells[:5]:
                    pdf.cell(col_w, 7, cell[:30], border=1, fill=True)
                pdf.ln()
            else:
                # Alternating row colours
                alt = (pdf.get_y() / 6) % 2 < 1
                if alt:
                    pdf.set_fill_color(*BLUE_LIGHT)
                else:
                    pdf.set_fill_color(*WHITE)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*BLACK)
                for i, cell in enumerate(cells[:5]):
                    # Red for critical column values
                    if i == 2 and any(kw in cell.lower() for kw in ["high", "severe", "urgent"]):
                        pdf.set_text_color(*RED)
                    else:
                        pdf.set_text_color(*BLACK)
                    pdf.cell(col_w, 7, cell[:35], border=1, fill=True)
                pdf.ln()
            continue
        else:
            in_table = False

        # Bold key-value: **Key:** Value
        if line.startswith("**") and ":**" in line:
            parts = line.split(":**", 1)
            key = _clean(parts[0])
            val = _clean(parts[1]) if len(parts) > 1 else ""
            severity_col = _severity_colour(val)

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*BLUE_DARK)
            pdf.cell(55, 7, f"{key}:", border=0)
            pdf.set_font("Helvetica", "", 10)
            if severity_col:
                pdf.set_text_color(*severity_col)
            else:
                pdf.set_text_color(*BLACK)
            pdf.cell(0, 7, val[:100], border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*BLACK)
            continue

        # Severity line (standalone: ? / ? etc.)
        sev_col = _severity_colour(line)
        if sev_col and len(line.strip()) < 120:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*sev_col)
            pdf.cell(0, 7, cleaned, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*BLACK)
            continue

        # Bullet points
        if line.strip().startswith(("- ", "- ", "* ")):
            text = _clean(line.strip()[2:])
            pdf.set_font("Helvetica", "", 10)

            # Highlight critical findings with yellow background
            if in_findings_section and _is_critical_finding(text):
                pdf.set_fill_color(*YELLOW_BG)
                pdf.set_draw_color(*ORANGE)
                pdf.set_line_width(0.3)
                pdf.set_x(12)
                # Highlight rectangle
                y_start = pdf.get_y()
                lines_needed = max(1, len(textwrap.wrap(text, width=85)))
                pdf.rect(12, y_start, 186, lines_needed * 6 + 2, style="FD")
                pdf.set_x(18)
                pdf.set_text_color(*RED)
                pdf.cell(5, 6, "[!]")
                pdf.set_text_color(*BLACK)
                for i, part in enumerate(textwrap.wrap(text, width=85)):
                    if i == 0:
                        pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.set_x(23)
                        pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_x(14)
                pdf.set_text_color(30, 90, 160)
                pdf.cell(5, 6, "-")
                pdf.set_text_color(*BLACK)
                for i, part in enumerate(textwrap.wrap(text, width=90)):
                    if i == 0:
                        pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.set_x(19)
                        pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
            continue

        # Numbered list
        if len(line) > 2 and line[0].isdigit() and line[1] in ".)" and line[2] == " ":
            num = line[0]
            text = _clean(line[3:])
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(14)
            pdf.set_text_color(*BLUE_DARK)
            pdf.cell(6, 6, f"{num}.")
            pdf.set_text_color(*BLACK)
            for i, part in enumerate(textwrap.wrap(text, width=90)):
                if i == 0:
                    pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.set_x(20)
                    pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
            continue

        # Italic disclaimer line
        if line.strip().startswith("*") and line.strip().endswith("*"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*GREY_TEXT)
            for part in textwrap.wrap(cleaned, width=95):
                pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*BLACK)
            continue

        # Regular paragraph text
        if cleaned:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*BLACK)
            for part in textwrap.wrap(cleaned, width=95):
                pdf.cell(0, 6, part, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.ln(2)

    # ?? Signature Block ??????????????????????????????????????????????????????
    pdf.ln(8)
    pdf.set_draw_color(*BLUE_DARK)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_fill_color(*BLUE_LIGHT)
    pdf.rect(10, pdf.get_y(), 190, 14, style="F")
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*BLUE_DARK)
    pdf.cell(
        0, 5,
        "?  PRISM -- AI Diagnostic Analysis Engine  |  HALO Health Platform",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY_TEXT)
    pdf.cell(
        0, 5,
        "This report is AI-generated and requires clinical correlation. "
        "It is not a legally binding medical diagnosis or prescription.",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )

    return bytes(pdf.output())
