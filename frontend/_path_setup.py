"""
AURA – Path Setup
Add the frontend directory to sys.path so that `from utils...` and
`from components...` imports work regardless of where Streamlit is launched from.
Import this module at the top of app.py and all pages BEFORE any local imports.
"""
import sys
import os

# Add the frontend/ directory to sys.path so local packages resolve correctly.
_frontend_dir = os.path.dirname(os.path.abspath(__file__))
if _frontend_dir not in sys.path:
    sys.path.insert(0, _frontend_dir)
