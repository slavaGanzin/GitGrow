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
DAYS_UNTIL_UNSTAR = 4  # Timeout for growth stars

def main():
    print("=== GitGrowBot autounstarback.py started ===")
    if not TOKEN:
        print("ERROR: PAT_TOKEN required.", file=sys.stderr)
        sys.exit(1)
    if not STATE_PATH.exists():
        print(f"ERROR: {STATE_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    gh = Github(TOKEN)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    with open(STATE_PATH) as f:
        state = json.load(f)

    current_stargazers = set(state.get("current_stargazers", []))
    growth_starred = state.get("growth_starred", {})
    reciprocity = state.get("reciprocity", {})
    unresponsive = state.get("unresponsive", {})

    changed = False

    # 1. GROWTH USERS: unstar after timeout if no reciprocation, move to unresponsive with timestamp
    for user in list(growth_starred.keys()):
        # If user is still a stargazer, skip (wait for reciprocation)
        if user in current_stargazers:
            continue
        for entry in list(growth_starred[user]):
            repo_name = entry["repo"]
            starred_at = entry.get("starred_at")
            do_unstar = False
            if not starred_at:
                do_unstar = True  # legacy entries
            else:
                try:
                    starred_dt = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
                    if now - starred_dt > timedelta(days=DAYS_UNTIL_UNSTAR):
                        do_unstar = True
                except Exception:
                    do_unstar = True  # treat bad timestamp as expired

            if do_unstar:
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                    print(f"[growth timeout] Unstarred {repo_name} for {user} (no reciprocation)")
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                # Log to unresponsive with timestamp
                entry["unstarred_at"] = now_iso
                unresponsive.setdefault(user, []).append(entry)
                growth_starred[user].remove(entry)
                changed = True

        # Clean up empty users
        if not growth_starred[user]:
            del growth_starred[user]

    # 2. RECIPROCITY: Keep starred_back <= starred_by
    for user, rec in reciprocity.items():
        starred_by = rec.get("starred_by", [])
        starred_back = rec.get("starred_back", [])
        excess = len(starred_back) - len(starred_by)
        # Only unstar if excess stars
        if excess > 0:
            for i in range(excess):
                repo_name = starred_back.pop()
                try:
                    repo = gh.get_repo(repo_name)
                    gh.get_user().remove_from_starred(repo)
                    print(f"[over-recip] Unstarred {repo_name} for {user}")
                except Exception as e:
                    print(f"  Warning: could not unstar {repo_name}: {e}")
                changed = True
            rec["starred_back"] = starred_back
            rec["last_reciprocity_update"] = now_iso

        # If cannot achieve parity due to lack of repos, record timestamp
        if len(starred_by) > len(starred_back):
            # User may not have enough public repos to restore balance
            rec["last_unbalanced_attempt"] = now_iso
            changed = True

    # Save JSON if changed
    if changed:
        state["growth_starred"] = growth_starred
        state["unresponsive"] = unresponsive
        state["reciprocity"] = reciprocity
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print("Updated state written to", STATE_PATH)
    else:
        print("No changes to state.")

    print("=== GitGrowBot autounstarback.py finished ===")

if __name__ == "__main__":
    main()
