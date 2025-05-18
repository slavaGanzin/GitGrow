# tests/test_usernames_integrity.py
from pathlib import Path

def test_usernames_file_integrity():
    path = Path(__file__).parent.parent / "config" / "usernames.txt"
    raw = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]

    # 1. file isn’t empty and still big enough
    assert len(raw) > 5000, "usernames.txt suddenly shrank!"

    # 2. no exact-case duplicates
    assert len(raw) == len(set(raw)), "Duplicate entries detected"

    # 3. all entries are simple GitHub login patterns
    bad = [u for u in raw if not u.isascii() or " " in u or "/" in u]
    assert not bad, f"Malformatted usernames: {bad[:5]}"
