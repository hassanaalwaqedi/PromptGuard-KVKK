"""Compatibility entry point for a root-level Render start command."""

from pathlib import Path
from runpy import run_path

_backend_main = Path(__file__).resolve().parents[1] / "backend" / "app" / "main.py"
app = run_path(str(_backend_main), run_name="promptguard_backend.main")["app"]
