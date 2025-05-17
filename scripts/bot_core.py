#!/usr/bin/env python3
import os
import sys
import random
from pathlib import Path
from github import Github, GithubException

def main():
    # — Auth & client setup —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    # — Determine repo root & config paths —
    base_dir   = Path(__file__).parent.parent.resolve()
    user_path  = base_dir / "config" / "usernames.txt"
    white_path = base_dir / "config" / "whitelist.txt"
    per_run    = 100

    # — Load whitelist —
    if white_path.exists():
        with white_path.open() as f:
            whitelist = {ln.strip().lower() for ln in f if ln.strip()}
    else:
        print(f"[WARN] config/whitelist.txt not found, proceeding with empty whitelist")
        whitelist = set()

    # — Load candidate usernames —
    if not user_path.exists():
        sys.exit(f"Username file not found: {user_path}")
    with user_path.open() as f:
        candidates = [ln.strip() for ln in f if ln.strip()]

    # --- STEP 1: Unfollow non-reciprocals (difference-based) ---
    try:
        followers = {u.login.lower() for u in me.get_followers()}
        following = {u.login.lower() for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    # Compute exactly who to unfollow
    to_unfollow = (
        following
        - followers                                     # they don’t follow you back
        - whitelist                                    # except whitelisted
        - {me.login.lower()}                           # never yourself
    )

    unfollowed = 0
    for login in to_unfollow:
        try:
            me.remove_from_following(login)
            unfollowed += 1
            print(f"[UNFOLLOWED] {login}")
        except GithubException as e:
            print(f"[ERROR] could not unfollow {login}: {e}")
    print(f"Done unfollow phase: {unfollowed}")

    # — Refresh following list after unfollowing —
    following = {u.login.lower() for u in me.get_following()}

    # --- STEP 2: Follow up to per_run new users ---
    random.shuffle(candidates)
    new_followed = 0
    notfound_new = []
    private_new = []

    for login in candidates:
        if new_followed >= per_run:
            break

        ll = login.lower()
        if ll == me.login.lower() or ll in whitelist or ll in following:
            continue

        # existence check
        try:
            gh.get_user(login)
        except GithubException as e:
            if getattr(e, "status", None) == 404:
                notfound_new.append(login)
                print(f"[SKIP] {login} not found")
            else:
                private_new.append(login)
                print(f"[PRIVATE] {login} inaccessible: {e}")
            continue

        # attempt follow
        try:
            me.add_to_following(login)
            new_followed += 1
            print(f"[FOLLOWED] {login} ({new_followed}/{per_run})")
        except GithubException as e:
            if getattr(e, "status", None) == 403:
                private_new.append(login)
                print(f"[PRIVATE] cannot follow {login}: {e}")
            else:
                print(f"[ERROR] follow {login}: {e}")

    print(f"Done follow phase: {new_followed}/{per_run} followed.")
    if notfound_new:
        print("Not found during follow phase:", notfound_new)
    if private_new:
        print("Private/inaccessible during follow phase:", private_new)

    # --- STEP 3: Follow-back current followers ---
    try:
        followers_now = {u.login.lower() for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching followers for follow-back: {e}")

    back_count = 0
    private_back = []

    for login in followers_now - following - whitelist - {me.login.lower()}:
        try:
            me.add_to_following(login)
            back_count += 1
            print(f"[FOLLOW-BACKED] {login}")
        except GithubException as e:
            if getattr(e, "status", None) == 403:
                private_back.append(login)
                print(f"[PRIVATE] cannot follow-back {login}: {e}")
            else:
                print(f"[ERROR] follow-back {login}: {e}")

    print(f"Done follow-back phase: {back_count}")
    if private_back:
        print("Private/inaccessible during follow-back:", private_back)

if __name__ == "__main__":
    main()
