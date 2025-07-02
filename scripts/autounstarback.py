#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from github import Github
from datetime import datetime, timedelta, timezone

TOKEN = os.getenv("PAT_TOKEN")
STATE_PATH = Path(".github/state/stargazer_state.json")
DAYS_UNTIL_UNSTAR = 4  # Unstar if not reciprocated within this period

def main():
    print("=== GitGrowBot autounstarback.py started ===")
    if not TOKEN:
        print("ERROR: PAT_TOKEN required.", file=sys.stderr)
        sys.exit(1)

    if not STATE_PATH.exists():
        print(f"ERROR: {STATE_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    gh = Github(TOKEN)
    with open(STATE_PATH) as f:
        state = json.load(f)
    current_stargazers = set(state.get("current_stargazers", []))
    starred_users = state.get("starred_users", {})
    unresponsive = state.get("unresponsive", {})

    now = datetime.now(timezone.utc)
    changed = False

    for user, starred in list(starred_users.items()):
        for repo_obj in list(starred):
            # Support both formats: dict with timestamp or legacy string
            if isinstance(repo_obj, dict):
                repo_name = repo_obj["repo"]
                starred_at = repo_obj.get("starred_at")
            else:
                repo_name = repo_obj
                starred_at = None

            if user in current_stargazers:
                continue  # Still a stargazer, do nothing

            if starred_at:
                try:
                    starred_dt = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
                except Exception:
                    print(f"  Invalid timestamp for {repo_name}, unstarring for safety.")
                    starred_dt = None

                if starred_dt and now - starred_dt > timedelta(days=DAYS_UNTIL_UNSTAR):
                    print(f"Unstarring {repo_name} for {user} (not reciprocated after {DAYS_UNTIL_UNSTAR} days).")
                    try:
                        repo = gh.get_repo(repo_name)
                        gh.get_user().remove_from_starred(repo)
                    except Exception as e:
                        print(f"  Warning: could not unstar {repo_name}: {e}")
                    if user not in unresponsive:
                        unresponsive[user] = []
                    unresponsive[user].append(repo_obj)
                    starred_users[user].remove(repo_obj)
                    changed = True
            else:
                # No timestamp: unstar and remove, do NOT add to unresponsive
                print(f"Unstarring {repo_name} for {user} (no timestamp, assumed legacy entry).")
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                starred_users[user].remove(repo_obj)
                changed = True

        # Clean up if user has no more starred repos
        if user in starred_users and not starred_users[user]:
            del starred_users[user]

    state["starred_users"] = starred_users
    state["unresponsive"] = unresponsive
    if changed:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print(f"Updated state written to {STATE_PATH}")
    else:
        print("No changes to state.")

    print("=== GitGrowBot autounstarback.py finished ===")

if __name__ == "__main__":
    main()
