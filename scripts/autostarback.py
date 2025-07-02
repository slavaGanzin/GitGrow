#!/usr/bin/env python3

import os
import sys
import json
import random
import subprocess
from pathlib import Path
from github import Github
from datetime import datetime, timezone

BOT_USER = os.getenv("BOT_USER")
TOKEN = os.getenv("PAT_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")
RECIPROCITY_LIMIT = 20   # Limit for reciprocal (stargazer) starring per run

def main():
    print("=== GitGrowBot autostarback.py started ===")

    if not TOKEN or not BOT_USER:
        print("ERROR: PAT_TOKEN and BOT_USER required", file=sys.stderr)
        sys.exit(1)
    print(f"PAT_TOKEN and BOT_USER env vars present.")
    print(f"BOT_USER: {BOT_USER}")

    # Ensure state exists, create if not
    if not STATE_PATH.exists():
        print(f"{STATE_PATH} not found; running autotrack.py to generate state.")
        result = subprocess.run(["python3", "scripts/autotrack.py"], capture_output=True, text=True)
        print("[autotrack.py stdout]:", result.stdout)
        if result.returncode != 0 or not STATE_PATH.exists():
            print("ERROR: autotrack.py failed or did not create state; aborting.", file=sys.stderr)
            print("[autotrack.py stderr]:", result.stderr)
            sys.exit(1)
        print("autotrack.py succeeded, state created.")

    print("Authenticating with GitHub...")
    gh = Github(TOKEN)
    try:
        me = gh.get_user()
        print(f"Authenticated as: {me.login}")
    except Exception as e:
        print("ERROR: Could not authenticate with GitHub:", e)
        sys.exit(1)

    print(f"Loading state from {STATE_PATH} ...")
    with open(STATE_PATH) as f:
        state = json.load(f)
    current_stargazers = set(state.get("current_stargazers", []))
    starred_users = state.get("starred_users", {})
    print(f"Loaded {len(current_stargazers)} stargazers, {len(starred_users)} starred_users.")

    # Star back new stargazers (reciprocity, up to limit)
    print(f"== Star new stargazers: {len(current_stargazers)} to check ==")
    new_to_star = [u for u in current_stargazers if u not in starred_users]
    print(f"Found {len(new_to_star)} new users to star. Limiting to {RECIPROCITY_LIMIT} per run.")
    new_to_star = new_to_star[:RECIPROCITY_LIMIT]  # Limit per run

    now = datetime.now(timezone.utc).isoformat()
    for i, user in enumerate(new_to_star):
        print(f"  [{i+1}/{len(new_to_star)}] Processing user: {user}")
        try:
            u = gh.get_user(user)
            # Fetch up to first 5 public, non-fork repos
            repos = [r for r in u.get_repos() if not r.fork and not r.private][:5]
            print(f"    Found {len(repos)} public non-fork repos for {user} (first 5 considered)")
            if not repos:
                print(f"    No public repos to star for {user}, skipping.")
                continue
            repo = random.choice(repos)
            print(f"    Starring repo: {repo.full_name}")
            me.add_to_starred(repo)
            # Store as object with repo and timestamp
            starred_users[user] = [{
                "repo": repo.full_name,
                "starred_at": now
            }]
            print(f"    Starred {repo.full_name} for {user} at {now}")
        except Exception as e:
            print(f"    Failed to star for {user}: {e}")

    # Save updated state
    print(f"Saving updated state to {STATE_PATH} ...")
    state["starred_users"] = starred_users
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Updated state written to {STATE_PATH}")

    print("=== GitGrowBot autostarback.py finished ===")

if __name__ == "__main__":
    main()
