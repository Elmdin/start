"""HTTP clients for the three services, on the standard library only.

Each function takes its credentials as arguments so the pipeline can be tested
without a network and so nothing here reads global state.
"""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

AGENT37_API = "https://api.agent37.com"
OPENAI_API = "https://api.openai.com"
USER_AGENT = "start-agent/0.1 (hackathon link check)"


class ClientError(RuntimeError):
    """A service call failed. The message names the service and the status, never a key."""


def load_env(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env file into a new dict."""
    if not path.exists():
        raise ClientError(f"{path} not found. Copy .env.example to .env and fill it in.")
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line and not line.startswith("#"))
    return {key.strip(): value.strip().strip("\"'") for key, value in pairs}


def require(env: dict[str, str], *names: str) -> None:
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise ClientError(f"Missing in .env: {', '.join(missing)}")


def _call(service: str, method: str, url: str, headers: dict[str, str], body: Any = None, timeout: int = 60) -> Any:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json", "User-Agent": USER_AGENT, **headers}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https hosts
            return json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise ClientError(f"{service} returned {error.code}: {detail}") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ClientError(f"{service} call failed: {error}") from error


# --- Agent37 -----------------------------------------------------------------


def agent37_create_instance(key: str, name: str, credit_micros: int) -> dict[str, Any]:
    return _call(
        "Agent37",
        "POST",
        f"{AGENT37_API}/v1/instances",
        {"Authorization": f"Bearer {key}"},
        {"name": name, "budget": {"credit_micros": credit_micros}},
        timeout=180,
    )


def agent37_healthy(key: str, instance_id: str) -> bool:
    health = _call("Agent37", "GET", f"https://{instance_id}.agent37.app/v1/health", {"X-Agent37-Key": key}, timeout=20)
    return bool(health and health.get("healthy"))


def agent37_respond(key: str, instance_id: str, prompt: str, timeout: int = 900) -> dict[str, Any]:
    """Run one unattended turn and return the finished response object."""
    response = _call(
        "Agent37",
        "POST",
        f"https://{instance_id}.agent37.app/v1/responses",
        {"X-Agent37-Key": key},
        {"input": prompt, "stream": False},
        timeout=timeout,
    )
    if not isinstance(response, dict):
        raise ClientError("Agent37 returned an empty response")
    if response.get("status") != "completed" or not response.get("output_text"):
        raise ClientError(f"Agent37 turn ended as '{response.get('status')}': {response.get('error')}")
    return response


# --- OpenAI ------------------------------------------------------------------


def openai_structured(key: str, model: str, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Ask for JSON that must match `schema` (strict structured output)."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "launch_packet", "strict": True, "schema": schema}},
    }
    reply = _call("OpenAI", "POST", f"{OPENAI_API}/v1/chat/completions", {"Authorization": f"Bearer {key}"}, body, timeout=600)
    try:
        message = reply["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise ClientError(f"OpenAI reply had an unexpected shape: {str(reply)[:300]}") from error
    if message.get("refusal") or not message.get("content"):
        raise ClientError(f"OpenAI returned no packet: {message.get('refusal') or 'empty content'}")
    try:
        return json.loads(message["content"])
    except json.JSONDecodeError as error:
        raise ClientError(f"OpenAI returned text that is not JSON: {error}") from error


# --- Supabase ----------------------------------------------------------------


def supabase_insert(url: str, anon_key: str, table: str, row: dict[str, Any]) -> dict[str, Any]:
    rows = _call(
        "Supabase",
        "POST",
        f"{url.rstrip('/')}/rest/v1/{table}",
        {"apikey": anon_key, "Authorization": f"Bearer {anon_key}", "Prefer": "return=representation"},
        row,
    )
    if not rows:
        raise ClientError("Supabase accepted the insert but returned no row")
    return rows[0]


def supabase_select(url: str, anon_key: str, table: str, query: dict[str, str]) -> list[dict[str, Any]]:
    rows = _call(
        "Supabase",
        "GET",
        f"{url.rstrip('/')}/rest/v1/{table}?{urlencode(query)}",
        {"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
    )
    if not isinstance(rows, list):
        raise ClientError("Supabase returned something other than a list of rows")
    return rows


# --- Monid (tool gateway) ----------------------------------------------------

MONID_SEARCH = ("keenable", "/v1/search")  # $0.004 per search when inspected on 7 Oct 2026


def parse_monid_results(payload: Any) -> list[dict[str, str]]:
    """Reduce a Monid run to title/url/snippet, dropping anything that is not an http(s) result."""
    if not isinstance(payload, dict) or payload.get("status") != "COMPLETED":
        status = payload.get("status") if isinstance(payload, dict) else "unreadable"
        raise ClientError(f"Monid run ended as {status}")
    raw = (payload.get("output") or {}).get("results") or []
    results = []
    for item in raw:
        if not isinstance(item, dict) or not str(item.get("url", "")).startswith(("https://", "http://")):
            continue
        results.append(
            {"title": str(item.get("title", ""))[:200], "url": item["url"], "snippet": str(item.get("snippet", ""))[:400]}
        )
    return results


def monid_search(monid_bin: Path, node_dir: str, query: str, max_results: int = 5) -> list[dict[str, str]]:
    """One web search through the Monid CLI. The query is passed as an argument, never through a shell."""
    provider, endpoint = MONID_SEARCH
    body = json.dumps({"query": query[:400], "max_results": max_results, "snippet_max_length": 400, "mode": "realtime"})
    command = [str(monid_bin), "run", "-p", provider, "-e", endpoint, "-i", body, "-w", "45", "-j"]
    env = {**os.environ, "PATH": f"{node_dir}{os.pathsep}{os.environ.get('PATH', '')}", "NO_COLOR": "1"}
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=60, env=env, check=False)  # noqa: S603
        payload = json.loads(done.stdout[done.stdout.index("{") :])
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        raise ClientError(f"Monid search failed: {error}") from error
    return parse_monid_results(payload)


# --- Link check --------------------------------------------------------------


def _is_public_host(host: str) -> bool:
    """False for loopback, private and link-local addresses, so a model-written URL cannot reach inside."""
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except (socket.gaierror, UnicodeError):
        return False
    return bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses)


class _PublicRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only if it still points at a public http(s) host."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        parsed = urlparse(newurl)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or not _is_public_host(parsed.hostname):
            raise urllib.error.URLError(f"redirect to a non-public address refused: {parsed.hostname}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_LINK_OPENER = urllib.request.build_opener(_PublicRedirects)


def url_resolves(url: str, timeout: int = 8) -> bool:
    """True if a public http(s) URL answers below 400. Says nothing about what the page claims."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or not _is_public_host(parsed.hostname):
        return False
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with _LINK_OPENER.open(request, timeout=timeout) as response:
            return response.status < 400
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return False
