#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from github import Github
from datetime import datetime, timezone

TOKEN = os.getenv("PAT_TOKEN")
BOT_USER = os.getenv("BOT_USER")
STATE_PATH = Path(".github/state/stargazer_state.json")

def main():
    print("==== [START] autostarback.py ====")
    print(f"ENV: TOKEN={'SET' if TOKEN else 'UNSET'} BOT_USER={BOT_USER}")

    if not TOKEN or not BOT_USER:
        print("[autostarback] ERROR: PAT_TOKEN and BOT_USER required.", file=sys.stderr)
        sys.exit(1)
    if not STATE_PATH.exists():
        print(f"[autostarback] ERROR: {STATE_PATH} not found.", file=sys.stderr)
        sys.exit(1)
    print("[autostarback] State file found.")

    with open(STATE_PATH) as f:
        state = json.load(f)

    current_stargazers = set(state.get("current_stargazers", []))
    reciprocity = state.get("reciprocity", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    changed = False

    print("[autostarback] Authenticating with GitHub ...")
    gh = Github(TOKEN)
    me = gh.get_user(BOT_USER)
    print(f"[autostarback] Authenticated as: {me.login}")

    print("[autostarback] Starting star-back reconciliation loop over all current stargazers ...")
    for user_idx, user in enumerate(current_stargargazers, 1):
        if user not in reciprocity:
            continue

        starred_by = reciprocity[user]["starred_by"]
        starred_back = reciprocity[user].get("starred_back", [])
        needed = len(starred_by)
        current = len(starred_back)

        print(f"\n[autostarback] Processing user [{user_idx}/{len(current_stargazers)}]: {user}")
        print(f"    starred_by={needed} starred_back={current}")

        try:
            u = gh.get_user(user)
            user_repos = []
            for r in u.get_repos():
                if r.fork or r.private:
                    continue
                user_repos.append(r)
                if len(user_repos) == needed:
                    break
            user_repo_names = [r.full_name for r in user_repos]
            max_possible = len(user_repo_names)

            # If all possible repos are already starred, but still unbalanced, log the attempt with timestamp
            if needed > max_possible and current >= max_possible:
                print(f"[autostarback] Cannot match reciprocity for {user} (starred_by={needed}, user has only {max_possible} repos). Logging unbalanced attempt.")
                reciprocity[user]["last_unbalanced_attempt"] = now_iso
                changed = True
                continue

            # Star more of their repos if needed, up to the max possible
            while len(starred_back) < needed and len(user_repo_names) > len(starred_back):
                repo_name = user_repo_names[len(starred_back)]
                print(f"[autostarback] Starring {repo_name} for {user} (to match count)")
                try:
                    repo = gh.get_repo(repo_name)
                    me.add_to_starred(repo)
                    starred_back.append(repo_name)
                    changed = True
                except Exception as err:
                    print(f"[autostarback] ERROR: Failed to star {repo_name} for {user}: {err}")
                    break

            print(f"[autostarback] Final: {user}: user_starred_yours={needed}, you_starred_theirs={len(starred_back)}")
            reciprocity[user]["starred_back"] = starred_back

        except Exception as e:
            print(f"[autostarback] ERROR processing {user}: {e}")

    # Write updated state (reciprocity only; autotrack will always overwrite on next run)
    if changed:
        state["reciprocity"] = reciprocity
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        print("[autostarback] State updated and saved to disk.")
    else:
        print("[autostarback] No changes to state.")

    print("==== [END] autostarback.py ====")

if __name__ == "__main__":
    main()
