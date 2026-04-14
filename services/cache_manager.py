import json
import os
import tempfile
import time
from pathlib import Path


def read_cache(filepath: Path) -> dict | list | None:
    """Read JSON cache file. Returns None if missing or corrupt."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_cache(filepath: Path, data: dict | list) -> None:
    """Write JSON cache file atomically."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=filepath.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def is_cache_fresh(filepath: Path, max_age_hours: float) -> bool:
    """Check if cache file exists and is within max_age_hours."""
    try:
        mtime = filepath.stat().st_mtime
        return (time.time() - mtime) < max_age_hours * 3600
    except (FileNotFoundError, OSError):
        return False
