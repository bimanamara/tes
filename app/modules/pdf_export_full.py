
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
def _title(c, t, y):
    c.setFont("Helvetica-Bold", 16); c.drawString(2*cm, y, t); return y-14
def section_img(c, title, path, y):
    y = _title(c, title, y)
    try:
        img = ImageReader(str(path)); iw, ih = img.getSize()
        maxw, maxh = 17*cm, 12*cm; s = min(maxw/iw, maxh/ih); w, h = iw*s, ih*s
        c.drawImage(img, 2*cm, y-h-0.5*cm, w, h); y -= (h+0.8*cm)
    except Exception as e:
        c.setFont("Helvetica", 10); c.drawString(2*cm, y, f"(image error: {e})"); y -= 12
    return y
def build_full_report(pdf_path, title, images_map: dict, notes: str=""):
    c = canvas.Canvas(str(pdf_path), pagesize=A4); w,h = A4
    c.setFont("Helvetica-Bold", 20); c.drawString(2*cm, h-3*cm, title)
    c.setFont("Helvetica", 11); c.drawString(2*cm, h-4*cm, notes[:1000]); c.showPage()
    for sec, img in images_map.items():
        y = h-2*cm; y = section_img(c, sec, img, y); c.showPage()
    c.save()
