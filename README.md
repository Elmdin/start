# Start — idea in, launch packet out

An agent that takes a startup idea and returns what the founder has to do next, unattended:
a staged roadmap, a compliance checklist, first hires, funding targets, drafted documents, and a
queue of only the decisions the CEO must make.
Fallback entry for the "Build an Agent" Hackathon, Corgi Cafe, San Francisco, Oct 7, 2026.

<!-- STATUS -->
**Status: pipeline code and tests written locally; see docs for what has actually been run.**

## What it does (target)
Idea in -> packet out, no human step until the decisions:
1. Research: an Agent37 instance works through what this company has to do.
2. Structure: OpenAI structured output turns the notes into one packet JSON.
3. Audit, in code: a "sourced" claim whose URL is missing or does not resolve is downgraded to
   "unverified". Tasks per owner (agent / CEO / professional) are counted, not estimated.
4. Store: the packet is written to Supabase; the page reads it as a feed.
5. Steer: the CEO answers the decision queue.

It drafts and lists. It does not file, pay, send, sign, or give legal advice.

## Stack
- Agent37 Cloud APIs: the unattended research worker (required by the hackathon)
- OpenAI: structured output for the packet
- Supabase: stores packets and decisions; the web page reads the feed

## Layout
- `agent/packet.py`    packet schema, validation and the deterministic audit
- `agent/clients.py`   HTTP clients for Agent37, OpenAI and Supabase
- `agent/worker.py`    the pipeline CLI: `python3 -m agent.worker "your idea"`
- `agent/provision.py` creates the Agent37 instance: `python3 -m agent.provision`
- `web/index.html`     the feed page
- `supabase/schema.sql` a dedicated table, for later; today rows go to the existing `papers` table
- `docs/SCOPE.md`      the vision, today's slice, existing players, decisions, demo script
- `docs/REQUIREMENTS.md` hackathon rules, sponsor plan, submission checklist

## Run
```
cp .env.example .env    # fill it in; never commit .env
python3 -m pytest agent -q
python3 -m agent.worker "your idea"
```
