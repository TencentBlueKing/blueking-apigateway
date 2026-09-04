from apigateway.biz.sdk.process import build_subprocess_env, redact_sensitive_text


def test_build_subprocess_env_only_keeps_allowlisted_values(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("BKREPO_PASSWORD", "repository-secret")

    env = build_subprocess_env({"HOME": "/tmp/sdk-home"})

    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == "/tmp/sdk-home"
    assert "BKREPO_PASSWORD" not in env


def test_redact_sensitive_text_removes_labeled_and_url_credentials():
    value = "token=abc password=def secret=ghi https://user:pass@example.com/path"

    redacted = redact_sensitive_text(value)

    assert redacted == "token=*** password=*** secret=*** https://***@example.com/path"
