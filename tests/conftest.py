# tests/conftest.py
# tests/conftest.py
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR   = PROJECT_ROOT / "config"

@pytest.fixture(scope="function")
def patch_config():
    """
    Swap in a tiny, test-specific usernames.txt & whitelist.txt,
    then restore the real ones afterward.
    """
    user_file  = CONFIG_DIR / "usernames.txt"
    white_file = CONFIG_DIR / "whitelist.txt"
    bak_user   = user_file.with_suffix(".bak")
    bak_white  = white_file.with_suffix(".bak")

    # back up real files
    user_file.rename(bak_user)
    white_file.rename(bak_white)

    try:
        # test data: two to follow, one nonexistent to skip, two whitelisted
        user_file.write_text(
            "irene\n"
            "guadalupe\n"
            "dne\n"
            "sotiris\n"
            "zakaria\n"
        )
        white_file.write_text(
            "sotiris\n"
            "zakaria\n"
        )
        yield
    finally:
        # restore originals
        user_file.unlink(missing_ok=True)
        white_file.unlink(missing_ok=True)
        bak_user.rename(user_file)
        bak_white.rename(white_file)
