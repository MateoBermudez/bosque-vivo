import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from bosquevivo.api.app import app

__all__ = ["app"]
