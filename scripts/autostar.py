#!/usr/bin/env python3

import os
import sys
import json
import random
import subprocess
from pathlib import Path
from github import Github

BOT_USER = os.getenv("BOT_USER")
TOKEN = os.getenv("GITHUB_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")
USERNAMES_PATH = Path("config/usernames.txt")
GROWTH_SAMPLE = 22

def main():
    if not TOKEN or not BOT_USER:
        sys.stderr.write("GITHUB_TOKEN and BOT_USER required\n")
        sys.exit(1)

    # Ensure state exists, create if not
    if not STATE_PATH.exists():
        print(f"{STATE_PATH} not found; running autotrack.py to generate state.")
        result = subprocess.run(["python3", "scripts/autotrack.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0 or not STATE_PATH.exists():
            sys.stderr.write("autotrack.py failed or did not create state; aborting.\n")
            print(result.stderr)
            sys.exit(1)

    gh = Github(TOKEN)
    me = gh.get_user()

    # Load state
    with open(STATE_PATH) as f:
        state = json.load(f)
    current_stargazers = set(state.get("current_stargazers", []))
    starred_users = state.get("starred_users", {})
    unstargazers = set(state.get("unstargazers", []))

    # 1. Star new stargazers
    new_to_star = [u for u in current_stargazers if u not in starred_users]
    for user in new_to_star:
        try:
            u = gh.get_user(user)
            repos = [r for r in u.get_repos() if not r.fork and not r.private]
            if not repos:
                continue
            repo = random.choice(repos)
            me.add_to_starred(repo)
            starred_users[user] = [repo.full_name]
            print(f"Starred {repo.full_name} for {user}")
        except Exception as e:
            print(f"Failed to star for {user}: {e}")

    # 2. Unstar repos of unstargazers
    for user in list(unstargazers):
        if user in starred_users:
            for repo_name in starred_users[user]:
                try:
                    repo = gh.get_repo(repo_name)
                    me.remove_from_starred(repo)
                    print(f"Unstarred {repo.full_name} (user {user} unstarred you)")
                except Exception as e:
                    print(f"Failed to unstar {repo_name}: {e}")
            del starred_users[user]

    # 3. Growth: star new users from usernames.txt
    if USERNAMES_PATH.exists():
        with open(USERNAMES_PATH) as f:
            all_usernames = [line.strip() for line in f if line.strip()]
        available = set(all_usernames) - current_stargazers - set(starred_users)
        sample = random.sample(list(available), min(GROWTH_SAMPLE, len(available)))
        for user in sample:
            try:
                u = gh.get_user(user)
                repos = [r for r in u.get_repos() if not r.fork and not r.private]
                if not repos:
                    continue
                repo = random.choice(repos)
                me.add_to_starred(repo)
                starred_users[user] = [repo.full_name]
                print(f"Growth: Starred {repo.full_name} for {user}")
            except Exception as e:
                print(f"Failed to star for growth {user}: {e}")

    # 4. Save updated state
    state["starred_users"] = starred_users
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Updated state written to {STATE_PATH}")

if __name__ == "__main__":
    main()
