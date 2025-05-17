# GitGrowBot 
*Build and nurture your GitHub network with automation. Easily follow, unfollow, star, and unstar on autopilot ✈️ so you can focus on coding while your community grows.*

GitGrowBot is your personal GitHub networking assistant. It's an automation tool designed to help you **grow** and **nurture** your developer network organically. With GitGrowBot, you’ll:

* **Follow** users from our curated list, up to a configurable limit per run.
* **Unfollow** anyone who doesn’t follow you back, because **reciprocity** matters.
* (COMING SOON) **Star** and **unstar** repositories with the same give-and-take logic.

All actions run on a schedule (or on demand) in GitHub Actions, so you never need to manually review your follow list.

## How it works
The motto **“You only get what you give”** drives GitGrowBot’s behavior:

1. GitGrowBot **follow** someone for you—chances are, they’ll notice and **follow you back** (especially if they’re clever like you and use GitGrowBot too!).  
2. If they **don’t** reciprocate by the next run, GitGrowBot quietly **unfollows** them.
3. Soon, we’ll extend this to **stars**: you star their repo, they star yours; you unstar, GitGrowBot unstars theirs.

This ensures your follow list stays active while you're busy coding.

## Features

- **Automated Follow / Unfollow**  
  - Follow 100 fresh users each run.  
  - Unfollow non-reciprocals first.  
  - Skip any usernames you whitelist.  
- **Cleaner utility** (`scripts/cleaner.py`)  
  - Deduplicates and prunes dead GitHub usernames locally.  
- **Offline logging**  
  - Records missing usernames in `logs/offline_usernames-<timestamp>.txt`.  
- **CI-first, dev-friendly**  
  - Runs hands-free in Actions.  
  - `.env` support for local testing (optional).  
- **Modular code**  
  - `scripts/bot_core.py` for main logic.  
  - `scripts/cleaner.py` for list maintenance.  
- **Prebuilt Workflow**  
  - `.github/workflows/run_bot.yml` schedules runs every 1, 3, or 5 hours (configurable).

## Getting started

1. **Fork** or **clone** this repo.
2. In **Settings → Secrets → Actions**, add your Github PA Token as `PAT_TOKEN` (scope: `user:follow`).
3. **5,500+ members like you who want to grow are waiting for you in** `config/usernames.txt`. You can join this list too—see **⭐ Don't miss out: Join our 5,500+ users** below.
4. (Important) Edit `config/whitelist.txt` to protect any accounts you never want the script to act on (mostly for not unfollowing them or unstarring their repositories).
5. (Optional) Copy `.env.example` → `.env` for local testing (or contributors).
6. **Enable** GitHub Actions in your repo settings.
7. Sit back and code—GitGrowBot handles the rest!

```bash
# Example local run of cleanup
python scripts/cleaner.py

# Example local dry-run of follow bot
python scripts/bot_core.py
```

## ⭐ Don't miss out: Join our 5,500+ users!

Want in? It’s effortless. If you:

1. **Star** this repository, **AND**
2. **Follow** both **[@ikramagix](https://github.com/ikramagix)** and **[@gr33kurious](https://github.com/gr33kurious)**

then your username will be **automatically** added to the master `usernames.txt` list alongside the **5,500+** active members!

Let's grow! 💪

## Configuration

| Options      | Description                                                   | Default                                             |
| ------------------ | ------------------------------------------------------------- | --------------------------------------------------- |
| PAT_TOKEN       | Your PAT with `user:follow` scope, added in your secrets   | (required)                                          |
| USERNAME_FILE      | List of usernames the script randomly samples to follow/star  | (keep it as it is) `config/usernames.txt`           |
| WHITELIST_FILE     | List of usernames the script will always-skip/ignore          | (editable, add usernames) `config/whitelist.txt` |
| FOLLOWERS_PER_RUN  | How many new users to follow each run                         | (keep it low to avoid rate-limit) `100`              |

## Repository structure

```
├── .github/
│   └── workflows/run_bot.yml     # Scheduled follow/unfollow workflow
├── config/
│   ├── usernames.txt             # 5,500+ community members
│   └── whitelist.txt             # Accounts to always skip
├── logs/                         # Runtime artifacts (gitignored)
│   └── offline_usernames-*.txt
├── scripts/
│   ├── bot_core.py               # Follow/unfollow logic
│   └── cleaner.py                # List maintenance
├── .env.example                  # Optional local dev settings
├── requirements.txt              # PyGithub, python-dotenv, etc.
└── README.md
```

## Contributing

We started building GitGrowBot as a peer-to-peer coding challenge on a sleepless night. But it doesn't have to end here. Feel free to:

1. **Open an issue** to suggest new features, report bugs, or share ideas.  
2. **Submit a pull request** to add enhancements, fix problems, or improve documentation.  
3. Join the discussion—your use cases, feedback, and code all keep our community vibrant.

Every contribution, big or small, helps everyone grow. Thank you for pitching in!

**Happy networking & happy coding!** 
– With 💛 from [@ikramagix](https://github.com/ikramagix) & ❤️ from [@gr33kurious](https://github.com/gr33kurious)