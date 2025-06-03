#!/usr/bin/env python3

import os
import json
from pathlib import Path
from github import Github
import requests

# Configuration from environment variables
DISCUSSION_NUMBER = int(os.environ["WELCOME_DISCUSSION_ID"])  # Discussion forum ID
TOKEN = os.environ["GITHUB_TOKEN"]  # Personal Access Token for API access
REPO = os.environ["GITHUB_REPOSITORY"]  # Current repository in 'owner/repo' format
STATE_FILE = Path(".github/state/stars.json")  # Persistence file path
HEADERS = {"Authorization": f"token {TOKEN}"}  # API request headers

# 1. Load previous state from JSON file
if STATE_FILE.exists():
    with open(STATE_FILE, "r") as f:
        previous_stars = set(json.load(f))  # Load as set for easy diffing
else:
    previous_stars = set()  # Initialize empty set for first run

# 2. Fetch current stargazers (paginated)
def get_stargazers():
    stargazers = set()
    page = 1
    while True:
        # Paginated API request (GitHub returns 100 results/page max)
        url = f"https://api.github.com/repos/{REPO}/stargazers?per_page=100&page={page}"
        resp = requests.get(url, headers=HEADERS)
        data = resp.json()
        
        # Break loop if empty response or unexpected data format
        if not data or "login" not in str(data):
            break
            
        stargazers |= {user["login"] for user in data}  # Add logins to set
        
        # Exit loop if fewer than 100 results (no more pages)
        if len(data) < 100:
            break
        page += 1
    return stargazers

current_stars = get_stargazers()

# 3. Detect changes using set operations
new_stars = current_stars - previous_stars  # Users who starred since last run
lost_stars = previous_stars - current_stars  # Users who removed their star

# 4. Post comments (REST API)
def post_discussion_comment(body):
    """Post formatted message to GitHub discussion thread"""
    url = f"https://api.github.com/repos/{REPO}/discussions/{DISCUSSION_NUMBER}/comments"
    resp = requests.post(url, headers=HEADERS, json={"body": body})
    resp.raise_for_status()  # Raise exception for HTTP errors

# Generate and post welcome message for new stargazers
if new_stars:
    body = (
        "✨ **New stargazer(s):**\n"
        + "\n".join(f"- @{u}" for u in sorted(new_stars))
        + "\nWelcome aboard!"
    )
    post_discussion_comment(body)

# Generate and post farewell message for lost stargazers

if lost_stars:
    body = (
        "👋 **Departed stargazer(s):**\n"
        + "\n".join(f"- @{u}" for u in sorted(lost_stars))
        + "\nSad to see you go."
    )
    post_discussion_comment(body)

# 5. Save new state persistently
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)  # Create state directory if missing
with open(STATE_FILE, "w") as f:
    json.dump(sorted(current_stars), f, indent=2)  # Save sorted list for readability
