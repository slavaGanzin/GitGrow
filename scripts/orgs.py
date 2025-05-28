#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from github import Github, GithubException

def main():
    # — Auth & client setup —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("[FATAL] GITHUB_TOKEN environment variable is required")

    gh = Github(token)
    try:
        me = gh.get_user()
    except GithubException as e:
        sys.exit(f"[FATAL] could not get authenticated user: {e}")

    # — Load target organizations —
    base_dir  = Path(__file__).parent.parent.resolve()
    orgs_path = base_dir / "config" / "organizations.txt"
    if not orgs_path.is_file():
        sys.exit(f"[FATAL] organizations file not found: {orgs_path}")

    with orgs_path.open() as f:
        org_logins = [ln.strip() for ln in f if ln.strip()]

    print(f"[INFO] loaded {len(org_logins)} organization(s) to process")

    # — Process each org —
    for login in org_logins:
        print(f"[INFO] processing '{login}'")
        # fetch as a NamedUser (works for both users & orgs)
        try:
            target = gh.get_user(login)
        except GithubException as e:
            print(f"[ERROR] cannot fetch '{login}': {e}")
            continue

        # unfollow if currently following
        try:
            me.remove_from_following(target)
        except GithubException as e:
            status = getattr(e, "status", None)
            if status == 404:
                print(f"[INFO] not following '{login}', skipping unfollow")
            else:
                print(f"[WARN] error unfollowing '{login}': {e}")
        else:
            print(f"[UNFOLLOWED] '{login}'")

        # follow again
        try:
            me.add_to_following(target)
        except GithubException as e:
            print(f"[ERROR] error following '{login}': {e}")
        else:
            print(f"[FOLLOWED] '{login}'")

if __name__ == "__main__":
    main()