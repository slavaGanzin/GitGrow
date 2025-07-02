#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from pathlib import Path
from github import Github
from datetime import datetime, timezone

TOKEN = os.getenv("PAT_TOKEN")
BOT_USER = os.getenv("BOT_USER")
STATE_PATH = Path(".github/state/stargazer_state.json")

def main():
    # Always refresh state file before proceeding
    try:
        print("Refreshing stargazer state with autotrack.py ...")
        subprocess.run(
            [sys.executable, "scripts/autotrack.py"],
            check=True,
            env={**os.environ, "PAT_TOKEN": TOKEN, "BOT_USER": BOT_USER or ""}
        )
    except Exception as e:
        print(f"ERROR: Failed to run autotrack.py: {e}", file=sys.stderr)
        sys.exit(1)
    if not TOKEN or not BOT_USER:
        print("ERROR: PAT_TOKEN and BOT_USER required.", file=sys.stderr)
        sys.exit(1)
    if not STATE_PATH.exists():
        print(f"ERROR: {STATE_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    with open(STATE_PATH) as f:
        state = json.load(f)

    current_stargazers = set(state.get("current_stargazers", []))
    mutual_stars = state.get("mutual_stars", {})
    now = datetime.now(timezone.utc).isoformat()

    gh = Github(TOKEN)
    me = gh.get_user(BOT_USER)
    my_repos = {repo.full_name for repo in me.get_repos()}

    for user in current_stargazers:
        try:
            u = gh.get_user(user)
            # How many of my repos has this user starred?
            user_star_count = 0
            for repo in my_repos:
                repo_obj = gh.get_repo(repo)
                if any(sg.login == user for sg in repo_obj.get_stargazers()):
                    user_star_count += 1
            print(f"{user} has starred {user_star_count} of your repos.")

            # How many of their repos have you starred?
            your_stars = mutual_stars.get(user, [])
            if your_stars and isinstance(your_stars[0], dict):
                your_stars = [d['repo'] for d in your_stars]
            your_star_count = len(your_stars)
            print(f"You have starred {your_star_count} of {user}'s repos.")

            # Get candidate repos to star for this user (first 5 for efficiency)
            user_repos = [r for r in u.get_repos() if not r.fork and not r.private][:5]

            # Star/unstar as needed to match counts
            while your_star_count < user_star_count and len(user_repos) > your_star_count:
                repo = user_repos[your_star_count]
                me.add_to_starred(repo)
                # Append new star to mutual_stars with timestamp
                mutual_stars.setdefault(user, [])
                mutual_stars[user].append({
                    "repo": repo.full_name,
                    "starred_at": now
                })
                your_star_count += 1
                print(f"Starred {repo.full_name} for {user} to match count.")

            while your_star_count > user_star_count and your_star_count > 0:
                repo_name = your_stars[-1]
                repo = gh.get_repo(repo_name)
                me.remove_from_starred(repo)
                mutual_stars[user].pop()
                your_star_count -= 1
                print(f"Unstarred {repo.full_name} for {user} to match count.")

            # Log result
            print(f"Final: {user}: user_starred_yours={user_star_count}, you_starred_theirs={your_star_count}")

        except Exception as e:
            print(f"Error processing {user}: {e}")

    # Update state
    state["mutual_stars"] = mutual_stars
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print("State updated.")

if __name__ == "__main__":
    main()
