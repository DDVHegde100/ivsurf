"""
OpenPulse Vercel compatibility shim.

Vercel routes API traffic to api/index.py (FastAPI).
This file remains for legacy build configs that reference app.py.
"""

from api.main import app
