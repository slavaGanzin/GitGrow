import os
import sys
import sqlite3
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from github import Github, GithubException

# --- CONFIGURATION ---
TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "")
if not TARGET_USERNAMES:
    sys.exit("TARGET_USERNAMES environment variable is required")
TARGET_USERNAMES = TARGET_USERNAMES.split(",")
FOLLOW_BATCH_SIZE = int(os.getenv("FOLLOW_BATCH_SIZE", 25))
WAIT_DAYS = int(os.getenv("WAIT_DAYS", 7))

# --- DIRECTORIES & PATHS ---
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "bot_data.db"
LOG_DIR_FOLLOW = BASE_DIR / "logs" / "follow"
LOG_DIR_STARS = BASE_DIR / "logs" / "stars"

for d in (DB_DIR, LOG_DIR_FOLLOW, LOG_DIR_STARS):
    d.mkdir(parents=True, exist_ok=True)

# --- SETUP GITHUB ---
token = os.getenv("GITHUB_TOKEN")
if not token:
    sys.exit("GITHUB_TOKEN environment variable is required")
gh = Github(token)
me = gh.get_user()

# --- TIMESTAMP & ATTEMPT ID ---
now = datetime.utcnow()
timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
existing_logs = list(LOG_DIR_FOLLOW.glob(f"{now.date()}-*followrun.log"))
attempt_id = len(existing_logs) + 1

# --- LOGGING ---
follow_log = logging.getLogger("follow")
follow_fh = logging.FileHandler(LOG_DIR_FOLLOW / f"{timestamp}-{attempt_id}-followrun.log")
follow_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
follow_log.addHandler(follow_fh)
follow_log.setLevel(logging.INFO)

star_log = logging.getLogger("stars")
star_fh = logging.FileHandler(LOG_DIR_STARS / f"{timestamp}-{attempt_id}-starrun.log")
star_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
star_log.addHandler(star_fh)
star_log.setLevel(logging.INFO)

# --- DATABASE SETUP ---
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS follows (
    username TEXT PRIMARY KEY,
    followed_at TIMESTAMP,
    status TEXT,
    original_repo_starred TEXT,
    attempt_id INTEGER
)
""")
c.execute("""CREATE TABLE IF NOT EXISTS stars (
    owner TEXT,
    repo TEXT,
    action TEXT,
    timestamp TIMESTAMP,
    attempt_id INTEGER,
    PRIMARY KEY(owner, repo, action, timestamp)
)
""")
conn.commit()

# --- HELPERS ---
def safe_api(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GithubException as e:
        message = e.data if hasattr(e, 'data') else str(e)
        follow_log.error(f"GitHub API error in {fn.__name__}: {message}")
        return None

def pick_random_repos(user, count):
    repos = safe_api(user.get_repos)
    if repos is None:
        return []
    all_repos = list(repos)
    return random.sample(all_repos, min(count, len(all_repos)))

# --- STEP 1: FOLLOW & STAR NEW BATCH ---
for target in TARGET_USERNAMES:
    user = safe_api(gh.get_user, target)
    if user is None:
        continue

    followers = safe_api(user.get_followers)
    if followers is None:
        continue
    followers_list = [f.login for f in followers[:1000]]
    batch = random.sample(followers_list, min(FOLLOW_BATCH_SIZE, len(followers_list)))

    for login in batch:
        c.execute("SELECT 1 FROM follows WHERE username=?", (login,))
        if c.fetchone():
            continue

        other_user = safe_api(gh.get_user, login)
        if other_user and safe_api(me.follow, other_user):
            follow_log.info(f"Followed {login}")
            repos = pick_random_repos(other_user, 1)
            orig_repo = None
            if repos:
                repo = repos[0]
                if safe_api(me.add_to_starred, repo):
                    star_log.info(f"Starred {login}/{repo.name}")
                    orig_repo = repo.name
                    c.execute("INSERT INTO stars VALUES (?,?,?,?,?)",
                              (login, repo.name, "starred", now, attempt_id))
            c.execute("INSERT INTO follows VALUES (?,?,?,?,?)",
                      (login, now, "pending", orig_repo, attempt_id))
            conn.commit()

# --- STEP 2: PROCESS PENDING FOLLOW-BACKS ---
cutoff = now - timedelta(days=WAIT_DAYS)
c.execute("SELECT username, original_repo_starred FROM follows WHERE followed_at<=? AND status='pending'", (cutoff,))
pending = c.fetchall()
current_followers = {f.login for f in safe_api(me.get_followers) or []}

for username, orig_repo in pending:
    user = safe_api(gh.get_user, username)
    if user is None:
        continue

    if username not in current_followers:
        if safe_api(me.unfollow, user):
            follow_log.info(f"Unfollowed {username} (no follow-back)")
            c.execute("UPDATE follows SET status='unfollowed' WHERE username=?", (username,))
    else:
        c.execute("UPDATE follows SET status='followed-back' WHERE username=?", (username,))
        # Check if they starred any of my repos
        my_repos = {r.full_name for r in safe_api(me.get_repos) or []}
        their_starred = {s.full_name for s in safe_api(user.get_starred) or []}
        if not (my_repos & their_starred):
            for r in pick_random_repos(user, 2):
                if safe_api(me.add_to_starred, r):
                    star_log.info(f"Starred {username}/{r.name}")
                    c.execute("INSERT INTO stars VALUES (?,?,?,?,?)",
                              (username, r.name, "starred", now, attempt_id))
        else:
            for r in pick_random_repos(user, 3):
                if safe_api(me.add_to_starred, r):
                    star_log.info(f"Starred {username}/{r.name}")
                    c.execute("INSERT INTO stars VALUES (?,?,?,?,?)",
                              (username, r.name, "starred", now, attempt_id))
        if orig_repo and f"{username}/{orig_repo}" not in their_starred:
            repo = safe_api(gh.get_repo, f"{username}/{orig_repo}")
            if repo and safe_api(me.remove_from_starred, repo):
                star_log.info(f"Unstarred {username}/{orig_repo} (no star-back)")
                c.execute("INSERT INTO stars VALUES (?,?,?,?,?)",
                          (username, orig_repo, "unstarred", now, attempt_id))
    conn.commit()

# --- PRUNE OLD LOGS & DB ENTRIES ---
def prune_old_logs(log_dir, days=30):
    cutoff_dt = now - timedelta(days=days)
    for f in Path(log_dir).iterdir():
        try:
            dt_str = "-".join(f.name.split("-")[:6])
            file_dt = datetime.strptime(dt_str, "%Y-%m-%d-%H-%M-%S")
            if file_dt < cutoff_dt:
                f.unlink()
        except Exception:
            continue

prune_old_logs(LOG_DIR_FOLLOW)
prune_old_logs(LOG_DIR_STARS)

threshold = now - timedelta(days=60)
c.execute("DELETE FROM follows WHERE followed_at<?", (threshold,))
c.execute("VACUUM;")
conn.commit()
conn.close()
