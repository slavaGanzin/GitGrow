import os
import sys
import random
from github import Github, GithubException

def main():
    # — Environment & GitHub client —
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN environment variable is required")
    gh = Github(token)
    me = gh.get_user()

    # — Load targets from file —
    username_file = os.getenv("USERNAME_FILE", "usernames.txt")
    try:
        with open(username_file) as f:
            candidates = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    # — Configuration —
    num_targets = int(os.getenv("NUM_TARGETS", len(candidates)))
    followers_per_target = int(os.getenv("FOLLOWERS_PER_TARGET", 50))

    # — Pick a random subset of target accounts —
    targets = random.sample(candidates, min(num_targets, len(candidates)))

    # — STEP 1: FOLLOW their followers —
    for target in targets:
        try:
            user = gh.get_user(target)
            all_followers = list(user.get_followers())
        except GithubException as e:
            print(f"[ERROR] fetching followers of {target}: {e}")
            continue

        to_follow = all_followers[:followers_per_target]
        for u in to_follow:
            try:
                me.add_to_following(u)
                print(f"Followed: {u.login}")
            except GithubException as e:
                print(f"[ERROR] follow {u.login}: {e}")

    # — STEP 2: UNFOLLOW non-reciprocals —
    try:
        current_followers = {u.login for u in me.get_followers()}
        current_following = list(me.get_following())
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your follow lists: {e}")

    for u in current_following:
        if u.login not in current_followers:
            try:
                me.remove_from_following(u)
                print(f"Unfollowed: {u.login}")
            except GithubException as e:
                print(f"[ERROR] unfollow {u.login}: {e}")

if __name__ == "__main__":
    main()
