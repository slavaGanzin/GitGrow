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

    # Gather stargazers and prepare reciprocity mapping
    stargazer_set = set()
    reciprocity = {}

    for idx, repo in enumerate(repos):
        print(f"[{idx+1}/{len(repos)}] Processing repo: {repo.full_name}")
        try:
            count = 0
            for u in repo.get_stargazers():
                login = u.login
                stargazer_set.add(login)
                if login not in reciprocity:
                    reciprocity[login] = {"starred_by": [], "starred_back": []}
                reciprocity[login]["starred_by"].append(repo.full_name)
                count += 1
                if count % 20 == 0:
                    print(f"    {count} stargazers fetched so far for this repo...")
            print(f"    Total stargazers fetched for {repo.full_name}: {count}")
        except Exception as e:
            print(f"    ERROR fetching stargazers for {repo.full_name}: {e}")

    current_stargazers = sorted(stargazer_set)
    print(f"Total unique stargazers across all repos: {len(current_stargazers)}")

    # Load previous state if exists (keep mutual_stars for legacy)
    if STATE_PATH.exists():
        print(f"Loading previous state from {STATE_PATH} ...")
        with open(STATE_PATH, "r") as f:
            state = json.load(f)
        previous_stargazers = set(state.get("current_stargazers", []))
        mutual_stars = state.get("mutual_stars", {})
        # Optionally, try to keep old starred_back for each user
        if "reciprocity" in state:
            for user, info in state["reciprocity"].items():
                if user in reciprocity:
                    reciprocity[user]["starred_back"] = info.get("starred_back", [])
        print(f"Previous stargazers: {len(previous_stargazers)}, mutual_stars: {len(mutual_stars)}")
    else:
        print("No previous state found.")
        previous_stargazers = set()
        mutual_stars = {}

    # Detect unstargazers: users who have unstarred since last run
    unstargazers = sorted(list(previous_stargazers - stargazer_set))
    print(f"Unstargazers detected: {len(unstargazers)}")

    # Save new state
    print("Saving new state ...")
    new_state = {
        "current_stargazers": current_stargazers,
        "mutual_stars": mutual_stars,
        "unstargazers": unstargazers,
        "reciprocity": reciprocity,
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(new_state, f, indent=2)
    print(f"Saved user-level stargazer state to {STATE_PATH}")
    print("=== GitGrowBot autotrack.py finished ===")

if __name__ == "__main__":
    main()
