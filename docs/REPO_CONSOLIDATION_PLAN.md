# Repo consolidation plan: BPN digests

**Status:** Proposed. Drafted 2026-04-18. To be executed next week after
Monday's first Meeting Digest send.

## The decision

Merge `jongeeting/Meeting-agendas-` and `jongeeting/development_digest`
into a single repo. Products remain distinct; codebases share
infrastructure.

## Why merge

1. **Shared data layer.** Meeting-agendas already reads BPN Postgres via
   `bpn_upcoming_events.py`. Development Digest still hits CARTO API
   directly. Merging lets Development Digest switch to BPN Postgres — a
   strict upgrade: faster, enriched parcel data (neighborhood, zoning,
   owner already joined), MEP classification flag, no CARTO rate limits.

2. **Shared formatters.** Both products render addresses, BPN parcel-page
   links, neighborhood grouping, markdown output. Deduplicate.

3. **Product family coherence.** Both are "BPN weekly digests." Readers
   see one brand. Code structure should reflect that.

4. **Substack migration.** Both products are landing on Substack.
   Deployment and scheduling should be unified.

5. **Small scope.** Combined ~2,500 lines of Python. Not big enough to
   warrant two repos.

## When

**Not before Monday 2026-04-20** — Meeting Agendas first send is that
morning. No structural changes until that's out the door.

**Target window:** Mon 2026-04-21 evening through Thu 2026-04-23. This
gives Friday's first Development Digest send (2026-04-24) the new repo
structure.

## Target structure

```
bpn-digests/                         # rename development_digest OR new repo
├── shared/
│   ├── bpn_queries.py              # all BPN Postgres queries (ZBA, sheriff, permits, transfers)
│   ├── bpn_links.py                # parcel-page URL helpers
│   ├── markdown_renderer.py        # shared output formatting + template chunks
│   ├── summarizer.py               # Claude integration (from Meeting-agendas/shared)
│   ├── geocoding.py                # AIS geocoder (from Meeting-agendas)
│   └── unit_counting.py            # unit-count parsing utilities
├── development_digest/              # Friday free product
│   ├── generate.py                 # adapted from generate_digest.py
│   ├── template.py                 # digest structure + copy
│   └── README.md
├── meeting_agendas/                 # Monday paid product
│   ├── generate.py                 # adapted from weekly_digest.py
│   ├── scrapers/                   # phila_gov, phdc, etc.
│   ├── monitors/                   # rco_monitor, official_meetings_monitor
│   └── README.md
├── samples/                         # generated digest archives
│   ├── development_digest/         # current digests/ dir contents
│   └── meeting_agendas/
├── .github/workflows/
│   └── digests.yml                 # cron for both sends
├── requirements.txt                 # merged
├── pyproject.toml                   # configure ruff, pytest
├── .env.example                    # all required env vars
└── README.md                        # top-level overview, points to product READMEs
```

## Migration plan

### Phase 0: Decisions (pre-merge)

- [ ] **Choose repo name.** Options:
  - Rename `development_digest` → `bpn-digests` (preserves git history +
    the 9 existing sample digests)
  - Create new `bpn-digests` repo fresh
  - Rename `Meeting-agendas-` instead
  - **Recommended:** rename `development_digest` — it's the larger of the
    two and has more historical output to preserve.
- [ ] **Confirm public vs private.** Dev Digest repo is currently public.
  Meeting Agendas currently public. Stay public? Private + publish
  sample digests separately?
- [ ] **Branch protection / review rules.** Decide whether merges need
  Brandon review.

### Phase 1: Prep

- [ ] Create `bpn-digests` structure as a new branch on the chosen repo
- [ ] Move existing code into new layout without behavior changes
- [ ] Import path updates so both products still run
- [ ] Requirements + pyproject.toml consolidation (resolve version diffs,
  pick single versions for `requests`, `anthropic`, etc.)
- [ ] Unified `.env.example` with all vars: `ANTHROPIC_API_KEY`,
  `BPN_POSTGRES`, `GMAIL_*`, anything Substack needs

### Phase 2: Dev Digest migration to BPN Postgres

**This is where the real value lands.**

Current Dev Digest fetches permits + variances from CARTO API via HTTP.
Switch to `shared/bpn_queries.py` which reads from BPN's enriched
`parcel_event` table.

- [ ] Write `shared/bpn_queries.fetch_recent_permits(days_back, ...)`
  mirroring existing CARTO query behavior
- [ ] Write `shared/bpn_queries.fetch_recent_variances(days_back)` same
- [ ] Side-by-side test: run new query + old CARTO query for the same
  date window, diff the outputs. Expected: identical row counts (or
  BPN version should be superset). Investigate any drift.
- [ ] Swap `development_digest/generate.py` to use new queries
- [ ] Keep `digests/2026-04-*` archive untouched for visual reference

### Phase 3: Shared formatters

- [ ] Extract markdown rendering from both products into
  `shared/markdown_renderer.py`
- [ ] Standardize: address format, unit-count prefix, BPN link format,
  neighborhood grouping
- [ ] Both products call the same helpers

### Phase 4: Scheduling

- [ ] `.github/workflows/digests.yml` — cron runs both sends on schedule:
  - Meeting Agendas: Monday 6am ET
  - Development Digest: Friday 2pm ET (or whatever Jon picks)
- [ ] Workflow outputs markdown artifacts to the repo
- [ ] Jon reviews artifact, pastes into Substack
- [ ] (Later: Substack API auto-post if viable)

### Phase 5: Deprecations

- [ ] Delete `buttondown_integration.py` (superseded by Substack decision)
- [ ] Update `PRODUCT_STRATEGY.md` to reflect current tier decisions
  (Dev = free Friday, Meeting = paid Monday)
- [ ] Update READMEs

## Risks

1. **Monday send breakage.** Mitigation: no structural changes before
   Monday. Current Meeting-agendas PR #1 can merge as-is.

2. **CARTO vs BPN Postgres drift.** If BPN pipeline has different field
   mappings than CARTO, Dev Digest output could shift. Mitigation:
   Phase 2 side-by-side diff before cutover.

3. **Import path changes break existing scripts.** Mitigation: keep
   top-level entry-point scripts (generate_digest.py, weekly_digest.py)
   as thin shims that import from new locations for one release cycle.

4. **Brandon / Jon need to update local clones.** Mitigation: clear
   README update with "if you have a local clone of either old repo,
   here's how to point at the new one."

## What this doesn't change

- Substack as the publication platform (both products)
- Manual paste workflow for now (direct-post API is Phase 6+)
- Product tiering (Dev = free, Meeting = $15+)
- Send cadence (Dev = Friday 7-day lookback, Meeting = Monday 7-day forward)
- BPN map integration (all address links go to /parcel/{opa})
- The existing Meeting-agendas work shipping Monday — that's frozen

## Decision points for Jon + Brandon

Before executing:
1. Rename `development_digest` or create new `bpn-digests`? (rec: rename)
2. Public or private? (current: both public)
3. Who owns the GitHub Actions scheduled runs — a service account or
   Jon's token? Current tokens need the right scopes.
4. Should samples/ dir ship in the repo or live on Substack only?
   (rec: keep samples/ for git-blame-style history of content evolution)

## Success criteria

- Both products ship on their regular cadence with no data loss
- CI passes on all PRs (once BPN Actions billing unblocks)
- Code in `shared/` is used by both products (not duplicated)
- One `.env.example` covers both products
- Reader sees consistent voice, format, and BPN links across both
  digests
