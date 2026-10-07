# Hackathon requirements

"Build an Agent" Hackathon, Corgi Cafe (office area), 9 Claude Ln, San Francisco, 7 Oct 2026.
Source: the event page, https://luma.com/b54ojqhl. Rules copied from
`../OpenMath/docs/REQUIREMENTS.md`. Judging criteria are announced at kickoff and are NOT
published; fill in the section at the bottom when known.

This project is the fallback entry if OpenMath does not land. Only one gets submitted.

## Hard requirements
- [x] Uses Agent37 Cloud APIs (mandatory for prize eligibility)
- [x] Uses at least one sponsor in the app: OpenAI, Supabase and Monid are used; InstaCloud is not
- [ ] Submitted by 4:40 PM with:
  - [ ] team members
  - [ ] the workflow replaced
  - [ ] demo video link
  - [ ] sponsor integrations used
  - [ ] live project or repo link (judges must open it without requesting access)
  - [ ] at most five files, 10 MB each
- [x] A public repo: https://github.com/Elmdin/start (opens without login, checked 3:25 PM)

## Theme
"What's the workflow you never want to do again?" They want agents you can sell.
Finalists show: what they replaced, how the agent works, how much time it saves.

## Schedule
2:00 doors · 2:20 kickoff · 2:30 build · 4:40 submissions close · 4:50 finalist demos ·
5:20 winners · 5:30 wrap

## Sponsor plan (build in this order; stop when time runs out)
| # | Sponsor | Job in the app | Needed for | Status (7 Oct, about 3:30 PM) |
|---|---|---|---|---|
| 1 | Agent37 | The unattended research worker: takes the idea, browses, works through many steps, returns cited notes. Also reworks the plan when the founder's decisions are sent back. | Eligibility | **Run.** Instance created with `POST /v1/instances`, health polled, three research turns completed through `POST /v1/responses` (measured 194 s, 253 s, and 447 s for the steer rework). |
| 2 | OpenAI | Structured output: turns the research notes into the packet JSON (`gpt-5.5`, strict JSON schema) | Eligibility (one sponsor) | **Run.** Four packets produced. |
| 3 | Supabase | Stores packets, the CEO's decisions and page requests; the page reads and writes the feed; the worker reads decisions and requests back | Core demo | **Run.** Rows written and read by both the worker and the page (existing `papers` table). |
| 4 | Monid | Live web search for the agent: regulations, investors, competitors, passed in as leads | Bonus | **Run.** Keenable search endpoint through the Monid CLI; 15 results fed into one full run. |
| 5 | InstaCloud | Would host the page as a live link | Bonus | Not tried. The repo link is the submission link. |

"Run" means we ran it ourselves today and saw the result. See the README status line.

## Only you can do these
- [x] Agent37 wallet funded; instance created with `python3 -m agent.provision`
- [ ] Decide which project is submitted
- [ ] Make a repo public or deploy a live link (needs your approval per action)
- [ ] Record the demo video

## What the pitch must answer
- **Workflow replaced:** the founder's first weeks of admin: working out what a new company
  legally and operationally has to do, in what order, and drafting it.
- **How it works:** idea in, audited launch packet and decision queue out, no human step until
  the decisions.
- **Time saved:** the agent's side is measured (about 3 to 4 minutes per new packet and about 7 for a rework, shown on the page). We have NOT measured how long a founder takes by hand, so state no ratio.
- **Who buys it:** see `SCOPE.md` (hypotheses, none validated).

## Honest limits to state on stage
- It drafts and lists. It does not file, pay, send or sign.
- Not legal, tax or financial advice.
- The audit checks that a source link resolves, not that the page supports the claim.
- Without an Agent37 instance the research step has no browsing, and the packet says so.
- Solo entry. Judging criteria given at kickoff: originality, business use case, working prototype, user experience.

## Ask at kickoff
- Judging criteria: ______
- Team size, solo entry allowed: ______
- Prior work / pre-written code allowed: ______
- How the $100 OpenAI credits are delivered: ______
