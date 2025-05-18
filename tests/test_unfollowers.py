# tests/test_unfollowers.py

from importlib import util
from pathlib import Path
import pytest

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
    def __init__(self, followers, following):
        self.login = "me"
        self._followers = [DummyUser(u) for u in followers]
        self._following = [DummyUser(u) for u in following]
        self.removed = []
    def get_followers(self): return self._followers
    def get_following(self): return self._following
    def remove_from_following(self, user):
        self.removed.append(getattr(user, "login", user))

class DummyGithub:
    def __init__(self, me): self._me = me
    def get_user(self, *args, **kwargs):
        return self._me if not args else None

@pytest.fixture(autouse=True)
def fake_github(monkeypatch, tmp_path):
    # empty config just to satisfy script
    cfg = tmp_path / "config"; cfg.mkdir()
    (cfg / "whitelist.txt").write_text("charlie\n")  # whitelist charlie
    (cfg / "usernames.txt").write_text("")           # not used here

    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    me = DummyMe(followers=["alice","bob"], following=["alice","charlie","delta"])
    monkeypatch.setattr("github.Github", lambda token: DummyGithub(me))
    monkeypatch.chdir(tmp_path)
    return me

def test_unfollowers_only(fake_github, capsys):
    unf = load_script(Path("scripts/unfollowers.py"))
    unf.main()
    # charlie is whitelisted, delta is the only non-reciprocal
    assert fake_github.removed == ["delta"]
    out = capsys.readouterr().out
    assert "[UNFOLLOWED] delta" in out
