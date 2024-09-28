import os
from io import BytesIO

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_pdf(self, summary):
    output = BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'free_serif.ttf')
    pdfmetrics.registerFont(TTFont('FreeSerif', font_path))

    p.setFont("FreeSerif", 16)
    p.drawString(100, height - 50, "Список покупок:")

    p.setFont("FreeSerif", 12)
    y_position = height - 100
    for name, data in summary.items():
        text = f"{name} ({data['measurement_unit']}) — {data['amount']}"
        p.drawString(100, y_position, f"• {text}")
        y_position -= 20

    p.showPage()
    p.save()
    output.seek(0)

    return output.getvalue()
