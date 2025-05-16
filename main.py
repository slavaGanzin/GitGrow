import os
import sys
import random
from github import Github, GithubException

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")

    gh = Github(token)
    me = gh.get_user()

    # load usernames
    USERNAME_FILE = os.getenv("USERNAME_FILE", "usernames.txt")
    try:
        with open(USERNAME_FILE) as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {USERNAME_FILE}")
    if not targets:
        sys.exit("No usernames found in file")

    # configuration
    NUM_TARGETS = int(os.getenv("NUM_TARGETS", 1))
    FOLLOWERS_PER_TARGET = int(os.getenv("FOLLOWERS_PER_TARGET", 20))

    # pick random targets
    sample = random.sample(targets, min(NUM_TARGETS, len(targets)))

    # STEP 1: follow up to FOLLOWERS_PER_TARGET followers of each sample
    for user_login in sample:
        try:
            user = gh.get_user(user_login)
            followers = list(user.get_followers())[:FOLLOWERS_PER_TARGET]
        except GithubException as e:
            print(f"[ERROR] fetching followers of {user_login}: {e}")
            continue

        for u in followers:
            try:
                me.add_to_following(u)
                print(f"Followed {u.login}")
            except GithubException as e:
                print(f"[ERROR] could not follow {u.login}: {e}")

    # STEP 2: unfollow anyone who isn’t following you back
    try:
        current_followers = {u.login for u in me.get_followers()}
        current_following = list(me.get_following())
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    for u in current_following:
        if u.login not in current_followers:
            try:
                me.remove_from_following(u)
                print(f"Unfollowed {u.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {u.login}: {e}")

if __name__ == "__main__":
    main()

