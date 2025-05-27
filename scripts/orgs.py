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
    orgs_path = base_dir / "config" / "organizations.txt"
    if not orgs_path.exists():
        sys.exit(f"Organization file not found: {orgs_path}")
    with orgs_path.open() as f:
        org_logins = [ln.strip() for ln in f if ln.strip()]

    for login in org_logins:
        try:
            org = gh.get_organization(login)
        except GithubException as e:
            print(f"[ERROR] fetching org {login}: {e}")
            continue

        # always try to unfollow (ignore failures), then follow
        try:
            me.remove_from_following(org)
            print(f"[UNFOLLOWED] {login}")
        except GithubException:
            pass

        try:
            me.add_to_following(org)
            print(f"[FOLLOWED] {login}")
        except GithubException as e:
            print(f"[ERROR] following {login}: {e}")

if __name__ == "__main__":
    main()