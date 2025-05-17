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

    # — Determine base repo directory —
    base_dir = Path(__file__).parent.parent

    # — Config & load files —
    # allow overriding via env, else default to config/
    user_file   = os.getenv("USERNAME_FILE", "config/usernames.txt")
    white_file  = os.getenv("WHITELIST_FILE", "config/whitelist.txt")
    per_run     = int(os.getenv("FOLLOWERS_PER_RUN", 10))

    user_path  = (base_dir / user_file).resolve()
    white_path = (base_dir / white_file).resolve()

    if not user_path.exists():
        sys.exit(f"Username file not found: {user_path}")
    if not white_path.exists():
        print(f"[WARN] Whitelist file not found at {white_path}, proceeding with empty whitelist.")
        whitelist = set()
    else:
        with white_path.open() as f:
            whitelist = {ln.strip().lower() for ln in f if ln.strip()}

    # load candidates
    with user_path.open() as f:
        candidates = [ln.strip() for ln in f if ln.strip()]

    # — STEP 1: Unfollow non-reciprocals —
    followers = {u.login.lower() for u in me.get_followers()}
    following = {u.login.lower(): u for u in me.get_following()}

    unfollowed = 0
    for login, user in list(following.items()):
        if login not in followers and login not in whitelist and login != me.login.lower():
            try:
                me.remove_from_following(user)
                unfollowed += 1
                print(f"[UNFOLLOWED] {login}")
            except GithubException as e:
                print(f"[ERROR] unfollow {login}: {e}")
    print(f"Done unfollow phase: {unfollowed}")

    # — Refresh following list —
    following = {u.login.lower(): u for u in me.get_following()}

    # — STEP 2: Follow up to PER_RUN new users, skipping private/unfound ones —
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
            user = gh.get_user(login)
        except GithubException as e:
            if getattr(e, "status", None) == 404:
                notfound_new.append(login)
                print(f"[SKIP] {login} not found")
            else:
                private_new.append(login)
                print(f"[PRIVATE?] {login} exists but inaccessible: {e}")
            continue

        # attempt follow
        try:
            me.add_to_following(user)
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
        print("Not found (skipped) during follow phase:", notfound_new)
    if private_new:
        print("Private/inaccessible (skipped) during follow phase:", private_new)

    # — STEP 3: Follow-back your followers, skipping private/inaccessible ones —
    followers_map = {u.login.lower(): u for u in me.get_followers()}
    private_back = []
    back_count = 0

    for login, user in followers_map.items():
        ll = login.lower()
        if ll == me.login.lower() or ll in whitelist or ll in following:
            continue
        try:
            me.add_to_following(user)
            back_count += 1
            print(f"[FOLLOW-BACKED] {login}")
        except GithubException as e:
            if getattr(e, "status", None) == 403:
                private_back.append(login)
                print(f"[PRIVATE] cannot follow-back {login}: {e}")
            else:
                print(f"[ERROR] follow-back {login}: {e}")

    print(f"Done follow-back phase: {back_count} followed-back.")
    if private_back:
        print("Private/inaccessible skipped during follow-back:", private_back)

if __name__ == "__main__":
    main()
