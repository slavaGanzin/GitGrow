#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from github import Github, GithubException

# Load variables from .env if present
load_dotenv()

def main():
    # Authenticate with GitHub API
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("Error: GITHUB_TOKEN environment variable is required for cleaner.py")
    gh = Github(token)

    base_dir = Path(__file__).parent
    username_path = base_dir / "usernames.txt"
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    offline_log = log_dir / "offline_usernames.log"

    if not username_path.exists():
        sys.exit(f"Error: usernames file not found at {username_path}")

    # Read and dedupe usernames (case-insensitive)
    lines = [line.strip() for line in username_path.read_text().splitlines() if line.strip()]
    seen = set()
    usernames = []
    for name in lines:
        lower = name.lower()
        if lower not in seen:
            seen.add(lower)
            usernames.append(name)
    print(f"[INFO] {len(usernames)} unique usernames loaded for existence check.")

    # Check existence via GitHub API
    missing = []
    for name in usernames:
        try:
            gh.get_user(name)
        except GithubException as e:
            if e.status == 404:
                missing.append(name)
            else:
                print(f"[ERROR] checking {name}: {e.data or str(e)}")

    print(f"[INFO] Existence check complete: {len(usernames)} checked, {len(missing)} missing.")

    # Log missing entries to offline_usernames.log and remove them from usernames.txt
    if missing:
        timestamp = datetime.utcnow().isoformat()
        with offline_log.open("a") as lf:
            for name in missing:
                lf.write(f"{timestamp} {name}\n")
        # Filter out missing and rewrite usernames.txt
        remaining = [u for u in usernames if u not in missing]
        try:
            username_path.write_text("\n".join(remaining) + "\n")
            print(f"[INFO] Removed {len(missing)} missing usernames, {len(remaining)} remain.")
        except Exception as e:
            print(f"[ERROR] writing cleaned usernames: {e}")
    else:
        print("[INFO] No missing usernames to remove.")

if __name__ == "__main__":
    main()
