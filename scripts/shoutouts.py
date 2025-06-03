#!/usr/bin/env python3

import os
import json
from pathlib import Path

STATE_FILE = Path(".github/state/stars.json")
OUTPUT_DIR = Path(".github/state")
WELCOME_FILE = OUTPUT_DIR / "welcome_comments.md"
FAREWELL_FILE = OUTPUT_DIR / "farewell_comments.md"
REPO = os.environ["GITHUB_REPOSITORY"]
HEADERS = {"Accept": "application/vnd.github+json"}

import requests

def get_stargazers():
    stargazers = set()
    page = 1
    while True:
        url = f"https://api.github.com/repos/{REPO}/stargazers?per_page=100&page={page}"
        resp = requests.get(url, headers=HEADERS)
        data = resp.json()
        if not isinstance(data, list) or not data:
            break
        stargazers |= {user["login"] for user in data}
        if len(data) < 100:
            break
        page += 1
    return stargazers

# Load previous state
if STATE_FILE.exists():
    with open(STATE_FILE, "r") as f:
        previous_stars = set(json.load(f))
else:
    previous_stars = set()

# Fetch current stargazers
current_stars = get_stargazers()

# Detect changes
new_stars = current_stars - previous_stars
lost_stars = previous_stars - current_stars

# Output messages
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if new_stars:
    welcome_msg = (
        "# 🌟 **New stargazers detected!**\n"
        "Welcome aboard and thank you for your interest: "
        + ", ".join(f"@{u}" for u in sorted(new_stars))
        + "\n\n"
        "You've been added to the active users follow list. Glad to have you here!\n\n"
        "> *L'amitié naît d'une mutuelle estime et s'entretient moins par les bienfaits que par l'honnêteté.*\n"
        "> — Étienne de La Boétie"
    )
    with open(WELCOME_FILE, "w") as f:
        f.write(welcome_msg)
else:
    WELCOME_FILE.unlink(missing_ok=True)

if lost_stars:
    farewell_msg = (
        "# 💔 **Oh no, stars fading away...**\n"
        + ", ".join(f"@{u}" for u in sorted(lost_stars))
        + " unstarred GitGrowBot.\n\n"
        "Your support was appreciated. We've removed you from the users follow list, but you're welcome back anytime.\n\n"
        "> *Rien ne se perd, rien ne se crée, tout se transforme.*\n"
        "> — Antoine Lavoisier"
    )
    with open(FAREWELL_FILE, "w") as f:
        f.write(farewell_msg)
else:
    FAREWELL_FILE.unlink(missing_ok=True)

# Save new state
with open(STATE_FILE, "w") as f:
    json.dump(sorted(current_stars), f, indent=2)
