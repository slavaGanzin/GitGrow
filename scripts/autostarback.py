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
    print(f"[autostarback] current_stargazers: {len(current_stargazers)} loaded")
    mutual_stars = state.get("mutual_stars", {})
    print(f"[autostarback] mutual_stars: {len(mutual_stars)} loaded")
    now = datetime.now(timezone.utc).isoformat()

    print("[autostarback] Authenticating with GitHub ...")
    gh = Github(TOKEN)
    me = gh.get_user(BOT_USER)
    print(f"[autostarback] Authenticated as: {me.login}")

    print("[autostarback] Fetching your repos ...")
    my_repos = {repo.full_name for repo in me.get_repos()}
    print(f"[autostarback] You own {len(my_repos)} repos.")

    print("[autostarback] Starting star-back loop over all current stargazers ...")
    for user_idx, user in enumerate(current_stargazers, 1):
        print(f"\n[autostarback] Processing user [{user_idx}/{len(current_stargazers)}]: {user}")
        try:
            u = gh.get_user(user)
            print(f"[autostarback] Got user object for {user}")

            # How many of my repos has this user starred?
            user_star_count = 0
            for repo_idx, repo in enumerate(my_repos, 1):
                print(f"    [repo-check] ({repo_idx}/{len(my_repos)}) Checking {repo} ...")
                repo_obj = gh.get_repo(repo)
                for sg in repo_obj.get_stargazers():
                    if sg.login == user:
                        user_star_count += 1
                        print(f"      [repo-check] {user} has starred {repo}")
                        break
            print(f"[autostarback] {user} has starred {user_star_count} of your repos.")

            # How many of their repos have you starred?
            your_stars = mutual_stars.get(user, [])
            if your_stars and isinstance(your_stars[0], dict):
                your_stars = [d['repo'] for d in your_stars]
            your_star_count = len(your_stars)
            print(f"[autostarback] You have starred {your_star_count} of {user}'s repos.")

            # Get candidate repos to star for this user (first 5 for efficiency)
            print(f"[autostarback] Fetching {user}'s repos ...")
            user_repos = [r for r in u.get_repos() if not r.fork and not r.private][:5]
            print(f"[autostarback] {user} has {len(user_repos)} candidate repos for reciprocity.")

            # Star/unstar as needed to match counts
            while your_star_count < user_star_count and len(user_repos) > your_star_count:
                repo = user_repos[your_star_count]
                print(f"[autostarback] Starring {repo.full_name} for {user} (to match count)")
                me.add_to_starred(repo)
                mutual_stars.setdefault(user, [])
                mutual_stars[user].append({
                    "repo": repo.full_name,
                    "starred_at": now
                })
                your_star_count += 1

            while your_star_count > user_star_count and your_star_count > 0:
                repo_name = your_stars[-1]
                print(f"[autostarback] Unstarring {repo_name} for {user} (to match count)")
                repo = gh.get_repo(repo_name)
                me.remove_from_starred(repo)
                mutual_stars[user].pop()
                your_star_count -= 1

            print(f"[autostarback] Final: {user}: user_starred_yours={user_star_count}, you_starred_theirs={your_star_count}")

        except Exception as e:
            print(f"[autostarback] ERROR processing {user}: {e}")

    # Update state
    print("[autostarback] Writing updated mutual_stars to state file ...")
    state["mutual_stars"] = mutual_stars
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    print("[autostarback] State updated and saved to disk.")

    print("==== [END] autostarback.py ====")

if __name__ == "__main__":
    main()
