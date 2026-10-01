from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
import os
from datetime import datetime


# Custom colour palette
NAVY   = HexColor('#0F1740')
GOLD   = HexColor('#C9A84C')
LIGHT  = HexColor('#F5F0E8')
TEAL   = HexColor('#1A6B72')
WHITE  = colors.white
GRAY   = HexColor('#555555')
LGRAY  = HexColor('#888888')


def draw_certificate_background(c, width, height):
    """Draw decorative background on the canvas."""
    # Gradient-like border strip
    c.setFillColor(NAVY)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Inner parchment area
    margin = 18
    c.setFillColor(LIGHT)
    c.roundRect(margin, margin, width - 2*margin, height - 2*margin, 8, fill=1, stroke=0)

    # Top gold band
    c.setFillColor(GOLD)
    c.rect(margin, height - margin - 60, width - 2*margin, 60, fill=1, stroke=0)

    # Bottom gold band
    c.setFillColor(GOLD)
    c.rect(margin, margin, width - 2*margin, 12, fill=1, stroke=0)

    # Decorative inner border lines
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.roundRect(margin + 12, margin + 20, width - 2*margin - 24, height - 2*margin - 80, 4, fill=0, stroke=1)

    # Corner ornaments
    for x, y in [(margin+14, margin+22), (width-margin-14, margin+22),
                 (margin+14, height-margin-62), (width-margin-14, height-margin-62)]:
        c.setFillColor(GOLD)
        c.circle(x, y, 5, fill=1, stroke=0)


def generate_certificate_pdf(cert_data: dict, qr_path: str, output_dir: str) -> str:
    """Generate a professional A4-landscape certificate PDF."""
    filename = f"cert_{cert_data['certificate_id']}.pdf"
    filepath = os.path.join(output_dir, filename)

    page_width, page_height = landscape(A4)

    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    w, h = page_width, page_height

    draw_certificate_background(c, w, h)

    # ── Institution name in gold banner ──
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(NAVY)
    c.drawCentredString(w / 2, h - 50, cert_data.get('institution_name', 'XYZ University').upper())

    c.setFont("Helvetica", 11)
    c.setFillColor(NAVY)
    accred = cert_data.get('accreditation', 'Accredited Institution')
    c.drawCentredString(w / 2, h - 68, accred)

    # ── Certificate type ──
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(NAVY)
    cert_title = cert_data.get('certificate_type', 'CERTIFICATE OF ACHIEVEMENT').upper()
    c.drawCentredString(w / 2, h - 115, cert_title)

    # ── Decorative gold line ──
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(w*0.25, h - 125, w*0.75, h - 125)

    # ── "This is to certify that" ──
    c.setFont("Helvetica-Oblique", 14)
    c.setFillColor(GRAY)
    c.drawCentredString(w / 2, h - 155, "This is to certify that")

    # ── Student name ──
    c.setFont("Helvetica-Bold", 38)
    c.setFillColor(NAVY)
    c.drawCentredString(w / 2, h - 200, cert_data.get('student_name', '').upper())

    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    name_len = len(cert_data.get('student_name', '')) * 22
    c.line(w/2 - min(name_len/2, 260), h - 208, w/2 + min(name_len/2, 260), h - 208)

    # ── Achievement text ──
    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(GRAY)
    c.drawCentredString(w / 2, h - 235, "has successfully completed")

    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(TEAL)
    c.drawCentredString(w / 2, h - 260, cert_data.get('course', ''))

    c.setFont("Helvetica", 14)
    c.setFillColor(NAVY)
    c.drawCentredString(w / 2, h - 282, cert_data.get('branch', ''))

    if cert_data.get('achievement'):
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(GRAY)
        c.drawCentredString(w / 2, h - 303, f"\u201c{cert_data['achievement']}\u201d")

    # ── Grade / Percentage row ──
    y_info = h - 338
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(NAVY)
    if cert_data.get('grade'):
        c.drawCentredString(w*0.35, y_info, f"Grade: {cert_data['grade']}")
    if cert_data.get('percentage'):
        c.drawCentredString(w*0.5, y_info, f"Percentage: {cert_data['percentage']}%")
    c.drawCentredString(w*0.65, y_info, f"Academic Year: {cert_data.get('academic_year', '')}")

    # ── Divider ──
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(w*0.12, h - 353, w*0.88, h - 353)

    # ── Bottom section: Date | Cert ID | QR | Issuer ──
    bottom_y = h - 360
    left_x = w * 0.13
    right_x = w * 0.72

    # Issue date
    c.setFont("Helvetica", 10)
    c.setFillColor(LGRAY)
    c.drawString(left_x, bottom_y - 10, "Date of Issue")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(NAVY)
    c.drawString(left_x, bottom_y - 26, cert_data.get('issue_date', ''))

    # Certificate ID
    c.setFont("Helvetica", 10)
    c.setFillColor(LGRAY)
    c.drawString(left_x, bottom_y - 55, "Certificate ID")
    c.setFont("Courier-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(left_x, bottom_y - 70, cert_data.get('certificate_id', ''))

    # Issuer signature area
    c.setFont("Helvetica", 10)
    c.setFillColor(LGRAY)
    c.drawString(left_x, bottom_y - 100, "Issued By")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(NAVY)
    c.drawString(left_x, bottom_y - 116, cert_data.get('issuer_name', ''))
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(LGRAY)
    c.drawString(left_x, bottom_y - 130, cert_data.get('institution_name', ''))

    # Signature line
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.7)
    c.line(left_x, bottom_y - 148, left_x + 180, bottom_y - 148)
    c.setFont("Helvetica", 9)
    c.setFillColor(LGRAY)
    c.drawString(left_x + 40, bottom_y - 160, "Authorized Signatory")

    # Hash fingerprint (tiny, at bottom)
    c.setFont("Courier", 7)
    c.setFillColor(LGRAY)
    hash_val = cert_data.get('certificate_hash', '')
    c.drawString(left_x, 32, f"SHA-256: {hash_val[:48]}...")

    # ── QR Code ──
    if qr_path and os.path.exists(qr_path):
        qr_size = 110
        c.drawImage(qr_path, right_x, bottom_y - 130, width=qr_size, height=qr_size,
                    preserveAspectRatio=True)
        c.setFont("Helvetica", 8)
        c.setFillColor(LGRAY)
        c.drawCentredString(right_x + qr_size/2, bottom_y - 144, "Scan to Verify")

    # ── Verification URL ──
    base_url = cert_data.get('base_url', 'http://localhost:5000')
    verify_url = f"{base_url}/verify/{cert_data['certificate_id']}"
    c.setFont("Helvetica", 8)
    c.setFillColor(TEAL)
    c.drawCentredString(w / 2, 22, f"Verify at: {verify_url}")

    c.save()
    return filename
