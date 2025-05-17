**GitGrowBot** 🎉
*Build and nurture your GitHub network with the principle: **You only get what you give***

---

## 🚀 What is GitGrowBot?

GitGrowBot is a GitHub automation tool designed to help you **grow** and **nurture** your developer network organically. With GitGrowBot, you’ll:

* **Follow** users from our curated list, up to a configurable limit per run.
* **Unfollow** anyone who doesn’t follow you back—because **reciprocity** matters.
* (Planned) **Star** and **Unstar** repositories with the same give-and-take mindset.

All actions run on a schedule (or on demand) in GitHub Actions, so you never need to babysit your follow list.

---

## 🎯 Why "You Only Get What You Give"?

In the open-source community, building genuine connections is key. The motto **“You only get what you give”** drives GitGrowBot’s behavior:

1. **Follow** someone → they see the connection and may follow you back.
2. If they **don’t** follow back within a set time, GitGrowBot **unfollows** them.
3. For stars and other interactions, the same reciprocity logic applies (future releases).

This ensures your follow list stays engaged and active while you're coding.

---

## ✨ Features

* **Automated Follow/Unfollow**: Scale your follow rate to \`FOLLOWERS\_PER\_RUN\` each run, skip whitelisted users, and unfollow non-reciprocals first.
* **Cleaner Utility**: Deduplicate and prune dead GitHub usernames from your list with \`cleaner.py\`. We usually do it, but you might need it on your fork.
* **Offline Logging**: Missing/offline usernames are logged in \`logs/offline\_usernames-<timestamp>.txt\`.
* **Env-Driven**: Configure via **.env** or GitHub Secrets without touching Python code: it's for everyone, no matter what's your stack.
* **Modular Scripts**: \`scripts/bot\_core.py\` for the follow/unfollow logic, \`scripts/cleaner.py\` for cleanup.
* **GitHub Actions Ready**: Prebuilt workflow under \`.github/workflows/run\_bot.yml\`—cron scheduling every 3 hours (configurable).

---

## ⚙️ Getting Started

1. **Fork** or **clone** this repo.
2. Copy \`.env.example\` to \`.env\` and fill in your **GITHUB\_TOKEN** (PAT with \`user\:follow\` scope).
3. **Edit** \`config/usernames.txt\` to include who you want to follow (one per line).
4. (Optional) Edit \`config/whitelist.txt\` to keep certain users always untouched.
5. **Commit** and push your changes.
6. **Enable** GitHub Actions in your repo settings.
7. Sit back—your bot runs on schedule!

```bash
# Example local run of cleanup
python scripts/cleaner.py

# Example local dry-run of follow bot
python scripts/bot_core.py
```

---

## ⭐ Special Perk: Join the 5,500+ Community

If you:

1. **Star** this repository, **AND**
2. **Follow** both **[@ikramagix](https://github.com/ikramagix)** and **[@gr33kurious](https://github.com/gr33kurious)**

then your username will be **automatically** added to the master \`usernames.txt\` list alongside the **5,500+** existing participants!

Growing together, one follow at a time. 💪

---

## 🛠️ Configuration

| Env Var             | Description                                           | Default                  |
| ------------------- | ----------------------------------------------------- | ------------------------ |
| GITHUB\_TOKEN       | Your PAT with \`user\:follow\` scope                  | (required)               |
| USERNAME\_FILE      | Path to the follower targets list                     | \`config/usernames.txt\` |
| WHITELIST\_FILE     | Path to always-skip list                              | \`config/whitelist.txt\` |
| FOLLOWERS\_PER\_RUN | How many new users to follow each run                 | \`100\`                  |

---

## 📁 Repository Structure

```
.gitignore
.env.example
README.md
requirements.txt

config/         # Data files
  ├── usernames.txt
  └── whitelist.example.txt

scripts/        # Python entrypoints
  ├── bot_core.py
  └── cleaner.py

logs/           # CI-run artifacts (gitignored)
  └── offline_usernames-YYYYMMDDHHMM.txt

.github/workflows/run_bot.yml  # Scheduled follow/unfollow workflow
```

---

## 🤝 Contributing

1. **Star** this repo & **follow** the founders!
2. Open an **issue** or **PR** for bug reports or feature requests.
3. Keep the motto alive: help others, and they’ll help you back!

---

**Happy networking & happy coding!** 🎉
– @ikramagix & @gr33kurious