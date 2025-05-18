#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from github import Github, GithubException

def main():
    # — Auth & client setup —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    # — Load whitelist —
    base_dir   = Path(__file__).parent.parent.resolve()
    white_path = base_dir / "config" / "whitelist.txt"
    if white_path.exists():
        with white_path.open() as f:
            whitelist = {ln.strip().lower() for ln in f if ln.strip()}
    else:
        print(f"[WARN] config/whitelist.txt not found, proceeding with empty whitelist")
        whitelist = set()

    # — Fetch your followers and following —
    try:
        followers     = {u.login.lower() for u in me.get_followers()}
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    # — Compute who to unfollow —
    to_unfollow = [
        login for login in following_map
        if login not in followers
        and login not in whitelist
        and login != me.login.lower()
    ]

    # — Unfollow them by passing the NamedUser object —
    unfollowed = 0
    for login in to_unfollow:
        user = following_map[login]
        try:
            me.remove_from_following(user)
            unfollowed += 1
            print(f"[UNFOLLOWED] {login}")
        except GithubException as e:
            print(f"[ERROR] could not unfollow {login}: {e}")

    print(f"Done unfollow phase: {unfollowed}")

if __name__ == "__main__":
    main()
