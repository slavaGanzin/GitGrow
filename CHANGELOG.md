## \[1.0.0] – 2025-05-19 (Pre-release)

* Initial public release of GitGrowBot.
* Automated follow/unfollow via scheduled GitHub Actions.
* Whitelist support to protect accounts from actions.
* Configurable target user list (`usernames.txt`), deduped and checked.
* Only follows accounts active in the last 3 days.
* Username cleaner utility (dedupe, dead user removal, offline logging).
* Manual workflows for on-demand actions and isolated testing.
* Isolated config/testing infrastructure.

**Contributors:**
[@ikramagix](https://github.com/ikramagix), [@gr33kurious](https://github.com/gr33kurious)
[All commits →](https://github.com/ikramagix/GitGrowBot/commits/1.0.0)

---

## \[1.1.0] – 2025-06-04

### Added

* Menu navigation in README.
* Expanded `usernames.txt` (now over 161,000 deduplicated, active users).
* Stargazer tracking:

  * `.github/workflows/stargazer_shoutouts.yml` tracks new/lost stargazers.
  * Artifacts for each run, state persisted on `tracker-data` branch.
* Follow logic now targets only users active in last 3 days.

### Changed

* Follower batch size is now random (5–55 per run) for rate-limit safety.

### Deprecated

* `.github/workflows/run_orgs.yml` and `scripts/orgs.py` (org-member mass-follow):

  * **Deprecated due to poor results** – did not increase profile visits or organic followers.

### Maintainer-only

* Local scripts (`.env`, `scripts/cleaner.py`, `scripts/gitgrow.py` for local runs).
* Manual workflows (`manual_follow.yml`, `manual_unfollow.yml`).
* Stargazer shoutouts workflow is for repo analytics/discussion, not for general users.

**Contributors:**
[@ikramagix](https://github.com/ikramagix)
[All commits →](https://github.com/ikramagix/GitGrowBot/commits/1.1.0)

---