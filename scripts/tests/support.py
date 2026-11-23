# Shared test helper: scripts act on the repository that contains them, so
# every test copies the scripts (with their shared modules) into the fixture
# repository's scripts/ and runs that copy.

import shutil
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]


def install_scripts(root: Path) -> Path:
    """Copy the scripts and shared modules into root/scripts; return that directory."""
    dest = root / "scripts"
    if dest.resolve() == SCRIPTS_DIR:
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    for src in SCRIPTS_DIR.iterdir():
        if src.is_file() and not src.name.startswith("README"):
            shutil.copy2(src, dest / src.name)
    return dest
