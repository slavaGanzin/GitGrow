# tests/test_gitgrow_behavior.py
import pytest
from importlib import util
from pathlib import Path
from github import GithubException

def load_script(path):
    project_root = Path(__file__).parent.parent
    full_path = project_root / path
    spec = util.spec_from_file_location(full_path.stem, full_path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class DummyUser:
    def __init__(self, login): self.login = login

class DummyMe:
    def __init__(self):
        self.login = "me"
        # followers & following both contain these → no follow-back
        self._followers = [DummyUser(u) for u in ["sotiris", "zakaria"]]
        self._following = [DummyUser(u) for u in ["sotiris", "zakaria"]]
        self.added = []

    def get_followers(self): return self._followers
    def get_following(self): return self._following

    def add_to_following(self, user):
        self.added.append(getattr(user, "login", user))

class DummyGithub:
    def __init__(self, me): self._me = me

    def get_user(self, *args, **kwargs):
        # no args → authenticated user
        if not args:
            return self._me
        login = args[0]
        # simulate missing user
        if login == "dne":
            raise GithubException(404, {"message": "Not Found"})
        return DummyUser(login)

@pytest.fixture(autouse=True)
def fake_github(monkeypatch):
    # fake token + patch Github()
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    me = DummyMe()
    monkeypatch.setattr("github.Github", lambda token: DummyGithub(me))
    return me

def test_gitgrow_follow_and_back(fake_github, patch_config, capsys):
    bot = load_script(Path("scripts/gitgrow.py"))
    bot.main()

    # should follow only irene & guadalupe
    assert "irene" in fake_github.added
    assert "guadalupe" in fake_github.added

    # never touch existing or whitelisted
    assert "sotiris" not in fake_github.added
    assert "zakaria" not in fake_github.added

    out = capsys.readouterr().out
    assert "[FOLLOWED] irene" in out
    assert "[FOLLOWED] guadalupe" in out
    # no follow-back because followers == following
    assert "[FOLLOW-BACKED]" not in out
