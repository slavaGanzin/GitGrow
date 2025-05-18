# GitGrowBot 

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
  - `scripts/gitgrow.py` for main logic.  
  - `scripts/cleaner.py` for list maintenance.  
- **Prebuilt Workflow**  
  - `.github/workflows/run_bot.yml` scheduled runner every 1, 3, or 5 hours (configurable).
  - `.github/workflows/manual_follow.yml` – manual trigger: **follow & follow-back only**  
  - `.github/workflows/manual_unfollow.yml` – manual trigger: **unfollow non-reciprocals only**  

## Getting started

1. **Fork** or **clone** this repo.
2. In **Settings → Secrets → Actions**, add your Github PAT as `PAT_TOKEN` (scope: `user:follow`).
3. **5,500+ members like you who want to grow are waiting for you in** `config/usernames.txt`. You can join this list too—see below (**⭐ Don't miss out: Join our 5,500+ users**).
4. Edit the `schedule.cron` in `run_bot.yml` to your desired interval.
5. (Important) Edit `config/whitelist.txt` to protect any accounts you never want the script to act on (mostly for not unfollowing them or unstarring their repositories).
6. (Optional) Copy `.env.example` → `.env` for local testing (or contributors).
7. **Enable** GitHub Actions in your repo settings.
8. Sit back and code—GitGrowBot handles the rest!

```bash
# Example local run of cleanup
python scripts/cleaner.py

# Example local dry-run of follow bot
python scripts/gitgrow.py
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
| PAT_TOKEN       | Your PAT with `user:follow` scope, added in your secrets   |(empty) **required**                                      |
| USERNAME_FILE      | File listing target usernames (in the `config/` directory)  | `config/usernames.txt` (keep it as it is)            |
| WHITELIST_FILE     | File listing usernames never to unfollow (in `config/`)          | `config/whitelist.txt` (editable, add usernames) |
| FOLLOWERS_PER_RUN  | How many new users to follow each run                         | `100` (keep it low to avoid rate-limit)               |

## Repository structure

```
├── .gitattributes
├── .github
│   └── workflows
│       ├── run_bot.yml          # Scheduled: unfollow + follow
│       ├── manual_follow.yml    # workflow_dispatch → follow only
│       └── manual_unfollow.yml  # workflow_dispatch → unfollow only
├── .gitignore
├── README.md
├── config
│   ├── usernames.txt            # 5,500+ community members
│   └── whitelist.txt            # accounts to always skip
├── logs                         # CI artifacts (gitignored)
│   └── offline_usernames-*.txt
├── requirements.txt
└── scripts
│   ├── gitgrow.py               # Main follow/unfollow driver
│   ├── unfollowers.py           # Unfollow-only logic
│   └── cleaner.py               # Username list maintenance
├──tests/
│   ├── test_bot_core_behavior.py   # follow/unfollow/follow-back
│   ├── test_unfollowers.py         # unfollow-only logic
│   └── test_cleaner.py             # cleaner dedupe + missing-user removal
```
### Manual Troubleshooting Runners (optional)

If you ever need to isolate one step for debugging, head to your repo’s **Actions** tab:

- **GitGrowBot Manual Follow** (`.github/workflows/manual_follow.yml`)  
  Manually triggers **only** the follow & follow-back logic.  
- **GitGrowBot Manual Unfollow** (`.github/workflows/manual_unfollow.yml`)  
  Manually triggers **only** the unfollow non-reciprocals logic.  

Choose the workflow, click **Run workflow**, select your branch, and go!

## Contributing

We started building GitGrowBot as a peer-to-peer coding challenge on a sleepless night. But it doesn't have to end here. Feel free to:

1. **Open an issue** to suggest new features, report bugs, or share ideas.  
2. **Submit a pull request** to add enhancements, fix problems, or improve documentation.  
3. Join the discussion—your use cases, feedback, and code all keep our community vibrant.

Every contribution, big or small, helps everyone grow. Thank you for pitching in!

**Happy networking & happy coding!** 

<div>
<a href="https://www.buymeacoffee.com/ikramagix" target="_blank">
  <img 
    src="https://i.ibb.co/tP37SFx/cuphead-thx-nobg.png" 
    alt="Buy Me A Coffee" 
    width="150">
</a>
</div>

<br>

– With 💛 from [@ikramagix](https://github.com/ikramagix) & [@gr33kurious](https://github.com/gr33kurious)