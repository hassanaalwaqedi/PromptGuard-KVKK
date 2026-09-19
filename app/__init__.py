"""Render root-directory compatibility package.

The canonical backend package lives in ``backend/app``. Extending this
package path lets a root-level ``uvicorn app.main:app`` command resolve the
same backend modules when an existing Render service has not yet been moved
to the ``backend`` root directory.
"""

from pathlib import Path

_backend_app = Path(__file__).resolve().parents[1] / "backend" / "app"
__path__.append(str(_backend_app))
