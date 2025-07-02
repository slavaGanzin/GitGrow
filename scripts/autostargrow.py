#!/usr/bin/env python3

import os
import sys
import json
import random
from pathlib import Path
from github import Github
from datetime import datetime, timezone

BOT_USER = os.getenv("BOT_USER")
TOKEN = os.getenv("PAT_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")
USERNAMES_PATH = Path("config/usernames.txt")
GROWTH_SAMPLE = 10  # Number of new growth users to process per run

def main():
    print("=== GitGrowBot autostargrow.py started ===")

    if not TOKEN or not BOT_USER:
        print("ERROR: PAT_TOKEN and BOT_USER required", file=sys.stderr)
        sys.exit(1)
    print(f"PAT_TOKEN and BOT_USER env vars present.")
    print(f"BOT_USER: {BOT_USER}")

    if not USERNAMES_PATH.exists():
        print(f"ERROR: {USERNAMES_PATH} not found; cannot perform growth starring.", file=sys.stderr)
        sys.exit(1)

    print("Authenticating with GitHub...")
    gh = Github(TOKEN)
    try:
        me = gh.get_user()
        print(f"Authenticated as: {me.login}")
    except Exception as e:
        print("ERROR: Could not authenticate with GitHub:", e)
        sys.exit(1)

    # Load previous growth_starred users from state file if available
    if STATE_PATH.exists():
        print(f"Loading state from {STATE_PATH} ...")
        with open(STATE_PATH) as f:
            state = json.load(f)
        growth_starred = state.get("growth_starred", {})
    else:
        print("No existing stargazer state found; starting fresh.")
        growth_starred = {}

    # Load candidate usernames for growth
    with open(USERNAMES_PATH) as f:
        all_usernames = [line.strip() for line in f if line.strip()]
    print(f"  Loaded {len(all_usernames)} usernames from {USERNAMES_PATH}")

    # Exclude already starred users
    available = set(all_usernames) - set(growth_starred)
    print(f"  {len(available)} candidates for growth starring.")
    sample = random.sample(list(available), min(GROWTH_SAMPLE, len(available)))

    now_iso = datetime.now(timezone.utc).isoformat()

    for i, user in enumerate(sample):
        print(f"  [{i+1}/{len(sample)}] Growth star for user: {user}")
        try:
            u = gh.get_user(user)
            repos = []
            for repo in u.get_repos():
                if not repo.fork and not repo.private:
                    repos.append(repo)
                if len(repos) >= 3:
                    break
            if not repos:
                print(f"    No public repos to star for {user}, skipping.")
                continue
            repo = random.choice(repos)
            print(f"    Starring repo: {repo.full_name}")
            me.add_to_starred(repo)
            growth_starred.setdefault(user, [])
            growth_starred[user].append({
                "repo": repo.full_name,
                "starred_at": now_iso
            })
            print(f"    Growth: Starred {repo.full_name} for {user} at {now_iso}")
        except Exception as e:
            print(f"    Failed to star for growth {user}: {e}")

    # Save updated growth_starred to state file
    print(f"Saving updated growth_starred to {STATE_PATH} ...")
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            state = json.load(f)
    else:
        state = {}
    state["growth_starred"] = growth_starred
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Updated growth_starred written to {STATE_PATH}")

    print("=== GitGrowBot autostargrow.py finished ===")

if __name__ == "__main__":
    main()
