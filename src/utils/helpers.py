import re
from pathlib import Path


def ensure_directory(path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    """Strip any folder part and unsafe characters from an uploaded file name."""
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip()
