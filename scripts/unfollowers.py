#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from github import Github, GithubException

def main():
    # — Auth & client setup —
    token = os.getenv("GITHUB_TOKEN")  # Retrieve GitHub token from environment variables
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")  # Exit if token is not found
    gh = Github(token)  # Initialize GitHub client
    me = gh.get_user()  # Get authenticated user

    # — Load whitelist —
    base_dir   = Path(__file__).parent.parent.resolve()  # Determine base directory of the repository
    white_path = base_dir / "config" / "whitelist.txt"  # Path to the whitelist configuration file
    if white_path.exists():
        with white_path.open() as f:
            whitelist = {ln.strip().lower() for ln in f if ln.strip()}  # Load whitelist from file
    else:
        print(f"[WARN] config/whitelist.txt not found, proceeding with empty whitelist")
        whitelist = set()  # Initialize empty whitelist if file is not found

    # — Fetch your followers and following —
    try:
        followers     = {u.login.lower() for u in me.get_followers()}  # Fetch list of followers
        following_map = {u.login.lower(): u for u in me.get_following()}  # Fetch list of users the authenticated user is following
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")  # Exit if there is an error fetching the lists

    # — Compute who to unfollow —
    to_unfollow = [
        login for login in following_map
        if login not in followers
        and login not in whitelist
        and login != me.login.lower()
    ]  # Determine users to unfollow

    # — Unfollow them by passing the NamedUser object —
    unfollowed = 0  # Counter for unfollowed users
    for login in to_unfollow:
        user = following_map[login]
        try:
            me.remove_from_following(user)  # Attempt to unfollow the user
            unfollowed += 1
            print(f"[UNFOLLOWED] {login}")  # Print success message
        except GithubException as e:
            print(f"[ERROR] could not unfollow {login}: {e}")  # Print error message if the user cannot be unfollowed

    print(f"Done unfollow phase: {unfollowed}")  # Print summary of unfollow phase

if __name__ == "__main__":
    main()
