import os
import sys
import tempfile
from pathlib import Path

_MEDIA_TEMP_DIRECTORY = tempfile.TemporaryDirectory(prefix="golt-test-media-")
os.environ.setdefault("MEDIA_FOLDER", _MEDIA_TEMP_DIRECTORY.name)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.auth.service import auth_service


def auth_headers(user_id: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {auth_service._issue_session(user_id)}'}
