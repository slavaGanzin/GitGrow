#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from github import Github

BOT_USER = os.getenv("BOT_USER")
TOKEN = os.getenv("GITHUB_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")

def main():
    if not TOKEN or not BOT_USER:
        sys.stderr.write("GITHUB_TOKEN and BOT_USER required\n")
        sys.exit(1)

    gh = Github(TOKEN)
    user = gh.get_user(BOT_USER)

    # Collect all public, non-fork repos owned by BOT_USER
    repos = [r for r in user.get_repos(type="owner") if not r.fork and not r.private]

    # Gather unique stargazer usernames across all repos
    stargazer_set = set()
    for repo in repos:
        for u in repo.get_stargazers():
            stargazer_set.add(u.login)
    current_stargazers = sorted(stargazer_set)

    # Load previous state if exists
    if STATE_PATH.exists():
        with open(STATE_PATH, "r") as f:
            state = json.load(f)
        previous_stargazers = set(state.get("current_stargazers", []))
        starred_users = state.get("starred_users", {})
    else:
        previous_stargazers = set()
        starred_users = {}

    # Detect unstargazers: users who have unstarred since last run
    unstargazers = sorted(list(previous_stargazers - stargazer_set))

    # Save new state
    new_state = {
        "current_stargazers": current_stargazers,
        "starred_users": starred_users,
        "unstargazers": unstargazers
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(new_state, f, indent=2)
    print(f"Saved user-level stargazer state to {STATE_PATH}")

if __name__ == "__main__":
    main()
