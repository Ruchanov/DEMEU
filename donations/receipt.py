from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_donation_receipt(donation):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFillColor(colors.red)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(100, 750, "Demeu - Donation Successful")

    pdf.setFillColor(colors.green)
    pdf.rect(100, 720, 400, 25, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(180, 728, "Donation Successfully Completed")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(100, 690, f"Amount: {donation.donor_amount} KZT")
    pdf.drawString(300, 690, f"Fee: {donation.support_amount} KZT")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 670, f"Donation ID: {donation.id}")
    pdf.drawString(100, 650, f"Date: {donation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    donor_name = f"{donation.donor.first_name} {donation.donor.last_name}" if donation.donor else "Anonymous"
    pdf.drawString(100, 630, f"Donor Name: {donor_name}")

    pdf.drawString(100, 610, "From: Kaspi Gold *XXXX")
    pdf.drawString(100, 590, f"To: {donation.publication.title}")

    pdf.setStrokeColor(colors.gray)
    pdf.line(100, 570, 400, 570)
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(100, 550, "Thank you for your support!")
    pdf.drawString(100, 535, "This receipt is automatically generated.")

    pdf.save()
    buffer.seek(0)
    return buffer
