# auto_qr_setup.py

import os
import sys
import subprocess
import platform
import shutil

def install_python_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")

def setup_wkhtmltopdf_on_ubuntu():
    try:
        if shutil.which("wkhtmltopdf"):
            print("✅ wkhtmltopdf already installed")
            return True
        subprocess.check_call(["sudo", "apt-get", "update"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "wkhtmltopdf"])
        print("✅ wkhtmltopdf installed successfully")
        return True
    except Exception as e:
        print(f"❌ Error installing wkhtmltopdf: {e}")
        return False

def check_and_setup_environment():
    print("🛠️ Checking environment...")

    install_python_package("pdfkit")
    install_python_package("qrcode")
    install_python_package("Pillow")
    install_python_package("pdf2image")
    install_python_package("xhtml2pdf")

    if platform.system() == "Windows":
        install_python_package("pywin32")
        wkhtmltopdf_path = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
        if os.path.exists(wkhtmltopdf_path):
            print(f"✅ wkhtmltopdf found at {wkhtmltopdf_path}")
        else:
            print("⚠️ Please install wkhtmltopdf manually on Windows: https://wkhtmltopdf.org/downloads.html")
    elif platform.system() == "Linux":
        setup_wkhtmltopdf_on_ubuntu()
    else:
        print("❌ Unsupported platform for auto-setup")

if __name__ == "__main__":
    check_and_setup_environment()
