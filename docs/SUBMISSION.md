# Submission form answers (paste-ready)

Form closes 4:40 PM PDT, 7 Oct 2026. One submission per team: submit this OR OpenMath, not both.
Fields marked YOU are yours to fill.

**Project name**
Start

**Team name and member names**
Solo entry. Team name: Elmdin (change if you prefer). Member: YOU (your name)

**Team lead contact email**
YOU (your email; not written here because this repo is public)

**What does your agent do, and which workflow does it improve?**
Start takes a startup idea in one sentence and, with no human step, returns a launch packet:
a staged roadmap from idea to seed, a compliance checklist with sources, first hires, funding
targets with sources, full first drafts of the documents you need, and a short queue of the only
decisions the founder has to make.

The workflow it replaces is the founder's first weeks of admin: working out what a new company
legally and operationally has to do, in what order, who has to do it, and drafting it. Every task
is assigned to the agent, the CEO, or a licensed professional, so the founder steers instead of
doing the paperwork. When the founder answers decisions on the page, the agent reworks the whole
plan around those choices and publishes a revision.

It checks itself in code, not with the model: a claim keeps its "sourced" label only if its link
is a real web address that loads; everything else is downgraded to "unverified" and shown that
way. The workload split and the agent's run time are counted and measured, not estimated.

It drafts and lists. It does not file, pay, send, sign, or give legal advice.

**Demo video URL**
YOU (record, upload, set to "anyone with the link")

**Live project, GitHub, or additional Drive links**
https://github.com/Elmdin/start

**Describe your Agent37 Cloud API integration and any OpenAI, Supabase, InstaCloud, or Monid integrations**
- Agent37 Cloud API: the unattended worker. We create an instance with `POST /v1/instances`
  (with a managed-spend budget), wait on `GET /v1/health`, then send the idea to the instance's
  `POST /v1/responses`. The Agent37 agent browses and works through many steps on its own and
  returns cited research notes. The same call is used again for the steer loop: the founder's
  saved decisions go back to the agent, which reworks the plan. Code: `agent/clients.py`,
  `agent/provision.py`, `agent/worker.py`.
- OpenAI: strict structured output (JSON schema, `gpt-5.5`) turns the research notes into the
  launch packet, so the page and the audit always get the same shape.
- Supabase: stores every finished packet and every CEO decision as rows; the web page reads the
  feed over the REST API and writes decisions back; the worker reads those decisions to steer.
- Monid: the agent's tool gateway. Before research, the worker runs live web searches through
  Monid (Keenable search endpoint) for regulations, investors and competitors, and passes the
  results to the agent as leads and sources.
- InstaCloud: not used.

## Before you press submit
- [ ] Demo video link opens in a private window
- [ ] https://github.com/Elmdin/start opens in a private window
- [ ] Team name, members and lead email filled in
- [ ] Optional file uploads: at most 5 files, 10 MB each
