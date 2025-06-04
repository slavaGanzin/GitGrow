#!/usr/bin/env python3
import os
import sys
import random
from pathlib import Path
from github import Github, GithubException
from datetime import datetime, timedelta, timezone

def main():
    # — Auth & client setup —
    token = os.getenv("PAT_TOKEN")  # Retrieve GitHub token from environment variables
    if not token:
        sys.exit("PAT_TOKEN environment variable is required")  # Exit if token is not found
    gh = Github(token)  # Initialize GitHub client
    me = gh.get_user()  # Get authenticated user

    # — Determine repo root & config paths —
    base_dir  = Path(__file__).parent.parent.resolve()  # Determine base directory of the repository
    user_path = base_dir / "config" / "usernames.txt"  # Path to the usernames configuration file
    white_path= base_dir / "config" / "whitelist.txt"  # Path to the whitelist configuration file
    per_run = int(os.getenv("FOLLOWERS_PER_RUN", 100))  # Number of users to follow per run, set by workflow .yml file with a fallback default value of 100

    # — Load whitelist —
    if white_path.exists():
        with white_path.open() as f:
            whitelist = {ln.strip().lower() for ln in f if ln.strip()}  # Load whitelist from file
    else:
        print(f"[WARN] config/whitelist.txt not found, proceeding with empty whitelist")
        whitelist = set()  # Initialize empty whitelist if file is not found

    # — Load candidate usernames —
    if not user_path.exists():
        sys.exit(f"Username file not found: {user_path}")  # Exit if usernames file is not found
    with user_path.open() as f:
        candidates = [ln.strip() for ln in f if ln.strip()]  # Load candidate usernames from file

    # — Fetch current following list once —
    try:
        following = {u.login.lower(): u for u in me.get_following()}  # Fetch list of users the authenticated user is following
    except GithubException as e:
        sys.exit(f"[ERROR] fetching following list: {e}")  # Exit if there is an error fetching the following list

    # --- STEP 2: Follow up to per_run new users ---
    random.shuffle(candidates)  # Shuffle candidate usernames
    new_followed = 0  # Counter for new followed users
    notfound_new = []  # List to store usernames not found
    private_new  = []  # List to store private/inaccessible usernames

    for login in candidates:
        if new_followed >= per_run:
            break  # Stop if the limit of new followed users is reached

        ll = login.lower()
        if ll == me.login.lower() or ll in whitelist or ll in following:
            continue  # Skip if the username is the authenticated user, in the whitelist, or already followed

        # — existence check —
        try:
            user = gh.get_user(login)  # Check if the user exists
        except GithubException as e:
            if getattr(e, "status", None) == 404:
                notfound_new.append(login)
                print(f"[SKIP] {login} not found")
            else:
                private_new.append(login)
                print(f"[PRIVATE] {login} inaccessible: {e}")
            continue

        # — activity filter (last 3 days) —
        try:
            events = user.get_events()
            last_event = next(iter(events), None)  # PaginatedList to iterator
            if not last_event or last_event.created_at < datetime.now(timezone.utc) - timedelta(days=3): #UTC conversion 
                print(f"[SKIP] {login} inactive (last event: {last_event.created_at if last_event else 'none'})")
                continue
        except GithubException as e:
            print(f"[WARN] could not fetch events for {login}, skipping: {e}")
            continue

        # attempt follow
        try:
            me.add_to_following(user)  # Attempt to follow the user
            new_followed += 1
            print(f"[FOLLOWED] {login} ({new_followed}/{per_run})")  # Print success message
        except GithubException as e:
            if getattr(e, "status", None) == 403:
                private_new.append(login)
                print(f"[PRIVATE] cannot follow {login}: {e}")  # Print error message if the user cannot be followed
            else:
                print(f"[ERROR] follow {login}: {e}")  # Print other errors

    print(f"Done follow phase: {new_followed}/{per_run} followed.")  # Print summary of follow phase
    if notfound_new:
        print("Not found (skipped) during follow phase:", notfound_new)  # Print list of not found users
    if private_new:
        print("Private/inaccessible (skipped) during follow phase:", private_new)  # Print list of private/inaccessible users

    # --- STEP 3: Follow-back your followers ---
    try:
        followers_map = {u.login.lower(): u for u in me.get_followers()}  # Fetch list of users following the authenticated user
    except GithubException as e:
        sys.exit(f"[ERROR] fetching followers list: {e}")  # Exit if there is an error fetching the followers list

    back_count  = 0  # Counter for follow-back users
    private_back = []  # List to store private/inaccessible follow-back users

    for login, user in followers_map.items():
        ll = login.lower()
        if ll == me.login.lower() or ll in whitelist or ll in following:
            continue  # Skip if the username is the authenticated user, in the whitelist, or already followed
        try:
            me.add_to_following(user)  # Attempt to follow-back the user
            back_count += 1
            print(f"[FOLLOW-BACKED] {login}")  # Print success message
        except GithubException as e:
            if getattr(e, "status", None) == 403:
                private_back.append(login)
                print(f"[PRIVATE] cannot follow-back {login}: {e}")  # Print error message if the user cannot be followed-back
            else:
                print(f"[ERROR] follow-back {login}: {e}")  # Print other errors

    print(f"Done follow-back phase: {back_count} followed-back.")  # Print summary of follow-back phase
    if private_back:
        print("Private/inaccessible skipped during follow-back:", private_back)  # Print list of private/inaccessible follow-back users


if __name__ == "__main__":
    main()
