import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from afad_earthquake_mcp import app  # noqa: E402

__all__ = ["app"]
