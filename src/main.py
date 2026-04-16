import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running this file directly from the repository root without requiring
# editable installation first.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli import Cli, Env


def get_env() -> Env:

    def get_required_env(key: str) -> str:
        value = os.getenv(key)
        if value is None or value == "":
            raise SystemExit(f"Missing required environment variable: {key}")
        return value

    load_dotenv()

    return Env(
        CONGRESSUS_API_BASE_URL=get_required_env("CONGRESSUS_API_BASE_URL"),
        CONGRESSUS_API_KEY=get_required_env("CONGRESSUS_API_KEY"),
        CONGRESSUS_API_COMMITTEE_FOLDER_ID=get_required_env("CONGRESSUS_API_COMMITTEE_FOLDER_ID"),
        ADMIN_DN=get_required_env("ADMIN_DN"),
        ADMIN_PW=get_required_env("ADMIN_PW"),
        BASE_OU=get_required_env("BASE_OU"),
        MEMBERS_OU=get_required_env("MEMBERS_OU"),
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return Cli(get_env()).run() or 0


if __name__ == "__main__":
    raise SystemExit(main())
