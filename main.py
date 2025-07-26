import subprocess
import sys
import importlib

# Install required packages if not already installed
required_packages = {
    "PIL": "Pillow",
    "customtkinter": "customtkinter", 
    "vobject":"vobject",
}

def install_and_import(module_name, package_name):
    try:
        importlib.import_module(module_name)
        print(f"[OK] {module_name} is already installed.")
    except ImportError:
        print(f"[INFO] {module_name} not found. Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"[INFO] {package_name} installed.")

for module, package in required_packages.items():
    install_and_import(module, package)


from dbms import vcard_import
from gui import gui 

# Run database init
subprocess.run([sys.executable, "dbms/dbms.py"])

# Launch GUI 
gui.launch()
