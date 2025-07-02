#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from github import Github

BOT_USER = os.getenv("BOT_USER")
TOKEN = os.getenv("PAT_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")

def main():
    print("=== GitGrowBot autotrack.py started ===")
    if not TOKEN or not BOT_USER:
        print("ERROR: PAT_TOKEN and BOT_USER required", file=sys.stderr)
        sys.exit(1)
    print(f"PAT_TOKEN and BOT_USER env vars present.")
    print(f"BOT_USER: {BOT_USER}")

    print("Authenticating with GitHub...")
    gh = Github(TOKEN)
    try:
        user = gh.get_user(BOT_USER)
        print(f"Authenticated as: {user.login}")
    except Exception as e:
        print("ERROR: Could not authenticate with GitHub:", e)
        sys.exit(1)

    print("Collecting all public, non-fork repos owned by BOT_USER...")
    try:
        repos = [r for r in user.get_repos(type="owner") if not r.fork and not r.private]
        print(f"Found {len(repos)} repos.")
    except Exception as e:
        print("ERROR: Failed to list repos:", e)
        sys.exit(1)

    # Gather unique stargazer usernames across all repos
    stargazer_set = set()
    for idx, repo in enumerate(repos):
        print(f"[{idx+1}/{len(repos)}] Processing repo: {repo.full_name}")
        try:
            count = 0
            for u in repo.get_stargazers():
                stargazer_set.add(u.login)
                count += 1
                if count % 20 == 0:
                    print(f"    {count} stargazers fetched so far for this repo...")
            print(f"    Total stargazers fetched for {repo.full_name}: {count}")
        except Exception as e:
            print(f"    ERROR fetching stargazers for {repo.full_name}: {e}")

    current_stargazers = sorted(stargazer_set)
    print(f"Total unique stargazers across all repos: {len(current_stargazers)}")

    # Load previous state if exists
    if STATE_PATH.exists():
        print(f"Loading previous state from {STATE_PATH} ...")
        with open(STATE_PATH, "r") as f:
            state = json.load(f)
        previous_stargazers = set(state.get("current_stargazers", []))
        starred_users = state.get("starred_users", {})
        print(f"Previous stargazers: {len(previous_stargazers)}, starred_users: {len(starred_users)}")
    else:
        print("No previous state found.")
        previous_stargazers = set()
        starred_users = {}

    # Detect unstargazers: users who have unstarred since last run
    unstargazers = sorted(list(previous_stargazers - stargazer_set))
    print(f"Unstargazers detected: {len(unstargazers)}")

    # Save new state
    print("Saving new state ...")
    new_state = {
        "current_stargazers": current_stargazers,
        "starred_users": starred_users,
        "unstargazers": unstargazers
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(new_state, f, indent=2)
    print(f"Saved user-level stargazer state to {STATE_PATH}")
    print("=== GitGrowBot autotrack.py finished ===")

if __name__ == "__main__":
    main()
