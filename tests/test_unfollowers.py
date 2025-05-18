# tests/test_unfollowers.py
import pytest
from importlib import util
from pathlib import Path

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
        # these two follow you back, but 'charlie' does not
        self._followers = [DummyUser(u) for u in ["sotiris", "zakaria"]]
        self._following = [DummyUser(u) for u in ["sotiris", "zakaria", "charlie"]]
        self.removed = []

    def get_followers(self): return self._followers
    def get_following(self): return self._following

    def remove_from_following(self, user):
        self.removed.append(getattr(user, "login", user))

class DummyGithub:
    def __init__(self, me): self._me = me
    def get_user(self, *args, **kwargs):
        return self._me

@pytest.fixture(autouse=True)
def fake_github(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    me = DummyMe()
    monkeypatch.setattr("github.Github", lambda token: DummyGithub(me))
    return me

def test_unfollowers_only(fake_github, patch_config, capsys):
    unf = load_script(Path("scripts/unfollowers.py"))
    unf.main()

    # only 'charlie' is non-reciprocal & not whitelisted
    assert fake_github.removed == ["charlie"]
    out = capsys.readouterr().out
    assert "[UNFOLLOWED] charlie" in out
