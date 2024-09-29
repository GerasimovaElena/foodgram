import os
from io import BytesIO

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def generate_pdf(summary):
    output = BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'free_serif.ttf')
    pdfmetrics.registerFont(TTFont('FreeSerif', font_path))

    p.setFont("FreeSerif", 16)
    p.drawString(100, height - 50, "Список покупок:")

    p.setFont("FreeSerif", 12)
    y_position = height - 100

    for item in summary:
        name = item['ingredient_name']
        unit = item['measurement_unit']
        amount = item['amount']
        text = f'{name} ({unit}) — {amount}'

        p.drawString(100, y_position, f"• {text}")
        y_position -= 20

        if y_position < 50:
            p.showPage()
            p.setFont("FreeSerif", 12)
            y_position = height - 50

    p.showPage()
    p.save()
    output.seek(0)

    return output.getvalue()
