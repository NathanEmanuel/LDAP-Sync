import sys
from pathlib import Path

# Allow running this file directly from the repository root without requiring
# editable installation first.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sync.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
