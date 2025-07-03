#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from github import Github
from datetime import datetime, timedelta, timezone

TOKEN = os.getenv("PAT_TOKEN")
BOT_USER = os.getenv("BOT_USER")
STATE_PATH = Path(".github/state/stargazer_state.json")
DAYS_UNTIL_UNSTAR = 4  # Days to wait for reciprocation

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
    growth_starred = state.get("growth_starred", {})
    reciprocity = state.get("reciprocity", {})
    unresponsive = state.get("unresponsive", {})

    now = datetime.now(timezone.utc)
    changed = False

    # Pass 1: users who are still stargazers (only fix over-reciprocity)
    for user in list(growth_starred.keys()):
        if user in current_stargazers:
            starred_back = reciprocity.get(user, {}).get("starred_back", [])
            starred_by = reciprocity.get(user, {}).get("starred_by", [])
            # Only trim over-reciprocation (starred_back > starred_by)
            while len(starred_back) > len(starred_by):
                repo_name = starred_back[-1]
                print(f"[over-recip] Unstarring {repo_name} for {user} (over-reciprocated: you starred more of their repos than they of yours)")
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                starred_back.pop()
                # Remove from growth_starred too if present
                entries = growth_starred.get(user, [])
                growth_starred[user] = [e for e in entries if e.get("repo") != repo_name]
                changed = True
            reciprocity[user]["starred_back"] = starred_back
            # Clean up growth_starred[user] if empty
            if user in growth_starred and not growth_starred[user]:
                del growth_starred[user]

    # Pass 2: users no longer stargazers (enforce unstar by timestamp)
    for user in list(growth_starred.keys()):
        if user in current_stargazers:
            continue  # Already handled above
        for entry in list(growth_starred[user]):
            repo_name = entry["repo"]
            starred_at = entry.get("starred_at")
            unstar_this = False
            if not starred_at:
                print(f"[legacy] Unstarring {repo_name} for {user} (no timestamp, user not in current_stargazers)")
                unstar_this = True
            else:
                try:
                    starred_dt = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
                    if now - starred_dt > timedelta(days=DAYS_UNTIL_UNSTAR):
                        print(f"[timeout] Unstarring {repo_name} for {user} (not reciprocated after {DAYS_UNTIL_UNSTAR} days)")
                        unstar_this = True
                except Exception:
                    print(f"[invalid-ts] Unstarring {repo_name} for {user} (invalid timestamp)")
                    unstar_this = True

            if unstar_this:
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                unresponsive.setdefault(user, []).append(entry)
                growth_starred[user].remove(entry)
                changed = True

        # Clean up
        if user in growth_starred and not growth_starred[user]:
            del growth_starred[user]

    # Write updated state
    state["growth_starred"] = growth_starred
    state["unresponsive"] = unresponsive
    state["reciprocity"] = reciprocity

    if changed:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print("Updated state written to", STATE_PATH)
    else:
        print("No changes to state.")

    print("=== GitGrowBot autounstarback.py finished ===")

if __name__ == "__main__":
    main()
