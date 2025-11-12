
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

def build_story(pdf_path, title, kpis: dict, paragraphs: list, logo_path=None):
    c = canvas.Canvas(str(pdf_path), pagesize=A4); w,h = A4
    # Cover
    if logo_path:
        try:
            img = ImageReader(str(logo_path)); iw, ih = img.getSize()
            s = min((5*cm)/iw, (5*cm)/ih); c.drawImage(img, w-6*cm, h-5*cm, iw*s, ih*s)
        except Exception:
            pass
    c.setFont("Helvetica-Bold", 22); c.drawString(2*cm, h-3*cm, title)
    y = h-4.2*cm
    c.setFont("Helvetica", 12)
    for k,v in kpis.items():
        c.drawString(2*cm, y, f"{k}: {v}"); y -= 14
    c.showPage()

    # Narrative
    c.setFont("Helvetica", 12)
    for para in paragraphs:
        y = h-2*cm
        for line in wrap_text(para, 90):
            if y < 2*cm: c.showPage(); y = h-2*cm
            c.drawString(2*cm, y, line); y -= 14
        c.showPage()
    c.save()

def wrap_text(text, width):
    words = text.split()
    line = []
    ln = 0
    for w in words:
        if ln + len(w) + 1 > width:
            yield " ".join(line); line=[w]; ln=len(w)
        else:
            line.append(w); ln += len(w)+1
    if line: yield " ".join(line)
