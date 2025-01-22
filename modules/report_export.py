import csv
from reportlab.pdfgen import canvas
from datetime import datetime

def export_to_txt(data, filename):
    with open(filename, "w") as f:
        for line in data:
            f.write(f"{line}\n")

def export_to_csv(data, filename):
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Nom", "Version actuelle", "Version nouvelle"])
        writer.writerows(data)

def export_to_pdf(data, filename):
    c = canvas.Canvas(filename)
    for i, line in enumerate(data):
        c.drawString(100, 800 - (i * 15), line)
    c.save()

def export_report(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_file = f"rapport_{timestamp}.txt"
    csv_file = f"rapport_{timestamp}.csv"
    pdf_file = f"rapport_{timestamp}.pdf"

    export_to_txt(data, txt_file)
    export_to_csv(data, csv_file)
    export_to_pdf(data, pdf_file)

    return txt_file, csv_file, pdf_file
