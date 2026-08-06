from app.core.config import settings


def test_settings_load_environment():
    assert settings.agent_webhook_secret == "test-webhook-secret"
    assert settings.agent_github_app_id == "12345"
    assert settings.agent_github_installation_id == 999
    assert settings.environment == "test"


def test_github_configured_with_valid_env():
    assert settings.github_configured is True


def test_github_private_key_falls_back_to_path(monkeypatch, tmp_path):
    key_file = tmp_path / "key.pem"
    key_file.write_text("PATH_KEY")
    monkeypatch.setattr(settings, "agent_github_app_private_key", "")
    monkeypatch.setattr(settings, "agent_github_app_private_key_path", str(key_file))
    assert settings.github_private_key == "PATH_KEY"


def test_github_private_key_none_when_unset(monkeypatch):
    monkeypatch.setattr(settings, "agent_github_app_private_key", "")
    monkeypatch.setattr(settings, "agent_github_app_private_key_path", None)
    assert settings.github_private_key is None
