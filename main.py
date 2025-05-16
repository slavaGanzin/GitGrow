import os
import sys
import random
from github import Github, GithubException

def main():
    # — Auth —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    # — Config & load files —
    USER_FILE      = os.getenv("USERNAME_FILE", "usernames.txt")
    WHITE_FILE     = os.getenv("WHITELIST_FILE", "whitelist.txt")
    PER_RUN        = int(os.getenv("FOLLOWERS_PER_RUN", 10))

    try:
        with open(USER_FILE) as f:
            candidates = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {USER_FILE}")
    try:
        with open(WHITE_FILE) as f:
            whitelist = {l.strip().lower() for l in f if l.strip()}
    except FileNotFoundError:
        whitelist = set()

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

    # — STEP 2: Refresh following list —
    following = {u.login.lower(): u for u in me.get_following()}

    # — STEP 3: Sample & follow fresh users (with existence+private checks) —
    random.shuffle(candidates)
    to_follow = []
    private_new = []

    for login in candidates:
        if len(to_follow) >= PER_RUN:
            break
        ll = login.lower()
        if ll in following or ll in whitelist or ll == me.login.lower():
            continue

        # existence check
        try:
            user = gh.get_user(login)
        except GithubException as e:
            if getattr(e, "status", None) == 404:
                print(f"[SKIP] {login} not found")
            else:
                private_new.append(login)
                print(f"[PRIVATE?] {login} exists but inaccessible: {e}")
            continue

        to_follow.append(user)

    print(f"Sampling complete: {len(to_follow)}/{PER_RUN} will be followed.")
    for user in to_follow:
        try:
            me.add_to_following(user)
            print(f"[FOLLOWED] {user.login}")
        except GithubException as e:
            print(f"[ERROR] follow {user.login}: {e}")
    if private_new:
        print("Private/inaccessible accounts when sampling:")
        for u in private_new:
            print(f" - {u}")

    # — STEP 4: Follow-back your followers (detect private) —
    # refresh followers
    followers_map = {u.login.lower(): u for u in me.get_followers()}
    private_back = []
    back_count = 0

    for login, user in followers_map.items():
        if login in following or login in whitelist or login == me.login.lower():
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

    print(f"Done follow-back phase: {back_count}")
    if private_back:
        print("Private/inaccessible accounts during follow-back:")
        for u in private_back:
            print(f" - {u}")

if __name__ == "__main__":
    main()
