import os
import sys
import sqlite3
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from github import Github, GithubException

# --- CONFIGURATION ---
USERNAME_FILE        = os.getenv("USERNAME_FILE", "usernames.txt")
NUM_TARGETS          = int(os.getenv("NUM_TARGETS", 10))
FOLLOWERS_PER_TARGET = int(os.getenv("FOLLOWERS_PER_TARGET", 50))
WAIT_DAYS            = int(os.getenv("WAIT_DAYS", 7))

# --- DIRECTORIES & PATHS ---
BASE_DIR       = Path(__file__).parent
DB_DIR         = BASE_DIR / "db"
DB_PATH        = DB_DIR / "bot_data.db"
LOG_DIR_FOLLOW = BASE_DIR / "logs" / "follow"
LOG_DIR_STARS  = BASE_DIR / "logs" / "stars"
USERNAME_PATH  = BASE_DIR / USERNAME_FILE

for d in (DB_DIR, LOG_DIR_FOLLOW, LOG_DIR_STARS):
    d.mkdir(parents=True, exist_ok=True)

if not USERNAME_PATH.is_file():
    sys.exit(f"Username file not found: {USERNAME_PATH}")

with USERNAME_PATH.open() as f:
    all_usernames = [line.strip() for line in f if line.strip()]

if not all_usernames:
    sys.exit("No usernames found in file.")

targets = random.sample(all_usernames, min(NUM_TARGETS, len(all_usernames)))

# --- GITHUB SETUP ---
token = os.getenv("GITHUB_TOKEN")
if not token:
    sys.exit("GITHUB_TOKEN environment variable is required")
gh = Github(token)
me = gh.get_user()

# --- TIMESTAMP & ATTEMPT ID ---
now = datetime.utcnow()
ts = now.strftime("%Y-%m-%d-%H-%M-%S")
existing = list(LOG_DIR_FOLLOW.glob(f"{now.date()}-*followrun.log"))
attempt_id = len(existing) + 1

# --- LOGGING ---
follow_log = logging.getLogger("follow")
fh = logging.FileHandler(LOG_DIR_FOLLOW / f"{ts}-{attempt_id}-followrun.log")
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
follow_log.addHandler(fh)
follow_log.setLevel(logging.INFO)

star_log = logging.getLogger("stars")
sh = logging.FileHandler(LOG_DIR_STARS / f"{ts}-{attempt_id}-starrun.log")
sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
star_log.addHandler(sh)
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
)""")
c.execute("""CREATE TABLE IF NOT EXISTS stars (
    owner TEXT,
    repo TEXT,
    action TEXT,
    timestamp TIMESTAMP,
    attempt_id INTEGER,
    PRIMARY KEY(owner, repo, action, timestamp)
)""")
conn.commit()

# --- HELPERS ---
def safe_api(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GithubException as e:
        msg = e.data if hasattr(e, 'data') else str(e)
        follow_log.error(f"{fn.__name__} error: {msg}")
        return None

def pick_random_repos(user, count):
    repos = safe_api(user.get_repos)
    if repos is None:
        return []
    repos_list = list(repos)
    return random.sample(repos_list, min(count, len(repos_list)))

# --- STEP 1: FOLLOW & STAR NEW BATCH ---
for target in targets:
    user = safe_api(gh.get_user, target)
    if not user:
        continue

    followers = safe_api(user.get_followers)
    if not followers:
        continue
    batch = [f.login for f in followers[:FOLLOWERS_PER_TARGET]]

    for login in batch:
        c.execute("SELECT 1 FROM follows WHERE username=?", (login,))
        if c.fetchone():
            continue

        other = safe_api(gh.get_user, login)
        # use authenticated user's add_to_following() to follow
        if other and safe_api(me.add_to_following, other):
            follow_log.info(f"Followed {login}")

            repos = pick_random_repos(other, 1)
            orig = None
            if repos and safe_api(me.add_to_starred, repos[0]):
                repo = repos[0]
                star_log.info(f"Starred {login}/{repo.name}")
                orig = repo.name
                c.execute(
                    "INSERT OR IGNORE INTO stars VALUES (?,?,?,?,?)",
                    (login, repo.name, "starred", now, attempt_id)
                )

            c.execute(
                "INSERT OR IGNORE INTO follows VALUES (?,?,?,?,?)",
                (login, now, "pending", orig, attempt_id)
            )
            conn.commit()

# --- STEP 2: PROCESS PENDING FOLLOW-BACKS & STAR-BACKS ---
cutoff = now - timedelta(days=WAIT_DAYS)
c.execute(
    "SELECT username, original_repo_starred FROM follows "
    "WHERE followed_at<=? AND status='pending'",
    (cutoff,)
)
pending = c.fetchall()

current_followers = {f.login for f in safe_api(me.get_followers) or []}
my_repos = {r.full_name for r in safe_api(me.get_repos) or []}

for username, orig_repo in pending:
    user = safe_api(gh.get_user, username)
    if not user:
        continue

    if username not in current_followers:
        # use authenticated user's remove_from_following() to unfollow
        if safe_api(me.remove_from_following, user):
            follow_log.info(f"Unfollowed {username} (no follow-back)")
            c.execute(
                "UPDATE follows SET status='unfollowed' WHERE username=?",
                (username,)
            )
    else:
        c.execute(
            "UPDATE follows SET status='followed-back' WHERE username=?",
            (username,)
        )
        starred = {s.full_name for s in safe_api(user.get_starred) or []}

        # star-back logic
        star_count = 2 if not (my_repos & starred) else 3
        for r in pick_random_repos(user, star_count):
            if safe_api(me.add_to_starred, r):
                star_log.info(f"Starred {username}/{r.name}")
                c.execute(
                    "INSERT OR IGNORE INTO stars VALUES (?,?,?,?,?)",
                    (username, r.name, "starred", now, attempt_id)
                )

        # remove original star if they didn’t star back
        if orig_repo and f"{username}/{orig_repo}" not in starred:
            repo = safe_api(gh.get_repo, f"{username}/{orig_repo}")
            if repo and safe_api(me.remove_from_starred, repo):
                star_log.info(
                    f"Unstarred {username}/{orig_repo} (no star-back)"
                )
                c.execute(
                    "INSERT OR IGNORE INTO stars VALUES (?,?,?,?,?)",
                    (username, orig_repo, "unstarred", now, attempt_id)
                )
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
            pass

prune_old_logs(LOG_DIR_FOLLOW)
prune_old_logs(LOG_DIR_STARS)

threshold = now - timedelta(days=60)
c.execute("DELETE FROM follows WHERE followed_at<?", (threshold,))
c.execute("VACUUM;")
conn.commit()
conn.close()
