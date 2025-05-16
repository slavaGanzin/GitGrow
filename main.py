import os
import sys
from github import Github, GithubException

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")

    gh = Github(token)
    me = gh.get_user()

    # load whitelist
    whitelist = set(
        usr.strip().lower()
        for usr in os.getenv("WHITELIST", "").split(",")
        if usr.strip()
    )

    # load list
    username_file = os.getenv("USERNAME_FILE", "usernames.txt")
    try:
        with open(username_file) as f:
            candidates = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    # how many to follow from list per run
    per_run = int(os.getenv("FOLLOWERS_PER_RUN", 10))

    # — prefetch your following list —
    try:
        already_following = {u.login.lower() for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your following list: {e}")

    # PART 1: follow next batch from file
    followed = 0
    for login in candidates:
        if followed >= per_run:
            break
        login_l = login.lower()
        if (
            login_l == me.login.lower()
            or login_l in already_following
            or login_l in whitelist
        ):
            continue

        # resolve user
        try:
            user = gh.get_user(login)
        except GithubException:
            print(f"[SKIP] {login} not found or inaccessible")
            continue

        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {login} ({followed}/{per_run})")
        except GithubException as e:
            print(f"[ERROR] could not follow {login}: {e}")

    print(f"Done follow-from-list: {followed}/{per_run}")

    # PART 2: follow back your followers
    try:
        followers = {u.login.lower(): u for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your followers: {e}")

    for login_l, user in followers.items():
        if (
            login_l not in already_following
            and login_l != me.login.lower()
            and login_l not in whitelist
        ):
            try:
                me.add_to_following(user)
                print(f"[FOLLOW-BACK] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not follow back {user.login}: {e}")

if __name__ == "__main__":
    main()

    # who you already follow
    try:
        already_following = {u.login for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your following list: {e}")

    # — PART 1: follow next batch from file —
    to_follow = []
    for login in candidates:
        if len(to_follow) >= per_run:
            break
        if login == me.login or login in already_following:
            continue
        to_follow.append(login)

    for login in to_follow:
        try:
            user = gh.get_user(login)
        except GithubException:
            print(f"[SKIP] {login} not found")
            continue

        try:
            me.add_to_following(user)
            print(f"[FOLLOWED] {login}")
        except GithubException as e:
            print(f"[ERROR] could not follow {login}: {e}")

    # — PART 2: follow back your followers —
    try:
        followers = {u.login: u for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your followers: {e}")

    for login, user in followers.items():
        if login not in already_following and login != me.login:
            try:
                me.add_to_following(user)
                print(f"[FOLLOW-BACK] {login}")
            except GithubException as e:
                print(f"[ERROR] could not follow back {login}: {e}")

if __name__ == "__main__":
    main()
