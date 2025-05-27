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

    # — Paths & load org list —
    base_dir    = Path(__file__).parent.parent.resolve()
    orgs_path   = base_dir / "config" / "organizations.txt"
    if not orgs_path.exists():
        sys.exit(f"Organization file not found: {orgs_path}")
    with orgs_path.open() as f:
        org_logins = [ln.strip() for ln in f if ln.strip()]

    # — Fetch current following once —
    try:
        following = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching following list: {e}")

    # — Iterate orgs —
    for login in org_logins:
        ll = login.lower()
        try:
            org = gh.get_organization(login)
        except GithubException as e:
            print(f"[ERROR] fetching org {login}: {e}")
            continue

        if ll in following:
            # unfollow then refollow
            try:
                me.remove_from_following(org)
                print(f"[UNFOLLOWED] {login}")
            except GithubException as e:
                print(f"[ERROR] unfollowing {login}: {e}")
                continue

            try:
                me.add_to_following(org)
                print(f"[REFOLLOWED] {login}")
            except GithubException as e:
                print(f"[ERROR] refollowing {login}: {e}")
        else:
            # first-time follow
            try:
                me.add_to_following(org)
                print(f"[FOLLOWED] {login}")
            except GithubException as e:
                print(f"[ERROR] following {login}: {e}")

if __name__ == "__main__":
    main()