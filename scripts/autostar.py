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
GROWTH_SAMPLE = 5

def main():
    print("=== GitGrowBot autostar.py started ===")

    if not TOKEN or not BOT_USER:
        print("ERROR: GITHUB_TOKEN and BOT_USER required", file=sys.stderr)
        sys.exit(1)
    print(f"GITHUB_TOKEN and BOT_USER env vars present.")
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
    unstargazers = set(state.get("unstargazers", []))
    print(f"Loaded {len(current_stargazers)} stargazers, {len(starred_users)} starred_users, {len(unstargazers)} unstargazers.")

    # 1. Star new stargazers
    print(f"== Star new stargazers: {len(current_stargazers)} to check ==")
    new_to_star = [u for u in current_stargazers if u not in starred_users]
    print(f"Found {len(new_to_star)} new users to star.")
    for i, user in enumerate(new_to_star):
        print(f"  [{i+1}/{len(new_to_star)}] Processing user: {user}")
        try:
            u = gh.get_user(user)
            repos = [r for r in u.get_repos() if not r.fork and not r.private]
            print(f"    Found {len(repos)} public non-fork repos for {user}")
            if not repos:
                print(f"    No public repos to star for {user}, skipping.")
                continue
            repo = random.choice(repos)
            print(f"    Starring repo: {repo.full_name}")
            me.add_to_starred(repo)
            starred_users[user] = [repo.full_name]
            print(f"    Starred {repo.full_name} for {user}")
        except Exception as e:
            print(f"    Failed to star for {user}: {e}")

    # 2. Unstar repos of unstargazers
    print(f"== Unstar users who unstarred you: {len(unstargazers)} to check ==")
    for i, user in enumerate(list(unstargazers)):
        print(f"  [{i+1}/{len(unstargazers)}] Checking unstargazer: {user}")
        if user in starred_users:
            for repo_name in starred_users[user]:
                try:
                    print(f"    Unstarring repo: {repo_name}")
                    repo = gh.get_repo(repo_name)
                    me.remove_from_starred(repo)
                    print(f"    Unstarred {repo.full_name} (user {user} unstarred you)")
                except Exception as e:
                    print(f"    Failed to unstar {repo_name}: {e}")
            del starred_users[user]
        else:
            print(f"    User {user} not in starred_users, nothing to unstar.")

    # 3. Growth: star new users from usernames.txt
    if USERNAMES_PATH.exists():
        print(f"== Growth: usernames.txt found ==")
        with open(USERNAMES_PATH) as f:
            all_usernames = [line.strip() for line in f if line.strip()]
        print(f"  Loaded {len(all_usernames)} usernames from {USERNAMES_PATH}")
        available = set(all_usernames) - current_stargazers - set(starred_users)
        print(f"  {len(available)} candidates for growth starring.")
        sample = random.sample(list(available), min(GROWTH_SAMPLE, len(available)))
        for i, user in enumerate(sample):
            print(f"  [{i+1}/{len(sample)}] Growth star for user: {user}")
            try:
                u = gh.get_user(user)
                repos = [r for r in u.get_repos() if not r.fork and not r.private]
                print(f"    Found {len(repos)} public non-fork repos for {user}")
                if not repos:
                    print(f"    No public repos to star for {user}, skipping.")
                    continue
                repo = random.choice(repos)
                print(f"    Starring repo: {repo.full_name}")
                me.add_to_starred(repo)
                starred_users[user] = [repo.full_name]
                print(f"    Growth: Starred {repo.full_name} for {user}")
            except Exception as e:
                print(f"    Failed to star for growth {user}: {e}")
    else:
        print("No usernames.txt found, skipping growth stars.")

    # 4. Save updated state
    print(f"Saving updated state to {STATE_PATH} ...")
    state["starred_users"] = starred_users
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Updated state written to {STATE_PATH}")

    print("=== GitGrowBot autostar.py finished ===")

if __name__ == "__main__":
    main()
