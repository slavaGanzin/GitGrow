import os
import sys
from github import Github, GithubException

def main():
    # — GitHub auth —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    # — Config from env & files —
    username_file  = os.getenv("USERNAME_FILE", "usernames.txt")
    whitelist_file = os.getenv("WHITELIST_FILE", "whitelist.txt")
    per_run        = int(os.getenv("FOLLOWERS_PER_RUN", 10))

    # — Load candidate list —
    try:
        with open(username_file) as f:
            candidates = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    # — Load whitelist —
    try:
        with open(whitelist_file) as f:
            whitelist = {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        whitelist = set()

    # — Prefetch your following & followers —
    try:
        following     = {u.login.lower(): u for u in me.get_following()}
        followers     = {u.login.lower() for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    # — PART 1: Follow up to per_run from list —
    followed = 0
    for login in candidates:
        if followed >= per_run:
            break

        ll = login.lower()
        # skip self, already following, whitelist
        if ll == me.login.lower() or ll in following or ll in whitelist:
            continue

        # validate user exists
        try:
            user = gh.get_user(login)
        except GithubException:
            print(f"[SKIP] {login} not found or inaccessible")
            continue

        # attempt follow
        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {login} ({followed}/{per_run})")
        except GithubException as e:
            print(f"[ERROR] could not follow {login}: {e}")

    print(f"Done follow phase: {followed}/{per_run}")

    # — PART 2: Unfollow non-reciprocals (excluding whitelist) —
    unfollowed = 0
    for ll, user in following.items():
        # only unfollow if they do not follow you back, and are not whitelisted or yourself
        if ll not in followers and ll not in whitelist and ll != me.login.lower():
            try:
                me.remove_from_following(user)
                unfollowed += 1
                print(f"[UNFOLLOWED] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {user.login}: {e}")

    print(f"Done unfollow phase: {unfollowed}")

if __name__ == "__main__":
    main()
