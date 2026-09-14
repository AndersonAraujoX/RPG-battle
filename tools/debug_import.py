import sys
import os
import inspect

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from src.ui.desenho import desenhar_menu_principal
    print(f"Function: {desenhar_menu_principal}")
    print(f"Signature: {inspect.signature(desenhar_menu_principal)}")
    print(f"File: {inspect.getfile(desenhar_menu_principal)}")
except Exception as e:
    print(f"Error: {e}")
