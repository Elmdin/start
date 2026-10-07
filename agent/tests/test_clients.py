import pytest

from agent import clients


def test_load_env_parses_and_skips_comments(tmp_path):
    path = tmp_path / ".env"
    path.write_text("# note\nA=1\nB=x=y\n\n")
    assert clients.load_env(path) == {"A": "1", "B": "x=y"}


def test_load_env_missing_file(tmp_path):
    with pytest.raises(clients.ClientError, match="not found"):
        clients.load_env(tmp_path / ".env")


def test_require_names_missing_keys():
    with pytest.raises(clients.ClientError, match="B, C"):
        clients.require({"A": "1", "B": ""}, "A", "B", "C")


@pytest.mark.parametrize("url", ["http://127.0.0.1/x", "http://localhost/x", "http://169.254.169.254/latest", "ftp://example.com", "http://10.0.0.5/"])
def test_url_resolves_refuses_non_public_targets(url):
    assert clients.url_resolves(url) is False


def test_load_env_strips_quotes(tmp_path):
    path = tmp_path / ".env"
    path.write_text("A=\"x\"\nB='y'\n")
    assert clients.load_env(path) == {"A": "x", "B": "y"}


def test_supabase_insert_tolerates_trailing_slash(monkeypatch):
    seen = []
    monkeypatch.setattr(clients, "_call", lambda service, method, url, headers, body=None, timeout=60: seen.append(url) or [{"id": 1}])
    assert clients.supabase_insert("https://x.supabase.co/", "k", "papers", {}) == {"id": 1}
    assert seen == ["https://x.supabase.co/rest/v1/papers"]


def test_redirect_to_private_host_is_refused():
    handler = clients._PublicRedirects()
    with pytest.raises(clients.urllib.error.URLError):
        handler.redirect_request(None, None, 302, "Found", {}, "http://127.0.0.1:9/x")


def test_parse_monid_results_keeps_only_http_results():
    payload = {"status": "COMPLETED", "output": {"results": [
        {"title": "A", "url": "https://a.example/x", "snippet": "s" * 900},
        {"title": "B", "url": "javascript:alert(1)", "snippet": "x"},
        {"title": "C"},
        "junk",
    ]}}
    results = clients.parse_monid_results(payload)
    assert [r["url"] for r in results] == ["https://a.example/x"]
    assert len(results[0]["snippet"]) == 400


def test_parse_monid_results_rejects_unfinished_runs():
    with pytest.raises(clients.ClientError, match="FAILED"):
        clients.parse_monid_results({"status": "FAILED"})
