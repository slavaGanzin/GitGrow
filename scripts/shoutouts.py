#!/usr/bin/env python3
import os, json
from pathlib import Path
import requests
from github import Github

# ─── Config ───────────────────────────────────────────────────────────────────
DISCUSSION_NUMBER = int(os.environ["WELCOME_DISCUSSION_ID"])
TOKEN             = os.environ["PAT_TOKEN"]
REPO              = os.environ["GITHUB_REPOSITORY"]
owner, repo_name  = REPO.split("/")
STATE_FILE        = Path(".github/state/stars.json")
GRAPHQL_URL       = "https://api.github.com/graphql"

# ─── GitHub client ────────────────────────────────────────────────────────────
gh   = Github(TOKEN)
repo = gh.get_repo(REPO)

# ─── 1. Load previous state ────────────────────────────────────────────────────
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
seen = set(json.loads(STATE_FILE.read_text())["stars"]) if STATE_FILE.exists() else set()

# ─── 2. Fetch stargazers & diff ───────────────────────────────────────────────
current   = {u.login.lower() for u in repo.get_stargazers()}
new_stars = sorted(current - seen)
un_stars  = sorted(seen    - current)

# ─── GraphQL helpers ───────────────────────────────────────────────────────────
def graphql(query: str, variables: dict):
    resp = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Accept":        "application/vnd.github.v3+json",
        },
        json={"query": query, "variables": variables},
    )
    resp.raise_for_status()
    return resp.json()

def get_discussion_node_id():
    q = """
    query($owner:String!,$name:String!,$number:Int!) {
      repository(owner:$owner,name:$name) {
        discussion(number:$number) { id }
      }
    }
    """
    v = {"owner": owner, "name": repo_name, "number": DISCUSSION_NUMBER}
    data = graphql(q, v)
    return data["data"]["repository"]["discussion"]["id"]

DISCUSSION_NODE_ID = get_discussion_node_id()

def post(msg: str):
    m = """
    mutation($input:AddDiscussionCommentInput!) {
      addDiscussionComment(input:$input) {
        comment { id }
      }
    }
    """
    v = {"input": {"subjectId": DISCUSSION_NODE_ID, "body": msg}}
    graphql(m, v)

# ─── 3. Post your original messages ────────────────────────────────────────────
if new_stars:
    msg = (
        "🎉 **A sky full of new stars!** 🌟 Welcome aboard: "
        + ", ".join(f"@{u}" for u in new_stars)
        + "\n\n"
        "> _'Cause you're a sky, you're a sky full of stars_\n"
        "> _I'm gonna give you my heart..._\n\n"
        "You've been added to `usernames.txt`. Glad to have you here!"
    )
    post(msg)

if un_stars:
    msg = (
        "👋 **Oh no, stars fading away...** We'll miss you: "
        + ", ".join(f"@{u}" for u in un_stars)
        + "\n\n"
        "> _I don't care, go on and tear me apart_\n"
        "> _I don't care if you do_\n"
        "> _'Cause in a sky, 'cause in a sky full of stars_\n"
        "> _I think I saw you..._\n\n"
        "We've removed you from the list, but you're always welcome back!"
    )
    post(msg)

# ─── 4. Save updated state ────────────────────────────────────────────────────
STATE_FILE.write_text(json.dumps({"stars": sorted(current)}))
print("Shout-out run complete.")
