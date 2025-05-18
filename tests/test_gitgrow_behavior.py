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
    def __init__(self):
        self.login = "me"
        self._followers = [DummyUser("alice")]
        self._following = [DummyUser("alice")]
        self.added = []
    def get_followers(self): return self._followers
    def get_following(self): return self._following
    def add_to_following(self, user):
        self.added.append(getattr(user, "login", user))

class DummyGithub:
    def __init__(self, me): self._me = me
    def get_user(self, *args, **kwargs):
        return self._me if not args else DummyUser(args[0])

@pytest.fixture(autouse=True)
def fake_github(monkeypatch, tmp_path):
    cfg = tmp_path / "config"; cfg.mkdir()
    (cfg / "usernames.txt").write_text("bob\ncarol\nalice\n")
    (cfg / "whitelist.txt").write_text("carol\n")

    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    me = DummyMe()
    monkeypatch.setattr("github.Github", lambda token: DummyGithub(me))
    monkeypatch.chdir(tmp_path)
    return me

def test_gitgrow_follow_and_back(fake_github, capsys):
    bot = load_script(Path("scripts/gitgrow.py"))
    bot.main()
    # should follow bob only (carol whitelisted, alice already)
    assert "bob" in fake_github.added
    assert "carol" not in fake_github.added
    out = capsys.readouterr().out
    assert "[FOLLOWED] bob" in out
    assert "[FOLLOW-BACKED]" not in out  # only alice followers already
