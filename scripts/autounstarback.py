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
    growth_starred = state.get("growth_starred", {})
    unresponsive = state.get("unresponsive", {})
    mutual_stars = state.get("mutual_stars", {})  # <-- Add this line if not present

    now = datetime.now(timezone.utc)
    changed = False

    for user, actions in list(growth_starred.items()):
        for entry in list(actions):
            repo_name = entry["repo"]
            starred_at = entry.get("starred_at")
            if user in current_stargazers:
                continue  # Reciprocated, so we skip

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
                    unresponsive.setdefault(user, [])
                    unresponsive[user].append(entry)
                    growth_starred[user].remove(entry)
                    # --- CLEANUP: remove from mutual_stars as well
                    if user in mutual_stars:
                        del mutual_stars[user]
                    changed = True
            else:
                # No timestamp: unstar and remove, do NOT add to unresponsive
                print(f"Unstarring {repo_name} for {user} (no timestamp, assumed legacy entry).")
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                growth_starred[user].remove(entry)
                # --- CLEANUP: remove from mutual_stars as well (legacy)
                if user in mutual_stars:
                    del mutual_stars[user]
                changed = True

        # Clean up if user has no more starred repos
        if user in growth_starred and not growth_starred[user]:
            del growth_starred[user]

    state["growth_starred"] = growth_starred
    state["unresponsive"] = unresponsive
    state["mutual_stars"] = mutual_stars  # <-- Ensure this updated

    if changed:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print(f"Updated state written to {STATE_PATH}")
    else:
        print("No changes to state.")

    print("=== GitGrowBot autounstarback.py finished ===")

if __name__ == "__main__":
    main()
