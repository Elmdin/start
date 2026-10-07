# Hackathon requirements

"Build an Agent" Hackathon, Corgi Cafe (office area), 9 Claude Ln, San Francisco, 7 Oct 2026.
Source: the event page, https://luma.com/b54ojqhl. Rules copied from
`../OpenMath/docs/REQUIREMENTS.md`. Judging criteria are announced at kickoff and are NOT
published; fill in the section at the bottom when known.

This project is the fallback entry if OpenMath does not land. Only one gets submitted.

## Hard requirements
- [ ] Uses Agent37 Cloud APIs (mandatory for prize eligibility)
- [ ] Uses at least one sponsor in the app: OpenAI, Supabase, InstaCloud, Monid ("the more, the better")
- [ ] Submitted by 4:40 PM with:
  - [ ] team members
  - [ ] the workflow replaced
  - [ ] demo video link
  - [ ] sponsor integrations used
  - [ ] live project or repo link (judges must open it without requesting access)
  - [ ] at most five files, 10 MB each
- [ ] A public repo or a live link. This project is a local git repo only: no remote, nothing pushed.

## Theme
"What's the workflow you never want to do again?" They want agents you can sell.
Finalists show: what they replaced, how the agent works, how much time it saves.

## Schedule
2:00 doors · 2:20 kickoff · 2:30 build · 4:40 submissions close · 4:50 finalist demos ·
5:20 winners · 5:30 wrap

## Sponsor plan (build in this order; stop when time runs out)
| # | Sponsor | Job in the app | Needed for | Status |
|---|---|---|---|---|
| 1 | Agent37 | The unattended research worker: takes the idea, browses, works through many steps, returns notes. Its ask-by-ending-the-turn behaviour plus `session_id` continuation is the "CEO steers" mechanism. | Eligibility | **Blocked.** Instance creation returned `402 insufficient_balance` at 3:20 PM. The wallet needs a card added (unlocks $5 free credit). The steer mechanism is documented in the Agent37 docs; not yet run by us. |
| 2 | OpenAI | Structured output: turns the research notes into the packet JSON (`gpt-5.5`) | Eligibility (one sponsor) | Key verified working; model is listed on the account. |
| 3 | Supabase | Stores finished packets and the CEO's decision rows; the page reads them as a feed | Core demo | URL and anon key verified working; table `papers` exists. |
| 4 | Monid | Tool access for the agent's search | Bonus | Not tried. |
| 5 | InstaCloud | Hosts the page, giving a live link | Bonus | Not tried. |

"Verified working" means an authenticated read returned HTTP 200 at about 3:15 PM. For what the
pipeline itself has run, see the status line in the README.

## Only you can do these
- [ ] Add a card to the Agent37 wallet, then run `python3 -m agent.provision`
- [ ] Decide which project is submitted
- [ ] Make a repo public or deploy a live link (needs your approval per action)
- [ ] Record the demo video

## What the pitch must answer
- **Workflow replaced:** the founder's first weeks of admin: working out what a new company
  legally and operationally has to do, in what order, and drafting it.
- **How it works:** idea in, audited launch packet and decision queue out, no human step until
  the decisions.
- **Time saved:** measure before stating a number.
- **Who buys it:** see `SCOPE.md` (hypotheses, none validated).

## Honest limits to state on stage
- It drafts and lists. It does not file, pay, send or sign.
- Not legal, tax or financial advice.
- The audit checks that a source link resolves, not that the page supports the claim.
- Without an Agent37 instance the research step has no browsing, and the packet says so.

## Ask at kickoff
- Judging criteria: ______
- Team size, solo entry allowed: ______
- Prior work / pre-written code allowed: ______
- How the $100 OpenAI credits are delivered: ______
