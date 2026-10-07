"""The unattended pipeline: idea in, audited launch packet in the feed, no human step.

    python3 -m agent.worker "a marketplace for ..."
    python3 -m agent.worker --steer 12      # rework packet 12 around the CEO's saved decisions

1. Research   Agent37 instance (browses, multi-step). Falls back to OpenAI alone,
              and says so in the saved row, when no instance is configured.
2. Structure  OpenAI strict structured output -> the packet (agent/packet.py).
3. Audit      Deterministic: schema, answerable decisions, sources that resolve.
4. Save       Supabase row; the web page reads the feed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agent import clients
from agent.packet import PACKET_SCHEMA, SOURCED_SECTIONS, Packet, PacketError, audit, is_http_url, validate

log = logging.getLogger("start.worker")

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
TABLE = "papers"  # shared with OpenMath today; rows are told apart by spec.kind
KIND = "startup-packet"
MAX_IDEA_CHARS = 4000
NO_RESEARCH = "(No research step ran: no Agent37 instance is configured. Nothing below has been looked up.)"

RESEARCH_PROMPT = """You are the chief of staff for a first-time founder. Work unattended; do not ask questions.
Research what this specific company must do to go from idea to a funded, operating startup.
Use your browser and cite the exact URL of every regulatory or investor fact you rely on.
Cover: (1) stages from idea to seed, with exit criteria; (2) legal, regulatory and compliance
duties specific to this sector and a sensible default jurisdiction, with official sources;
(3) the first hires and when; (4) specific investors, accelerators or grants that fit, with URLs;
(5) the few decisions only the founder can make, each with options and your recommendation.
Say plainly which points you could not verify. Reply with research notes only.

The founder's idea:
"""

STRUCTURE_SYSTEM = """You turn research notes into a launch packet for a first-time founder who wants to act
as CEO, not as the person doing the admin. Rules:
- Assign every task an owner: "agent" (you drafted or can draft it), "ceo" (a decision only the
  founder can make) or "professional" (needs a licensed lawyer, accountant or filing agent).
- Never invent a source. Use confidence "sourced" only with a real URL that supports the item;
  otherwise set source_url to "" and confidence "unverified".
- decisions: only what the founder must decide. 2-4 options each; "recommended" must equal one
  option exactly; ids are short kebab-case.
- drafts: write 2-3 real, usable first drafts in full (for example an investor one-pager, a
  first-hire job description, a 30-day plan). Not placeholders.
- limits: state honestly what this packet does not do.
- If the input lists decisions the CEO has already made, they are settled: never ask them again,
  rebuild the roadmap, compliance list and drafts around the chosen options, and list only the
  new decisions those choices open up.
Be specific to this company. No filler."""


class WorkerError(RuntimeError):
    """The run stopped before a packet was saved."""


@dataclass(frozen=True)
class Deps:
    """Everything the pipeline touches outside itself."""

    research: Callable[[str], tuple[str, str]]
    structure: Callable[[str, str], Packet]
    url_ok: Callable[[str], bool]
    save: Callable[[dict[str, Any]], dict[str, Any]]


def build_row(
    idea: str, worker: str, packet: Packet, report: dict[str, Any], extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    spec = {"kind": KIND, "idea": idea, "worker": worker, "packet": packet, "audit": report}
    return {"title": packet["company"]["name"], "spec": {**spec, **(extra or {})}}


def _check_urls(packet: Packet, url_ok: Callable[[str], bool]) -> dict[str, bool]:
    urls = sorted(
        {item["source_url"].strip() for section in SOURCED_SECTIONS for item in packet[section]} - {""}
    )
    urls = [url for url in urls if is_http_url(url)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(urls, pool.map(url_ok, urls)))


def run(idea: str, deps: Deps, brief: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the whole pipeline once and return the saved row.

    `brief` replaces the idea as the text the agent works from (used when steering);
    the row always records the founder's original idea.
    """
    started = time.monotonic()
    idea = idea.strip()
    if not idea:
        raise WorkerError("The idea is empty.")
    if len(idea) > MAX_IDEA_CHARS:
        raise WorkerError(f"The idea is longer than {MAX_IDEA_CHARS} characters.")

    task = brief or idea
    worker, notes = deps.research(task)
    log.info("research done by %s (%d chars)", worker, len(notes))
    packet = deps.structure(task, notes)
    try:
        validate(packet)
    except PacketError as error:
        raise WorkerError(f"The packet failed validation and was not saved: {error}") from error

    resolved = _check_urls(packet, deps.url_ok)
    audited, report = audit(packet, lambda url: resolved.get(url, False))
    report = {**report, "seconds": round(time.monotonic() - started, 1)}
    log.info("audit: %s", json.dumps(report))
    return deps.save(build_row(idea, worker, audited, report, extra))


def collect_choices(packet_row: dict[str, Any], decision_rows: list[dict[str, Any]]) -> dict[str, str]:
    """The CEO's newest choice per decision, keeping only choices the packet actually offered.

    Decision rows come from a table anyone can insert into, so nothing in them is trusted.
    """
    options = {decision["id"]: decision["options"] for decision in packet_row["spec"]["packet"]["decisions"]}
    choices: dict[str, str] = {}
    for row in sorted(decision_rows, key=lambda row: row.get("id") or 0):
        spec = row.get("spec")
        if not isinstance(spec, dict) or spec.get("packet_id") != packet_row["id"]:
            continue
        decision_id, choice = spec.get("decision_id"), spec.get("choice")
        if decision_id in options and choice in options[decision_id]:
            choices = {**choices, decision_id: choice}
    return choices


