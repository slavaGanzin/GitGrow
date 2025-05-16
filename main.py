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

    try:
        with open(whitelist_file) as f:
            whitelist = {l.strip().lower() for l in f if l.strip()}
    except FileNotFoundError:
        whitelist = set()

    # — STEP 1: Unfollow non-reciprocals —
    try:
        followers_set = {u.login.lower() for u in me.get_followers()}
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    unfollowed = 0
    for login, user in list(following_map.items()):
        if login not in followers_set and login not in whitelist and login != me.login.lower():
            try:
                me.remove_from_following(user)
                unfollowed += 1
                print(f"[UNFOLLOWED] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {user.login}: {e}")
    print(f"Done unfollow phase: {unfollowed}")

    # — STEP 2: Refresh your following list —
    try:
        following_map = {u.login.lower(): u for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] refreshing following list: {e}")

    # — STEP 3: SAMPLE up to per_run EXISTING users to follow —
    random.shuffle(candidates)
    to_follow = []
    for login in candidates:
        if len(to_follow) >= per_run:
            break

        ll = login.lower()
        # skip self, already following, whitelist
        if ll == me.login.lower() or ll in following_map or ll in whitelist:
            continue

        # existence check
        try:
            user = gh.get_user(login)
        except GithubException:
            print(f"[SKIP] {login} not found")
            continue

        to_follow.append(user)  # store the actual NamedUser
    print(f"Sampling complete: will follow {len(to_follow)}/{per_run} users.")

    # — STEP 4: FOLLOW the sampled users —
    followed = 0
    for user in to_follow:
        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {user.login}")
        except GithubException as e:
            print(f"[ERROR] could not follow {user.login}: {e}")
    print(f"Done follow phase: {followed}/{per_run}")

if __name__ == "__main__":
    main()
