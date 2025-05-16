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

    # — Settings from env —
    username_file = os.getenv("USERNAME_FILE", "usernames.txt")
    per_run = int(os.getenv("FOLLOWERS_PER_RUN", 10))
    whitelist = {
        u.strip().lower()
        for u in os.getenv("WHITELIST", "").split(",")
        if u.strip()
    }

    # — Load candidate list —
    try:
        with open(username_file) as f:
            candidates = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    # — Who you already follow? —
    try:
        already_following = {u.login.lower() for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your following list: {e}")

    # — PART 1: Follow up to per_run from the file —
    followed = 0
    for login in candidates:
        if followed >= per_run:
            break
        ll = login.lower()
        if ll in already_following or ll == me.login.lower() or ll in whitelist:
            continue

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

    print(f"Done follow-from-list: {followed}/{per_run}")

    # — PART 2: Follow back anyone who follows you —
    try:
        followers = {u.login.lower(): u for u in me.get_followers()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your followers: {e}")

    for ll, user in followers.items():
        if ll not in already_following and ll != me.login.lower() and ll not in whitelist:
            try:
                me.add_to_following(user)
                print(f"[FOLLOW-BACK] {user.login}")
            except GithubException as e:
                print(f"[ERROR] could not follow back {user.login}: {e}")

if __name__ == "__main__":
    main()
