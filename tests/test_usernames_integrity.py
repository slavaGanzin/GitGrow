# tests/test_usernames_integrity.py
from pathlib import Path

def test_usernames_file_integrity():
    """
    Test the integrity of the usernames file.
    - Check if the file is not empty and has sufficient entries.
    - Ensure there are no exact-case duplicate entries.
    - Verify all entries follow simple GitHub login patterns.
    """
    path = Path(__file__).parent.parent / "config" / "usernames.txt"  # Path to the usernames file
    raw = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]  # Read and strip lines from the file

    # 1. file isn’t empty and still big enough
    assert len(raw) > 5000, "usernames.txt suddenly shrank!"  # Check if the file has more than 5000 entries

    # 2. no exact-case duplicates
    assert len(raw) == len(set(raw)), "Duplicate entries detected"  # Check for exact-case duplicate entries

    # 3. all entries are simple GitHub login patterns
    bad = [u for u in raw if not u.isascii() or " " in u or "/" in u]  # Check for invalid GitHub login patterns
    assert not bad, f"Malformatted usernames: {bad[:5]}"  # Ensure no invalid entries are found
