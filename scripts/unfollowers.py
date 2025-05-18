#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from github import Github, GithubException

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    base_dir  = Path(__file__).parent.parent.resolve()
    white_path = base_dir / "config" / "whitelist.txt"

    if white_path.exists():
        with white_path.open() as f:
            whitelist = {line.strip().lower() for line in f if line.strip()}
    else:
        print(f"[WARN] no whitelist.txt found, proceeding with empty whitelist")
        whitelist = set()

    # fetch fresh lists
    followers = {u.login.lower() for u in me.get_followers()}
    following = list(me.get_following())

    unfollowed = 0
    for user in following:
        login = user.login.lower()
        if (login not in followers
            and login not in whitelist
            and login != me.login.lower()
        ):
            try:
                me.remove_from_following(login)
                unfollowed += 1
                print(f"[UNFOLLOWED] {login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {login}: {e}")

    print(f"Done unfollow phase: {unfollowed}")

if __name__ == "__main__":
    main()
