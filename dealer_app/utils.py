from django.utils import timezone
from django.conf import settings

def handle_datetime(dt):
    if dt is None:
        return None
    if settings.USE_TZ:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return timezone.localtime(dt)
    return dt



import qrcode
import base64
from io import BytesIO
import tempfile
import os
import imgkit
from PIL import Image, ImageWin
import win32print
import win32ui

def generate_qr_base64(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def send_qr_to_printer_using_html(html_string, printer_name):
    try:
        import tempfile
        import os
        import pdfkit
        from pdf2image import convert_from_path
        from PIL import ImageWin, Image
        import win32print
        import win32ui

        print("🛠️ Start generating QR print...")

        # Step 1: Save HTML to temp .html file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as html_file:
            html_file.write(html_string)
            html_path = html_file.name

        # Step 2: Define PDF and image output path
        pdf_path = html_path.replace('.html', '.pdf')
        print(f"📄 PDF will be saved to: {pdf_path}")

        # Step 3: Convert HTML to PDF using pdfkit
        pdfkit.from_file(html_path, pdf_path, options={
            'enable-local-file-access': '',
            'page-size': 'A6',
            'margin-top': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'margin-right': '0in',
        })

        # Step 4: Convert PDF to Image (first page only)
        images = convert_from_path(pdf_path, dpi=300)
        image = images[0]  # Only one QR per call

        # Step 5: Send to printer
        hprinter = win32print.OpenPrinter(printer_name)
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Parcel QR Label")
        hdc.StartPage()

        dib = ImageWin.Dib(image)
        dib.draw(hdc.GetHandleOutput(), (0, 0, image.width, image.height))

        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
        win32print.ClosePrinter(hprinter)

        print("✅ QR printed successfully!")

        # Clean up
        os.remove(html_path)
        os.remove(pdf_path)

        return True

    except Exception as e:
        print(f"❌ Print failed: {e}")
        return False
