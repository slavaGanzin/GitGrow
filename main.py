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
    username_file  = os.getenv("USERNAME_FILE", "usernames.txt")
    whitelist_file = os.getenv("WHITELIST_FILE", "whitelist.txt")
    per_run        = int(os.getenv("FOLLOWERS_PER_RUN", 10))

    # load candidate usernames
    try:
        with open(username_file) as f:
            candidates = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")

    # load whitelist
    try:
        with open(whitelist_file) as f:
            whitelist = {l.strip().lower() for l in f if l.strip()}
    except FileNotFoundError:
        whitelist = set()

    # STEP 1: Unfollow non-reciprocals
    try:
        followers_set = {u.login.lower() for u in me.get_followers()}
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    unfollowed = 0
    for login, user in list(following_map.items()):
        if (
            login not in followers_set
            and login not in whitelist
            and login != me.login.lower()
        ):
            try:
                me.remove_from_following(user)
                unfollowed += 1
                print(f"[UNFOLLOWED] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {user.login}: {e}")
    print(f"Done unfollow phase: {unfollowed}")

    # STEP 2: Refresh your following list
    try:
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] refreshing following list: {e}")

    # STEP 3: Sample & follow NEW users (with existence check)
    random.shuffle(candidates)
    to_follow = []
    for login in candidates:
        if len(to_follow) >= per_run:
            break
        ll = login.lower()
        if ll in following_map or ll in whitelist or ll == me.login.lower():
            continue

        # existence check
        try:
            user = gh.get_user(login)
        except GithubException as e:
            if getattr(e, 'status', None) == 404:
                print(f"[SKIP] {login} not found")
            else:
                print(f"[PRIVATE?] {login} exists but can’t access: {e}")
            continue

        to_follow.append(user)

    print(f"Will attempt to follow {len(to_follow)}/{per_run} new users.")

    followed = 0
    for user in to_follow:
        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {user.login}")
        except GithubException as e:
            print(f"[ERROR] could not follow {user.login}: {e}")
    print(f"Done follow phase: {followed}/{per_run}")

    # STEP 4: Follow-back your followers (with private detection)
    try:
        followers_map = {u.login.lower(): u for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching followers for follow-back: {e}")

    private_back = []
    back_count = 0

    for login, user in followers_map.items():
        if login in following_map or login in whitelist or login == me.login.lower():
            continue

        # attempt follow-back
        try:
            me.add_to_following(user)
            back_count += 1
            print(f"[FOLLOW-BACKED] {login}")
        except GithubException as e:
            if getattr(e, 'status', None) == 403:
                private_back.append(login)
                print(f"[PRIVATE] cannot follow-back {login}: {e}")
            else:
                print(f"[ERROR] follow-back {login} failed: {e}")

    print(f"Done follow-back phase: {back_count} followed back.")

    if private_back:
        print("Private/inaccessible accounts during follow-back:")
        for u in private_back:
            print(f"  - {u}")

if __name__ == "__main__":
    main()
