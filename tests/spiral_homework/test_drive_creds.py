# tests/spiral_homework/test_drive_creds.py
import json

import pytest

from agent.tools.spiral_homework import drive_store


class FakeCreds:
    def __init__(self, valid=False, refresh_token="rt"):
        self.valid = valid
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        self.valid = True


def _patch_from_info(monkeypatch, fake):
    import google.oauth2.credentials as goc
    monkeypatch.setattr(goc.Credentials, "from_authorized_user_info",
                        lambda info, scopes=None: fake)


def test_env_token_is_used_and_refreshed(monkeypatch):
    fake = FakeCreds(valid=False, refresh_token="rt")
    _patch_from_info(monkeypatch, fake)
    monkeypatch.setenv("NOVA_DRIVE_TOKEN_JSON", json.dumps({"refresh_token": "rt"}))
    creds = drive_store._get_creds()
    assert creds is fake
    assert fake.refreshed


def test_env_token_still_valid_skips_refresh(monkeypatch):
    fake = FakeCreds(valid=True)
    _patch_from_info(monkeypatch, fake)
    monkeypatch.setenv("NOVA_DRIVE_TOKEN_JSON", json.dumps({"refresh_token": "rt"}))
    creds = drive_store._get_creds()
    assert creds is fake
    assert not fake.refreshed


def test_env_token_without_refresh_token_raises(monkeypatch):
    fake = FakeCreds(valid=False, refresh_token=None)
    _patch_from_info(monkeypatch, fake)
    monkeypatch.setenv("NOVA_DRIVE_TOKEN_JSON", json.dumps({"token": "at"}))
    with pytest.raises(RuntimeError, match="re-mint"):
        drive_store._get_creds()
