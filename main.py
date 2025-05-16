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

    try:
        with open(username_file) as f:
            candidates = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    try:
        with open(whitelist_file) as f:
            whitelist = {l.strip().lower() for l in f if l.strip()}
    except FileNotFoundError:
        whitelist = set()

    # — STEP 1: Fetch current follow lists & unfollow non-reciprocals —
    try:
        followers_set = {u.login.lower() for u in me.get_followers()}
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    unfollowed = 0
    for login, user in list(following_map.items()):
        if (
            login not in followers_set    # they don’t follow you back
            and login not in whitelist     # not whitelisted
            and login != me.login.lower()  # not yourself
        ):
            try:
                me.remove_from_following(user)
                unfollowed += 1
                print(f"[UNFOLLOWED] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {user.login}: {e}")
    print(f"Done unfollow phase: {unfollowed}")

    # — STEP 2: Refresh your live following list —
    try:
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] refreshing following list: {e}")

    # — STEP 3: Randomly pick up to per_run new users to follow —
    random.shuffle(candidates)
    to_follow = []
    for login in candidates:
        if len(to_follow) >= per_run:
            break
        ll = login.lower()
        # ← check here against refreshed following_map
        if ll == me.login.lower() or ll in following_map or ll in whitelist:
            continue
        to_follow.append(login)

    # — STEP 4: Follow the sampled users —
    followed = 0
    for login in to_follow:
        try:
            user = gh.get_user(login)
        except GithubException:
            print(f"[SKIP] {login} not found")
            continue
        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {login} ({followed}/{per_run})")
        except GithubException as e:
            print(f"[ERROR] could not follow {login}: {e}")
    print(f"Done follow phase: {followed}/{per_run}")

if __name__ == "__main__":
    main()
