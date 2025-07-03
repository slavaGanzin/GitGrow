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
    print("==== [START] autostarback.py ====")
    print(f"ENV: TOKEN={'SET' if TOKEN else 'UNSET'} BOT_USER={BOT_USER}")

    # Always refresh state file before proceeding
    try:
        print("[autostarback] Launching autotrack.py to refresh state ...")
        res = subprocess.run(
            [sys.executable, "scripts/autotrack.py"],
            check=True,
            env={**os.environ, "PAT_TOKEN": TOKEN, "BOT_USER": BOT_USER or ""}
        )
        print(f"[autostarback] autotrack.py finished with return code: {res.returncode}")
    except Exception as e:
        print(f"[autostarback] ERROR: Failed to run autotrack.py: {e}", file=sys.stderr)
        sys.exit(1)

    print("[autostarback] Checking critical environment variables ...")
    if not TOKEN or not BOT_USER:
        print("[autostarback] ERROR: PAT_TOKEN and BOT_USER required.", file=sys.stderr)
        sys.exit(1)
    if not STATE_PATH.exists():
        print(f"[autostarback] ERROR: {STATE_PATH} not found.", file=sys.stderr)
        sys.exit(1)
    print("[autostarback] State file found.")

    print(f"[autostarback] Loading state file: {STATE_PATH}")
    with open(STATE_PATH) as f:
        state = json.load(f)

    current_stargazers = set(state.get("current_stargazers", []))
    reciprocity = state.get("reciprocity", {})
    now = datetime.now(timezone.utc).isoformat()

    print("[autostarback] Authenticating with GitHub ...")
    gh = Github(TOKEN)
    me = gh.get_user(BOT_USER)
    print(f"[autostarback] Authenticated as: {me.login}")

    print("[autostarback] Starting star-back reconciliation loop over all current stargazers ...")
    for user_idx, user in enumerate(current_stargazers, 1):
        if user not in reciprocity:
            continue
        starred_by = reciprocity[user]["starred_by"]
        starred_back = reciprocity[user]["starred_back"]
        print(f"\n[autostarback] Processing user [{user_idx}/{len(current_stargazers)}]: {user}")
        print(f"    starred_by={len(starred_by)} starred_back={len(starred_back)}")
        try:
            u = gh.get_user(user)
            # Candidate repos to (star/unstar), always work on first 5 (as in autotrack)
            user_repos = [r for r in u.get_repos() if not r.fork and not r.private][:5]
            # For easy lookup
            user_repo_names = [r.full_name for r in user_repos]

            # Star more of their repos if needed
            while len(starred_back) < len(starred_by) and len(user_repos) > len(starred_back):
                repo = user_repos[len(starred_back)]
                print(f"[autostarback] Starring {repo.full_name} for {user} (to match count)")
                try:
                    me.add_to_starred(repo)
                    starred_back.append(repo.full_name)
                except Exception as err:
                    print(f"[autostarback] ERROR: Failed to star {repo.full_name} for {user}: {err}")

            # Unstar extra repos if needed
            while len(starred_back) > len(starred_by):
                repo_name = starred_back[-1]
                print(f"[autostarback] Unstarring {repo_name} for {user} (to match count)")
                try:
                    repo = gh.get_repo(repo_name)
                    me.remove_from_starred(repo)
                    starred_back.pop()
                except Exception as err:
                    print(f"[autostarback] ERROR: Failed to unstar {repo_name} for {user}: {err}")

            print(f"[autostarback] Final: {user}: user_starred_yours={len(starred_by)}, you_starred_theirs={len(starred_back)}")

            # Save changes to state (they will be refreshed on next autotrack anyway)
            reciprocity[user]["starred_back"] = starred_back

        except Exception as e:
            print(f"[autostarback] ERROR processing {user}: {e}")

    # Write updated state (reciprocity only; autotrack will always overwrite on next run)
    state["reciprocity"] = reciprocity
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print("[autostarback] State updated and saved to disk.")

    print("==== [END] autostarback.py ====")

if __name__ == "__main__":
    main()
