#!/usr/bin/env python3
# integrity.py
# Manual batch integrity check with line-range prompts
# This script verifies the integrity of GitHub usernames listed in config/usernames.txt for the bot’s operation.
# It checks that each username exists on GitHub.
# Any missing usernames are logged, and the file is updated accordingly.

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from github import Github, GithubException

def main():
    load_dotenv()
    token = os.getenv("PAT_TOKEN")
    if not token:
        sys.exit("Error: PAT_TOKEN environment variable is required")
    gh = Github(token)

    base_dir      = Path(__file__).parent.parent
    username_path = base_dir / "config" / "usernames.txt"
    log_dir       = base_dir / "logs" / "integrity"
    log_dir.mkdir(parents=True, exist_ok=True)

    if not username_path.exists():
        sys.exit(f"Error: usernames file not found at {username_path}")

    # Read all usernames ahead of prompting so we can show the valid range
    lines = [l.strip() for l in username_path.read_text().splitlines() if l.strip()]
    total = len(lines)
    if total == 0:
        sys.exit("Error: usernames.txt is empty")

    # Prompt user for batch range, showing valid bounds
    try:
        start = int(input(f"Enter START line number (1–{total}): ").strip())
        end   = int(input(f"Enter   END   line number ({start}–{total}): ").strip())
    except ValueError:
        sys.exit("Invalid input. Please enter integer values for start and end.")

    if not (1 <= start <= end <= total):
        sys.exit(f"Range out of bounds: file has {total} lines, but you requested {start}-{end}.")

    batch = lines[start-1:end]

    # Check existence
    results = []    # (line_no, username, status)
    missing = []
    for idx, name in enumerate(batch, start=start):
        try:
            gh.get_user(name)
            status = "OK"
        except GithubException as e:
            if e.status == 404:
                status = "MISSING"
                missing.append(name)
            else:
                status = f"ERROR({e.status})"
        results.append((idx, name, status))

    # Write run log
    ts       = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    run_file = log_dir / f"run-{ts}-{start}-{end}.txt"
    with run_file.open("w") as f:
        f.write(f"Run timestamp: {ts} (UTC)\n")
        f.write(f"Lines processed: {start} to {end} (of {total})\n\n")
        for idx, name, status in results:
            f.write(f"{idx}: {name} – {status}\n")
        last_idx, last_name, _ = results[-1]
        f.write(f"\nLast processed: {last_idx}: {last_name}\n")
    print(f"[INFO] Run log → {run_file}")

    # If any missing, log and remove them
    if missing:
        miss_file = log_dir / f"missing-{ts}-{start}-{end}.txt"
        with miss_file.open("w") as f:
            f.write("\n".join(missing) + "\n")
        print(f"[INFO] Logged {len(missing)} missing → {miss_file}")

        remaining = [u for u in lines if u not in missing]
        username_path.write_text("\n".join(remaining) + "\n")
        print(f"[INFO] Removed {len(missing)} missing entries; {len(remaining)} remain.")
    else:
        print("[INFO] No missing usernames in this batch.")

if __name__ == "__main__":
    main()
