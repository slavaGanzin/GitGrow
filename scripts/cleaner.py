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
    token = os.getenv("GITHUB_TOKEN")  # Retrieve GitHub token from environment variables
    if not token:
        sys.exit("Error: GITHUB_TOKEN environment variable is required for cleaner.py")  # Exit if token is not found
    gh = Github(token)  # Initialize GitHub client

    base_dir = Path(__file__).parent  # Determine base directory of the script
    username_path = base_dir.parent / "config" / "usernames.txt"  # Path to the usernames file in the config directory
    log_dir = base_dir.parent / "logs"  # Path to the logs directory
    log_dir.mkdir(exist_ok=True)  # Create logs directory if it does not exist

    if not username_path.exists():
        sys.exit(f"Error: usernames file not found at {username_path}")  # Exit if usernames file is not found

    # Read and dedupe usernames (case-insensitive)
    lines = [line.strip() for line in username_path.read_text().splitlines() if line.strip()]  # Read usernames from file
    seen = set()  # Set to track seen usernames
    usernames = []  # List to store unique usernames
    for name in lines:
        lower = name.lower()
        if lower not in seen:
            seen.add(lower)
            usernames.append(name)  # Add unique usernames to the list
    print(f"[INFO] {len(usernames)} unique usernames loaded for existence check.")  # Print number of unique usernames

    # Check existence via GitHub API
    missing = []  # List to store missing usernames
    for name in usernames:
        try:
            gh.get_user(name)  # Check if the user exists
        except GithubException as e:
            if e.status == 404:
                missing.append(name)  # Add missing usernames to the list
            else:
                print(f"[ERROR] checking {name}: {e.data or str(e)}")  # Print error message for other exceptions

    print(f"[INFO] Existence check complete: {len(usernames)} checked, {len(missing)} missing.")  # Print summary of existence check

    # Log missing entries to a timestamped file and remove them from usernames.txt
    if missing:
        timestamp = datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")  # Get current timestamp in UTC
        offline_file = log_dir / f"offline_usernames-{timestamp}.txt"  # Path to the offline usernames log file
        try:
            with offline_file.open("w") as lf:
                for name in missing:
                    lf.write(f"{name}\n")  # Write missing usernames to the log file
            print(f"[INFO] Logged {len(missing)} missing usernames to {offline_file}")  # Print success message
        except Exception as e:
            print(f"[ERROR] failed to write offline file: {e}")  # Print error message if log file cannot be written

        # Filter out missing and rewrite usernames.txt
        remaining = [u for u in usernames if u not in missing]  # Filter out missing usernames
        try:
            username_path.write_text("\n".join(remaining) + "\n")  # Rewrite usernames file with remaining usernames
            print(f"[INFO] Removed {len(missing)} missing usernames, {len(remaining)} remain.")  # Print success message
        except Exception as e:
            print(f"[ERROR] writing cleaned usernames: {e}")  # Print error message if usernames file cannot be written
    else:
        print("[INFO] No missing usernames to remove.")  # Print message if no missing usernames

if __name__ == "__main__":
    main()
