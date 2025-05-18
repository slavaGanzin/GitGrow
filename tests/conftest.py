# tests/conftest.py  (new file)

import shutil
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR   = PROJECT_ROOT / "config"

@pytest.fixture
def patch_config(tmp_path):
    """
    Replace usernames.txt & whitelist.txt with small test-specific versions,
    then restore the originals after the test.
    """
    # paths
    user_file  = CONFIG_DIR / "usernames.txt"
    white_file = CONFIG_DIR / "whitelist.txt"
    bak_user   = user_file.with_suffix(".bak")
    bak_white  = white_file.with_suffix(".bak")

    # --- backup originals -------------------------------------------------
    user_file.rename(bak_user)
    white_file.rename(bak_white)

    # --- write tiny dummy data --------------------------------------------
    user_file.write_text("bob\ncarol\nalice\n")
    white_file.write_text("carol\n")

    try:
        yield  #  ⇢  run the test
    finally:
        # --- restore originals --------------------------------------------
        user_file.unlink(missing_ok=True)
        white_file.unlink(missing_ok=True)
        bak_user.rename(user_file)
        bak_white.rename(white_file)
