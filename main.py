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

    # load all candidate usernames
    username_file = os.getenv("USERNAME_FILE", "usernames.txt")
    try:
        with open(username_file) as f:
            candidates = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        sys.exit(f"Username file not found: {username_file}")
    if not candidates:
        sys.exit("No usernames found in file")

    # how many to follow this run
    to_follow_target = int(os.getenv("FOLLOWERS_PER_RUN", 50))

    # shuffle and iterate until we hit the target
    random.shuffle(candidates)
    followed = 0

    # fetch whom we already follow
    try:
        already_following = {u.login for u in me.get_following()}
    except GithubException as e:
        sys.exit(f"[ERROR] fetching your following list: {e}")

    for login in candidates:
        if followed >= to_follow_target:
            break
        if login == me.login or login in already_following:
            # skip yourself or anyone you're already following
            continue

        # try to resolve the user
        try:
            user = gh.get_user(login)
        except GithubException:
            # user not found or inaccessible; skip
            print(f"[SKIP] {login} not found")
            continue

        # attempt to follow
        try:
            me.add_to_following(user)
            followed += 1
            print(f"[FOLLOWED] {login} ({followed}/{to_follow_target})")
        except GithubException as e:
            print(f"[ERROR] could not follow {login}: {e}")

    print(f"Finished follow phase: followed {followed} of {to_follow_target} requested")

    # — now unfollow anyone who isn't following you back —
    try:
        current_followers = {u.login for u in me.get_followers()}
        current_following = list(me.get_following())
    except GithubException as e:
        sys.exit(f"[ERROR] fetching follow lists: {e}")

    for u in current_following:
        if u.login not in current_followers:
            try:
                me.remove_from_following(u)
                print(f"[UNFOLLOWED] {u.login}")
            except GithubException as e:
                print(f"[ERROR] could not unfollow {u.login}: {e}")

if __name__ == "__main__":
    main()
