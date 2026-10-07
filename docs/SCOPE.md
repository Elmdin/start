# Scope (7 Oct 2026)

Fallback entry for the "Build an Agent" hackathon in case OpenMath does not land.
Hackathon rules are in `REQUIREMENTS.md`.

## The full vision (not what we build today)
You have an idea. The agent takes care of everything around the business: formation, legal and
compliance, funding and investors, hiring, payroll, audits, documentation, marketing. The founder
steers as CEO: they make decisions, they do not do the admin.

That is a company-sized product. None of it exists yet.

## What is scoped for today: one slice
**Idea in -> launch packet + decision queue out, unattended.**

The packet contains:
- [ ] Stage roadmap; every task assigned to one of: agent / CEO / professional
- [ ] Compliance checklist, each item with a source URL
- [ ] First hires, by stage
- [ ] Funding targets, each with a source URL
- [ ] Drafted documents (text only)
- [ ] A queue of only the decisions the CEO must make, each with options and a recommendation

### The deterministic audit (code, not the model)
- A claim labelled "sourced" keeps that label only if its URL is http(s) and resolves.
  Missing or dead URL -> downgraded to "unverified".
- Workload is counted, not estimated: how many tasks went to the agent, the CEO, a professional.
- Every decision must have at least two options, and the recommendation must be one of them.
- A packet that fails validation is not saved.

### What we will NOT claim
- That it files, pays, sends or signs anything. It drafts and lists. Nothing leaves the machine
  except the packet row written to Supabase.
- That it gives legal, tax or financial advice. Items needing a lawyer or accountant are assigned
  to "professional".
- That a resolving URL proves the claim. The audit checks the link works, not that the page says
  what the model says it says.
- That it replaces Stripe Atlas, Carta, Gusto or anyone below. It does not execute their step.
- Any time-saved number until we have measured one.
- That it works for any jurisdiction or sector. Not tested beyond what is listed under status in
  the README.

## Existing players (the space is crowded)
Found by web search on 7 Oct 2026. Descriptions are from search-result summaries of comparison
sites and vendor pages; **we did not open and read each vendor's own site.** No prices or
customer numbers are repeated here because we did not verify them.

| Area | Name | What it does | Where we read it |
|---|---|---|---|
| Incorporation | Stripe Atlas | One-time formation of Delaware C corps and LLCs, with EIN and 83(b) filing | https://www.rho.co/blog/stripe-atlas-vs-firstbase |
| Incorporation | Clerky | Legal document platform; forms Delaware corporations | https://www.rho.co/blog/clerky-alternatives |
| Incorporation + ops | Firstbase | Formation as entry point to a subscription stack: mail, compliance filings, bookkeeping, tax | https://www.rho.co/blog/stripe-atlas-vs-firstbase |
| Cap table | Carta | Cap table, SAFE issuance, 409A valuations | https://carta.com/carta-vs-angellist/ |
| Cap table / fundraising | AngelList | Cap table for US companies, tied to its syndicate and fund infrastructure | https://qubit.capital/blog/angellist-alternatives |
| Payroll / HR | Gusto | Payroll-first platform for small businesses | https://www.rippling.com/blog/rippling-vs-gusto-hr-payroll-comparison |
| Payroll / HR / IT | Rippling | All-in-one: HR, payroll, IT management, finance | https://www.rippling.com/blog/rippling-vs-gusto-hr-payroll-comparison |
| Global hiring | Deel | Employer-of-record hiring and localized payroll across countries | https://www.deel.com/llm-info |
| Security compliance | Vanta | Automates evidence collection and audit prep for SOC 2 and related frameworks | https://scytale.ai/resources/drata-vs-vanta/ |
| Security compliance | Drata | Same category as Vanta; positioned for multi-framework setups | https://scytale.ai/resources/drata-vs-vanta/ |
| "AI co-founder" (formation) | Zenind | US formation and compliance service using AI co-founder framing; says it is not a replacement for an attorney or accountant | https://www.zenind.com/help/post/what-is-an-ai-co-founder-for-u-s-entrepreneurs-how-zenind-can-support-formation-and-compliance |
| "AI co-founder" (multi-agent) | Cofounder (General Intelligence Company) | Multi-agent workspace, one agent per department | https://www.agentmail.to/blog/how-cofounder-gives-every-ai-agent-its-own-inbox |
| Autonomous founders | Feltsense | Reported seed round to build agents that found and run companies themselves | https://pulse2.com/feltsense-5-1-million-seed-funding-raised-to-build-autonomous-agentic-founders-to-create-new-companies |
| "AI chief of staff" | Yutori, Nebula (named in coverage) | Category for founders and executives; mostly calendar, email, status work | https://www.thedeepview.com/articles/goodbye-virtual-assistant-hello-ai-chief-of-staff |