def steer_brief(idea: str, packet: Packet, choices: dict[str, str]) -> str:
    questions = {decision["id"]: decision["question"] for decision in packet["decisions"]}
    decided = "\n".join(f"- {questions[key]} -> {choice}" for key, choice in choices.items())
    return (
        f"{idea}\n\nThe CEO has reviewed your first plan and DECIDED:\n{decided}\n\n"
        "Rework the plan around these choices. Research what each choice now requires "
        "(filings, licences, contracts, vendors), and say what new decisions they open up.\n\n"
        f"Your first plan, for reference:\n{json.dumps(packet)[:12000]}"
    )


def steer(packet_row: dict[str, Any], choices: dict[str, str], deps: Deps) -> dict[str, Any]:
    """Produce the next revision of a packet from the decisions the CEO saved."""
    if not choices:
        raise WorkerError("No decisions have been saved for this packet yet. Answer some on the page first.")
    spec = packet_row["spec"]
    brief = steer_brief(spec["idea"], spec["packet"], choices)
    return run(spec["idea"], deps, brief=brief, extra={"revision_of": packet_row["id"], "decided": choices})


def _keep(name: str, text: str) -> None:
    """Keep paid-for output on disk so a later failure does not lose it."""
    RUNS.mkdir(exist_ok=True)
    (RUNS / name).write_text(text)


def real_deps(env: dict[str, str]) -> Deps:
    clients.require(env, "OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY")
    model = env.get("OPENAI_MODEL") or "gpt-5.5"
    instance = env.get("AGENT37_INSTANCE_ID", "")

    def research(idea: str) -> tuple[str, str]:
        if not instance:
            log.warning("AGENT37_INSTANCE_ID is not set: skipping research, the row will say 'openai-direct'")
            return "openai-direct", NO_RESEARCH
        clients.require(env, "AGENT37_API_KEY")
        response = clients.agent37_respond(env["AGENT37_API_KEY"], instance, RESEARCH_PROMPT + idea)
        _keep("last-research.md", response["output_text"])
        return "agent37", response["output_text"]

    def structure(idea: str, notes: str) -> Packet:
        user = f"The founder's idea:\n{idea}\n\nResearch notes:\n{notes}"
        packet = clients.openai_structured(env["OPENAI_API_KEY"], model, STRUCTURE_SYSTEM, user, PACKET_SCHEMA)
        _keep("last-packet.json", json.dumps(packet, indent=2))
        return packet

    def save(row: dict[str, Any]) -> dict[str, Any]:
        return clients.supabase_insert(env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"], TABLE, row)

    return Deps(research=research, structure=structure, url_ok=clients.url_resolves, save=save)


def load_for_steer(env: dict[str, str], packet_id: int) -> tuple[dict[str, Any], dict[str, str]]:
    def select(query: dict[str, str]) -> list[dict[str, Any]]:
        return clients.supabase_select(env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"], TABLE, query)

    found = select({"select": "*", "id": f"eq.{packet_id}", "spec->>kind": f"eq.{KIND}"})
    if not found:
        raise WorkerError(f"No packet with id {packet_id} in the feed.")
    try:
        validate(found[0]["spec"]["packet"])
    except (PacketError, KeyError, TypeError) as error:
        raise WorkerError(f"Packet {packet_id} in the feed is malformed: {error}") from error
    decisions = select({"select": "id,spec", "spec->>kind": "eq.startup-decision", "spec->>packet_id": f"eq.{packet_id}"})
    return found[0], collect_choices(found[0], decisions)


def write_web_files(env: dict[str, str], row: dict[str, Any], web: Path) -> None:
    """Give the static page its public config and an offline copy of the newest packet."""
    config = {"supabaseUrl": env["SUPABASE_URL"], "anonKey": env["SUPABASE_ANON_KEY"]}
    (web / "config.js").write_text(f"window.START_CONFIG = {json.dumps(config)};\n")
    (web / "latest.js").write_text(f"window.START_LATEST = {json.dumps(row)};\n")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Turn a startup idea into an audited launch packet.")
    parser.add_argument("idea", nargs="?", help="the idea, in the founder's own words")
    parser.add_argument("--steer", type=int, metavar="PACKET_ID", help="rework a saved packet around the CEO's decisions")
    args = parser.parse_args(argv)
    if (args.idea is None) == (args.steer is None):
        parser.error("give either an idea or --steer PACKET_ID")
    try:
        env = clients.load_env(ROOT / ".env")
        deps = real_deps(env)
        if args.steer is None:
            row = run(args.idea, deps)
        else:
            row = steer(*load_for_steer(env, args.steer), deps)
        write_web_files(env, row, ROOT / "web")
    except (WorkerError, clients.ClientError) as error:
        log.error("%s", error)
        return 1
    except Exception:  # last line of defence: say what broke, exit non-zero
        log.exception("unexpected failure; any research or packet already paid for is in %s", RUNS)
        return 1
    log.info("saved packet id=%s title=%s worker=%s", row.get("id"), row.get("title"), row["spec"]["worker"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
