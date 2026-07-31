# PartnerHub Python backend

This directory contains a FastAPI-based Python port of the existing Node/Express backend.
It is intentionally scaffolded to mirror the current API shape so it can be evolved incrementally.

## Quick start

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - CMD: `.venv\Scripts\activate.bat`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Run the API:
   `uvicorn app.main:app --reload --port 8000`