Also seen in search, not verified at all: Foundrs (UK "AI co-founder" for formation), Locus
Founder, and a hackathon project called Agent Startup Box (idea validation and pitch material).
Assume more exist that we did not find.

### Honest positioning
Each tool above executes **one step**, and assumes you already know which step to ask for.
A first-time founder's problem is earlier: they do not know what the steps are, in what order,
or which ones need a professional.

This project is the layer above: it works out what must be done, sequences it, drafts what can be
drafted, and hands the founder only decisions. In a full version each task would hand off to one
of the tools above. Today it hands off to nobody: it does not file, pay, send, or give legal advice.

The "AI co-founder" products are the closest neighbours. What we can point to as different, in
code that exists: the source audit that downgrades unsupported claims, the counted workload split,
and the decision queue. We have not used those products, so we do not claim they lack these.

## Decisions (ADR style)

### A. Scope: broad dashboard vs. one deep slice
- **Option 1, broad:** a multi-department dashboard (legal, finance, HR, marketing tabs), each
  with a thin agent.
- **Option 2, one slice:** idea -> audited launch packet + decision queue.
- **Chosen: one slice.** The broad dashboard loses because nothing in it can be checked or
  finished in about 90 minutes: every tab would be a mock, and "Only what's real" rules out mocks.
  The slice runs end to end and has an audit a judge can watch fail a bad source.
- Cost: the demo shows one stage of the vision, not the vision.

### B. Storage: reuse OpenMath's `papers` table vs. a new table
- **Option 1, reuse:** write rows to the existing Supabase `papers` table (`title`, `spec jsonb`),
  with `spec.kind = "startup-packet"` (and `"startup-decision"` for CEO choices).
- **Option 2, new table:** a dedicated table with typed columns.
- **Chosen today: reuse.** The new table loses on setup: it needs a manual run in the Supabase SQL
  editor during the build window. The existing table is already there and its URL and key were
  verified working at about 3:15 PM.
- Cost: two projects share one table and must filter on `spec.kind`; anon insert is open, so the
  page must treat every row as untrusted. The dedicated table SQL is in `supabase/schema.sql`
  for later.

## Demo script (2 minutes)
1. The problem: a founder has an idea and a list of things they do not know they have to do.
   A crowded field of tools each does one step; none tells you the steps.
2. Type one idea. Run the worker live, untouched.
3. Open the feed page. Show the roadmap with the agent / CEO / professional split and the
   counted workload.
4. Show the audit: sourced vs. unverified, and how many "sourced" claims were downgraded.
5. Click one decision in the queue. That is the only thing the CEO did.
6. One line: the tools that execute each step exist; working out the steps was still manual.

Say out loud what did not run (see the README status line).

## Who would pay (hypotheses, none validated)
- First-time founders before they can afford a lawyer or a chief of staff
- Accelerators and incubators, as a per-cohort licence
- Formation and startup-banking providers, as the front door that routes founders to them
- Startup law firms, as intake that arrives pre-sorted

No customer has been asked yet.
