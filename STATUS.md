# Status — StudyOS Thesis-Finder

> **This is the only continuously updated file.** Here we collect progress, blockers, difficulties, and decisions. The stable overall plan is in [MASTERPLAN.md](MASTERPLAN.md).
>
> **Convention:** When working on a task, change its status here, note difficulties, and add a dated line to the log below. Do not edit the Masterplan.

**Last update:** 2026-07-05 — Independent 1.0-readiness review completed and actioned:
Phase 5 is now fully **scoped** (Tasks V–AA, MASTERPLAN.md §9), the Phase 4 GO verdict is
flagged **provisional** (hard-faculty blindness gap, see below), and `docs/thesis-report/03`
and `04` were corrected to match the current state instead of a stale 2026-07-03 snapshot.
Before that: Task M2 done and committed, closing out the Task M (Gehler feedback) plan
(M1, M2, M3 all done); Task L merged (BW company backbone extended to all 7 Tübingen
faculties + ZITh via a 13-field employment taxonomy). Working tree clean. **Next up when
work resumes:** Task V (blind Theology run, ~20 min, repairs the Phase 4 evidentiary gap),
then Task W (scope-erosion experiment — the single highest-value remaining task). See
"Current phase" below for the full, exact re-entry summary.

---

## Current phase

> ⏸ **Project paused here as of 2026-07-05, after the independent 1.0-readiness review.**
> No further work is planned on this branch until further notice. This section is written
> to be a precise, self-contained re-entry point — read it first when work resumes, before
> touching anything else.
>
> **Exact state:** `feat/no-db-universal-skill`, working tree clean, ahead of
> `origin/feat/no-db-universal-skill` (not yet pushed to the remote). `pytest -q` → 29
> passed / 8 skipped; `python3 scripts/build_skill_release.py` builds cleanly. Phases 1–4
> are done. Phase 4's go/no-go verdict is **GO, but flagged provisional** (see below).
> Phase 5 is now fully **scoped** (Tasks V–AA, MASTERPLAN.md §9) but only Task L
> (company-backbone taxonomy) is actually done.
>
> **Task M1 is done** (upfront framing message in `thesis-finder`, committed 2026-07-05).
> **Task M3 is done** (paper-first gate in `draft-thesis-contact`, committed 2026-07-05).
> **Task M2 is done** (recommend & drill-down step in `thesis-finder`, committed 2026-07-05).
> **The Task M (Gehler feedback) plan is complete** — see
> [`findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md`](findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md)
> for the full plan (now committed; it was briefly untracked, fixed in this pass). The
> professor-input coverage-caveat item (M4) and the example-walkthrough/example-prompts
> idea were considered and explicitly dropped, not folded into M1-M3. No open task remains
> from this plan. **Caveat added by the 2026-07-05 review:** M1–M3 have not been
> live-exercised since landing — no runbook re-run confirms the new flow works end-to-end
> in practice. Folded into Task AA's hygiene sweep rather than given its own task.
>
> **What happened 2026-07-05 — the independent 1.0-readiness review:** a from-scratch,
> deliberately skeptical review assessed the project for both a thesis committee and real
> students (full text:
> [`findings/no_db_universal_skill/2026-07-05-fable-1.0-readiness-review.md`](findings/no_db_universal_skill/2026-07-05-fable-1.0-readiness-review.md)).
> Its findings, now the authoritative source for what's left before 1.0:
>
> 1. **The Phase 4 GO verdict is evidentially weaker than its write-up suggests.** The two
>    hard-faculty recall numbers that flipped it to GO (Humanities 100%, Law 80%) are not
>    clean blind measurements — Humanities is a transparent re-score by a session that was
>    explicitly un-blind on that faculty; the Law re-run's session had already read the
>    document naming the missed chair (Remmert) and the exact fix that flips her. Every
>    genuinely blind hard-faculty run to date (Humanities 60%, Law 60%) landed below the
>    80% bar. **Not reversed** — Task U's underlying §5 enrich-before-exclude skill fix is
>    real and independently corroborated (Droege/Seiler stayed correctly excluded under the
>    same fix) — but the verdict is now **provisional** pending one clean blind run. New
>    **Task V**: blind Theology run (ground truth exists, never opened mid-run — the last
>    uncontaminated hard-faculty data point available).
> 2. **The project's central scientific claim is still asserted, not tested.** The
>    "narrow scope beats plain Claude; breadth erodes the advantage" argument
>    (`docs/thesis-report/04-open-work/2026-07-02-ideen-domi.md`, point 6; formalized in
>    `findings/gesamtplan-2026-07-02.md` §3 Idee 6) is probably right in conclusion but its
>    SLLN framing over-claims — a curated foreign backbone would not dilute Tübingen's
>    curation density; only an uncurated expansion trivially converges to baseline. The
>    defensible form is a dose-response claim (advantage ∝ curated local-knowledge
>    density), and the gesamtplan's own scope-erosion experiment (§6 T3) to test it has
>    never been run. New **Task W** — the review's single highest-value remaining task.
> 3. **Self-scoring, company-GT circularity, and single-agent authorship** remain open
>    methodological caveats the project already named (STATUS/scorecard) but never
>    mitigated. New **Task X** (independent re-scoring of a sample) and **Task Y**
>    (non-circular company ground truth).
> 4. **Product readiness gap:** nobody outside the project has run the shipped release
>    artifact; the one informal external test (Gehler) had no protocol or ground truth.
>    Design-Entscheidungen.md TODOs 1 and 2 (both "Hoch/Ja") remain untouched. New
>    **Task Z**: a protocolled 3–5-student external test plus one distribution channel.
> 5. **Small, real, unfixed defects** (review is read-only by design — nothing was
>    patched): `find-recent-papers`' shipped paper index conflates two different people
>    both named "Matthias Hein" (radar/superconductivity papers filed under Tübingen's ML
>    professor); `build-student-profile/references/tuebingen-degree-programs.md` is
>    CS-only but used/titled as if university-wide; `find-company-thesis-options`'s
>    frontmatter claims "any discipline" against its own routing table's honest
>    exceptions; portability claims vs. the hardcoded `~/.claude/` session path; two
>    recorded backbone 404s with no link-audit process. Bundled into new **Task AA**.
>
> The Phase 5 task table (MASTERPLAN.md §9, Tasks V–AA) is the actionable form of this
> review. `docs/thesis-report/03-hardening-and-evaluation/README.md` and
> `04-open-work/README.md` were corrected in this same pass — they previously stated a
> stale 2026-07-03 snapshot (Task S "not started", recall bar "not yet met") that
> contradicted the current GO/Task-S-done state; both now link to the review and state
> the provisional-GO caveat directly. **Recommended first move on re-entry: Task V**, then
> **Task W**.

**Phase 3 — Orchestration & Distribution: COMPLETE.** Backbone maintenance, entry-point skill,
distribution artifacts, and smoke test are all done. Branch `feat/no-db-universal-skill` is
package-ready; beta-ready after independent live test by another person/group.

**Phase 4 — Core hardening: DONE.** Tracks 1–4 of the optimization roadmap are complete
(recall/precision fixes, steering proof, robustness, output quality). The explicit go/no-go
on roadmap §4's "core is done" bar is **GO** (flipped 2026-07-04, Task U): all 5 criteria are
met. The recall criterion — ≥80% across ≥6 faculties incl. ≥1 hard faculty — cleared once
Task T fixed the eval-protocol (persona-construction) gap and Task U fixed a genuine skill
gap (§5 "enrich before excluding" a candidate whose dense multi-strand title buries a
core-interest term). All 6 measured faculties now clear 80% (CS 100%, Medicine ≥83%,
Psychology ≥83%, WiSo ≥83%, Humanities 100%, Law 80%), 2 of them hard.
Decision doc: [2026-07-03-core-done-go-no-go.md](findings/no_db_universal_skill/2026-07-03-core-done-go-no-go.md).
**Flagged provisional 2026-07-05** — see "Current phase" above and the
[independent review](findings/no_db_universal_skill/2026-07-05-fable-1.0-readiness-review.md):
the Humanities and Law numbers behind this verdict are not clean blind measurements: Task V
(blind Theology run) is the named repair.

**Phase 5 — Task L done, merged 2026-07-04; fully scoped 2026-07-05.** Task U was the last
task on the critical path to GO; candidates discussed (Theology blind run, independent
external validation, the scope-erosion experiment, company-backbone taxonomy) — Domi picked
**company-backbone taxonomy (Task L)**, run in worktree `study-os-thesis-taskL` (branch
`task/L-company-backbone`). Extended `bw-company-backbone.md` from a MINT-heavy ~90-entry
list to a 99-entry list covering all 13 employment fields derived from Uni Tübingen's actual
faculty structure (not the CS-only reference file the task brief originally pointed at — see
the findings doc §0 for that correction). Merged fast-forward into
`feat/no-db-universal-skill`; worktree and branch removed. Full write-up:
[2026-07-04-taskL-taxonomy-and-gap-analysis.md](findings/no_db_universal_skill/2026-07-04-taskL-taxonomy-and-gap-analysis.md).
The other three candidates named that day (Theology blind run, independent external
validation, scope-erosion experiment) are no longer just "undecided" — the 2026-07-05
independent review formally scoped them (plus two new tasks, independent scoring and
non-circular company GT) as **Tasks V–AA** in MASTERPLAN.md §9. See "Current phase" above
for the full task table and evidence.

Phase 1 is **complete** with live validation (all 4 faculties ≥70% live recall on fixture-based
evaluation; gate passed 2026-06-28). Phase 1 build plan: [2026-06-26-build-plan.md](findings/no_db_universal_skill/2026-06-26-build-plan.md).

Phase 2 decisions: [2026-06-28-phase2-company-decisions.md](findings/no_db_universal_skill/2026-06-28-phase2-company-decisions.md)
· Phase 2 build plan: [2026-06-28-phase2-build-plan.md](findings/no_db_universal_skill/2026-06-28-phase2-build-plan.md)

Phase 3 build plan: [2026-06-28-phase3-build-plan.md](findings/no_db_universal_skill/2026-06-28-phase3-build-plan.md)
· Phase 3 smoke test: [2026-06-28-phase3-smoke-test.md](findings/no_db_universal_skill/2026-06-28-phase3-smoke-test.md)

---

## Task status

Legend: ⬜ open · 🟨 in progress · ✅ done · ⛔ blocked

| Task | Step | Status | Owner | Notes / difficulties |
|---|---|---|---|---|
| A | Conversation discipline in `build-student-profile` | ✅ | Domi | One-question rule + precise-answer instruction + no-search gate added to SKILL.md. |
| B | Faculty backbone reference (Tübingen listing URLs) | ✅ | Domi | All 7 faculties + ZITh covered; ≥1 official listing URL each, 6 spot-checked live. |
| C | Search-strategy reference (profile → queries) | ✅ | Domi | Created `search-strategy.md`: profile→query-variable mapping, 18 query skeletons, two-pass strategy, quality filters, dedup rules, no-go exclusion, faculty routing table, two worked examples (Ethical AI/Education + Clinical Neuroscience). |
| D | Rework `find-university-chairs` into universal discovery skill | ✅ | Domi | Rewrote SKILL.md: faculty-agnostic description, 6-dimension profile gate, faculty routing via search-strategy.md §2, two-pass search (backbone crawl + live enrichment), quality filters/dedup/no-go exclusion, MAP output grouped by interest dimension with pros/cons, dated evidence, conversation starter, coverage caveat. No seed-list dependency. |
| E | Retire DB assets (match-thesis-advisors, openalex index, seed data → eval) | ✅ | Domi | Deleted match-thesis-advisors + update-openalex-paper-index; moved CS seed data to skills/tests/eval_ground_truth/cs_seed/; fixed seed-path refs in find-recent-papers + design-agent-skill. grep confirms no runtime DB deps remain. |
| F | Eval ground truth for 3–4 faculties + metric | ✅ | Domi | 4 faculties: CS (cs_seed/), Medicine (6 chairs), Psychology (6 chairs), WiSo (7 chairs). README defines recall metric + ≥70% target. |
| G | Wire discovery into Max's multiturn harness (skill vs. baseline) | ✅ | Domi | Harness already existed in branch. Added medicine-discovery scenario (skill + baseline arms), neuro-student persona, scripted fixtures, coverage/relevance/structure scoring, `--discovery-comparison` CLI flag. 12/12 tests pass; fixture run: skill 83% recall vs. 0% baseline. |
| H | Run eval, measure coverage & skill-vs-baseline delta, document | ✅ | Domi | **Fixture-mode only.** Mean skill recall 96%, baseline 0% — but both arms were hand-scripted, so the gap is circular and does NOT validate live behavior. See Task I. |
| I | **Live validation** — real recall + real baseline with live WebSearch | ✅ | Domi | **GREEN (after I-fix).** Initial run AMBER: Psych 67%, CS 60%. Fixed: (1) PI attribution discipline (2e verification step); (2) MPI-IS/ELLIS explicit Pass-1 crawl leg. Re-validated Psych (primary 100%, strict 83%) and CS (primary 100%, strict 100%) live. All 4 faculties ≥70%. Results: `findings/no_db_universal_skill/2026-06-28-I-fix-revalidation.md`. |

**Gate Phase 1 → 2 (REVISED):** skill runs end-to-end with no DB ✅ · ground
truth for ≥3 faculties ✅ · harness plumbing works ✅ · **live** coverage ≥70%
AND a meaningful live margin over plain Claude ✅ **GREEN** (Task I-fix: all 4
faculties ≥70% primary and strict; Psych 100%/83%, CS 100%/100%, Med 100%/83%,
WiSo 100%/100%; real +65pp over baseline confirmed in Task I).

### Phase 2 — Company discovery

| Task | Step | Status | Owner | Notes / difficulties |
|---|---|---|---|---|
| 2-A | BW company backbone reference (~100–130 entries, Cyber Valley + manual BW R&D additions) | ✅ | Domi | 107 entries across 7 sectors; 10 URLs spot-checked live; `bw-company-backbone.md` committed. |
| 2-B | Company search strategy (profile → backbone filter + live enrichment queries) | ✅ | Domi | `company-search-strategy.md`: interest→tag mapping, Pass 1 (backbone filter), Pass 2 (site: enrichment), query skeletons, quality filters, no-go exclusion, 2 worked examples. |
| 2-C | Build `find-company-thesis-options` skill | ✅ | Domi | `SKILL.md`: 8-step workflow, backbone filter → live enrichment, output schema from decisions doc, evidence rules (no invented contacts), no-go guard, coverage caveat required. |
| 2-D | Eval ground truth for companies (3 profiles × 5–8 companies each) | ✅ | Domi | 3 profiles × 5–6 verified companies each; confirmation URLs live-verified; README defines recall + thesis-signal metrics. `company_seed/` committed. |
| 2-E | Live validation (real recall + baseline, ≥70% target per profile) | ✅ | Domi | **GREEN.** 100% recall all 3 profiles (vs 74% baseline mean); +26pp mean delta; 94% thesis-signal accuracy. Caveats: circular recall (GT built from same backbone), weak C1 delta (+17pp), Aleph Alpha stale post-merger. Results: `2026-06-28-phase2-live-eval-results.md`. |

**Gate Phase 2 → 3:** skill runs end-to-end ✅ · ground truth for ≥3 profiles ✅ · live recall ≥70% all profiles ✅ · meaningful live margin over plain Claude ✅ **GREEN** (Task 2-E: all 3 profiles 100%; +26pp mean over baseline; no DB dependency confirmed).

### Phase 3 — Orchestration & Distribution

| Task | Step | Status | Owner | Notes / difficulties |
|---|---|---|---|---|
| 3-A | Backbone maintenance (Aleph Alpha fix + §5 expansion) | ✅ | Domi | Aleph Alpha → Cohere entry updated; §5 expanded to 7 entries (added IONOS, Haufe, GFT, Schwarz IT). |
| 3-B | Create `thesis-finder/SKILL.md` entry point | ✅ | Domi | Thin orchestrator: profile check → track question → routes to find-university-chairs / find-company-thesis-options / both; offers draft-thesis-contact as next step. |
| 3-C | Update `AGENTS.md` + `README.md` for distribution | ✅ | Domi | AGENTS.md: new student workflow, thesis-finder + find-company-thesis-options documented, retired skills annotated. README: student-facing top section (≤200 words) added. |
| 3-D | End-to-end smoke test + STATUS.md update | ✅ | Domi | C1 trace passes all steps; no dead references found. Full trace in `2026-06-28-phase3-smoke-test.md`. |

**Gate Phase 3 (all criteria):**
- Backbone: Aleph Alpha corrected; §5 ≥6 entries ✅
- `thesis-finder/SKILL.md` routes correctly for all three student choices ✅
- `AGENTS.md` reflects current skill set (no retired skills in active workflow) ✅
- `README.md` has student-readable top section ✅
- Smoke test passes with no dead references ✅
- STATUS.md closed with gate verdict ✅

**Overall Phase 3 gate: COHERENT & PACKAGE-READY.** Branch `feat/no-db-universal-skill` is in a
coherent state with all orchestration in place; independent live validation pending. *Caveat:*
Company eval exhibits circular recall (ground truth built from same BW backbone as the skill),
and uni eval was initially weaker (Psych/CS issues) before 2e/2f fixes. Real-world validation
by a fresh user or group is recommended before beta release. Post-Phase-3 human actions: hand off
to Fachschaft Informatik, Hennig-GitHub, and Ersti-Heft editors (outside scope of this branch).

### Post-Phase-3 hardening

| Task | Step | Status | Owner | Notes / difficulties |
|---|---|---|---|---|
| J | Canonical six profile dimensions everywhere (cold-start consistency) | ✅ | Domi | Fixed dimension-list mismatch: `build-student-profile/SKILL.md` required "interests, liked/disliked courses, skills, experience, preferred thesis style, no-gos" while thesis-finder and both discovery skills gated on Interests/Methods/Domain/Thesis style/Skills/No-gos. A standalone build-student-profile pass could pass its own gate without satisfying the discovery skills'. Added a canonical definition to `student-profile-schema.md`, corrected workflow step 4 and the Output section in `build-student-profile/SKILL.md`; courses/experience kept as elicitation avenues, not dimensions. `pytest -q` 29 passed/8 skipped; release build OK. |
| Roadmap-J | Lightweight live-eval runbook (see [core-optimization-roadmap.md](findings/no_db_universal_skill/2026-06-28-core-optimization-roadmap.md) Track 1) | ✅ | Domi | **Note:** this is the roadmap's own "Task J", distinct from the "J" row above (letter collision — the roadmap's Task J was never built under that name; a different fix got logged as J first). Relabeled `Roadmap-J`/`Roadmap-K` here to avoid ambiguity. Wrote `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md`: a ~15–20 min checklist to re-validate one faculty live after a skill change (reuse existing persona, no-peeking, skill arm only, score recall+precision, log a one-paragraph entry), vs. the full 4-faculty `2026-06-28-live-validation-protocol.md` written for one-time validation. Not yet exercised — log has no runs. |
| Roadmap-K | Add a precision metric to the eval ground truth | ✅ | Domi | Recall alone rewards over-surfacing. Added "What precision means here" to `skills/tests/eval_ground_truth/README.md`: precision = surfaced options judged relevant / total surfaced options; relevance judged against the MAP's own "Relevance rationale" field, not just ground-truth membership (ground truth isn't exhaustive). No fixed precision target yet — needs a few live runs (via Roadmap-J's runbook) to establish a baseline first. Scoring steps 5–7 added to the "How to score" section. `pytest -q` 29 passed/8 skipped; release build OK. |
| Roadmap-J run 1 | First live exercise of the runbook (`cs` faculty) | ✅ | Domi | Recall 5/5 = 100% (matches Task I-fix, no regression). Precision 9/12 = 75% — first-ever precision data point. 3 noise entries: Butz (domain mismatch, cognitive science), Williamson (weak topical fit / borderline pure-math no-go), and Oh/STAI (relocated to KAIST Feb 2026 but still listed on the live FB-Informatik backbone page — a stale-backbone gap, not a relevance miss). Zell excluded pre-scoring via the hardware/embedded no-go. **Caveat: no-peeking discipline was broken** — the CS ground truth and Task I-fix's named results were read during general task context-gathering before Pass 1 ran; recall is probably still representative (the GT names surfaced organically from the FB-Informatik page) but isn't a blind result. Points to **Track 3 / Task O** (relevance/no-go tightening + strengthen the 2f existence check to catch PI relocations, not just page staleness) as the next track. Full write-up: `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md` log. `pytest -q` and `build_skill_release.py` still green. |
| Task O | Relevance/no-go tightening + affiliation-currency check (Track 3, per Roadmap-J run 1's finding) | ✅ | Domi | Added a "topical justification" quality filter to search-strategy.md §5 (co-location on a faculty page section ≠ relevance; Butz worked example), sharpened §7's pure-math no-go wording (foundational-but-not-proof-only theory work is ambiguous-by-default, kept+flagged), and added a §4.7 affiliation-currency query skeleton + SKILL.md 2f upgrade to catch relocated PIs distinct from the existing recency check. Re-ran the Roadmap-J runbook live for `cs` with the same persona (no-peeking held this time): **recall 5/5 = 100%** (no regression), **precision 10/10 = 100%** (up from 75%) — Butz and Williamson now excluded before reaching the map instead of surfaced-with-caveat, Oh's KAIST relocation caught by the codified 2f check instead of incidental diligence. Small-sample caveat: one faculty, one persona, one run — evidence the known noise is fixed, not proof the filter generalizes. `pytest -q` 29 passed/8 skipped; release build OK. Full write-up: `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md` log (second 2026-07-02 entry). |
| Task P | **Steering proof (Track 3 — "most important for the thesis claim")** | ✅ | Domi | **Steering CONFIRMED (strong).** Ran `cs` live with two students with *inverted* profiles: Persona A (causality + probabilistic/Bayesian ML; no-go **computer vision** + hardware) vs. Persona B (computer vision + representation learning; no-go **heavy Bayesian theory** + hardware). Same faculty, same Pass-1 candidate set (25 groups; the live FB-Informatik page now also exposes a "Vision & Cognition" section). The two option maps are **near-disjoint**: numbered options A={Schölkopf, Brendel, Hennig, Macke, von Luxburg, Hein, Martius}, B={Geiger, Black, Pons-Moll, Kühne, Bethge, Brendel, Lensch, Berens} — intersection only {Brendel, Hein}, and those two are reframed/reranked per profile. Vision chairs top B and are excluded from A; Bayesian chairs top A and are excluded from B — flips in exactly the predicted direction. Conversation starters also fully diverge. Steering is driven by §1 (topic→query) + §5 (topical justification); **honest gap** — the two no-gos ("CV", "heavy Bayesian") are *not* codified rows in §7, so they ran via §7's general rule, not the table (one-line §7 note is a minor follow-up, not fixed here). Caveats: single-agent authored/judged (confirmation-bias risk, mitigated by live-verified per-chair facts); personas built to diverge (proves mechanism *can* steer, not that it steers on subtle personas); one faculty. Outputs: `dist/live-validation/cs-persona-{A,B}-skill.md`. Full write-up: `findings/no_db_universal_skill/2026-07-02-task-p-steering-proof.md`. `pytest -q` 29 passed/8 skipped; release build OK. |
| Task Q | **Hard-faculty ground truth (Track 4 — robustness)** | ✅ (GT authored; blind live run deferred) | Domi | Extended eval ground truth from the 4 easy faculties (Med/Psych/WiSo/CS) to the **structurally harder** ones + one interdisciplinary persona, all built by crawling the official faculty backbone (not a skill run) on 2026-07-02. New files under `skills/tests/eval_ground_truth/`: **`humanities.md`** (Philosophisches Seminar — phil. of mind/metaphysics/cognitive science; hardness = large 3-level faculty, chairs live deep in a Seminar; core GT Sattig/Wong/Corcilius/Schlösser/Döring), **`law.md`** (Öffentliches Recht — constitutional/international law + tech regulation; hardness = dense German chair-title formulas; von Bernstorff/Nettesheim/Finck/Saurer/Remmert), **`theology.md`** (Ev.-Theol. — biblical studies/early-church history; Leuenberger/Kamlah/Tilly/Landmesser/Drecoll/Witt), and **`interdisciplinary.md`** (AI ethics & governance across Law/Humanities-IZEW/Science-ML — Finck + Heesen + Ammicht Quinn + Hardt + Wong; tests routing breadth, not depth). **Task-P caveat #3 confirmed live as a robustness finding:** Ev.-Theol. has several **vacant (N.N.) chairs** incl. Systematic Theology II (Ethik) — for an ethics/systematic persona the relevant chair is unstaffed, so honest discovery should say "no staffed chair for this focus," not misroute; recorded as chair-scarcity, not a steering/skill failure (see `theology.md` Notes). README Files table + a new interdisciplinary routing-metric note updated. **Blind live run deferred by design:** authoring GT this session contaminates a same-session skill run (runbook no-peeking discipline), so the first recall/precision read on a hard faculty is handed to a fresh conversation. `python3 -m pytest -q` and `build_skill_release.py` still green. |
| Track 2 | Backbone audit & repair / weak-web-presence fallback / query-skeleton iteration (roadmap's own "Task L/M/N", see [core-optimization-roadmap.md](findings/no_db_universal_skill/2026-06-28-core-optimization-roadmap.md) Track 2) | ⬜ open | — | Implicitly skipped so far: Task I already showed ≥70% live recall, so the fork in the roadmap's §5 dependency graph ("recall low? → Track 2") never triggered. Not formally closed — the backbone has not been systematically audited for drill-down completeness, and no weak-web-presence fallback (Vorlesungsverzeichnis, Fachschaft lists, institute staff directories) exists yet. Revisit if a future faculty's recall comes in low. |
| Task Q run 1 | First blind hard-faculty live run (`humanities`, Track 4 — robustness) | ✅ | Domi | Recall 3/5 = 60% (Sattig, Wong, Schlösser found; Corcilius, Döring missed) — below the README's 70% target, but root-caused to a persona-construction gap in the eval protocol (the README's one-line sample-interest summary omits `humanities.md`'s "...with an interest in the history of the field" clause), not a skill discovery failure: the live crawl found and evaluated all 5 GT chairs, then correctly excluded 2 per no-gos the incomplete persona implied. Precision 3/3 = 100%, and the run independently re-derived the GT file's own "deliberately excluded, not noise" calls (Grabmayr, Schumski). Backbone drill-down (Faculty→FB5→Seminar) worked correctly first try — the "must descend the department tree" hardness this faculty was chosen to test was not the failure mode. One interfaculty backbone URL 404'd (second data point for Track 2). Output: `dist/live-validation/humanities-skill.md`. Full write-up: `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md` log (2026-07-03 entry). `pytest -q` and `build_skill_release.py` still green. |
| Task R | Edge-case behavior — niche topic with no Tübingen match, shallow/resistant student (does the gate hold?), interdisciplinary routing (Track 4, see roadmap §3) | ✅ | Domi | All 3 edge cases exercised live, all pass. (1) Niche no-match (rocket-engine/aerospace propulsion — Tübingen has no engineering faculty): honest "no strong fit" output, no padding. (2) Shallow/resistant student: 8-turn simulated adversarial interview never triggered a premature `find-university-chairs` call; gate held via `build-student-profile`'s own re-prompting plus `find-university-chairs`'s independent Step 1 re-check. (3) Interdisciplinary routing (`interdisciplinary.md` persona): 5/5 GT anchors surfaced, 3/3 spanned faculties/centers covered (Law/Finck, Humanities-IZEW/Heesen+Ammicht Quinn+Wong, Science-ML/Hardt) — no collapse onto a single discipline. Two small spec gaps found and fixed: `find-university-chairs/SKILL.md` now has an explicit zero-candidates rule; `build-student-profile/SKILL.md` now recommends forced-choice questions for resistant students plus an honest generic-pointer fallback instead of an endless interview loop. Full write-up: `findings/no_db_universal_skill/2026-07-03-task-r-edge-cases.md`. Outputs: `dist/live-validation/{niche-no-match,interdisciplinary}-skill.md`. `pytest -q` and `build_skill_release.py` still green. |
| Task S | Output & interview quality pass — honest pros/cons, concrete conversation starters, dated evidence, caveat presence, interview convergence (Track 4, see roadmap §3) | ✅ | Domi | Reviewed all 5 full discovery transcripts against the 5 criteria. 4/5 criteria pass cleanly (pros/cons, conversation starters, coverage caveat, and — via a live happy-path interview simulation, since none existed — interview convergence: 6 turns, clean, vs. edge case 2's adversarial 8-turn non-convergence). 1 real repeated gap found: cs-skill and wiso-skill (2/5 transcripts) omit the "Dated evidence" field from every option. Fixed with one worked example added to `find-university-chairs/SKILL.md` Step 8 Output section. Full write-up: `findings/no_db_universal_skill/2026-07-03-task-s-output-quality.md`. `pytest -q` and `build_skill_release.py` still green. |
| Eval Scorecard | Aggregate every recall/precision/steering/robustness number to date into one document | ✅ | Domi | Pure aggregation, no new live run. `findings/no_db_universal_skill/2026-07-03-eval-aggregate-scorecard.md`: one table per axis (university recall/precision by faculty, company recall/thesis-signal, steering, robustness), each cell cited to its source. Honest bottom line: the roadmap's "core is done" bar (≥80% recall across ≥6 faculties incl. one hard faculty) is **not yet met** — only 5 faculties have any live number and the one hard faculty tested (Humanities, 60%) is below bar; Task S has zero data. `docs/thesis-report/03-hardening-and-evaluation/README.md` and `04-open-work/README.md` updated to match (Task Q's blind run and Task R are no longer described as pending). |
| §4 Go/No-Go | Explicit go/no-go call on roadmap §4 "core is done" (over existing evidence, no new run) | ✅ | Domi | **Verdict: NO-GO** (narrowly). Scored §4's 5 criteria: steering (Task P), output quality (Task S), edge cases (Task R) all ✅; precision strong but under-sampled (2/5 faculties); **recall bar ❌** — fails on two independent counts: only 5 faculties measured (not ≥6), and no hard faculty has a clean live ≥80% (Humanities 60%, protocol-caveated; Law/Theology unrun). The Humanities miss is root-caused to the eval protocol (personas built from the README's lossy one-line summaries, not the GT files' full sample interest), not a skill defect — the crawl found all 5 GT chairs. Not a GO because (1) precedent: the project was already burned by a premature "gate GREEN" on partial evidence (2026-06-28 CI-hygiene entry); (2) no schedule pressure — Phase 2 (companies) is already GREEN, so nothing waits on this. Names **Task T** (eval-protocol fix + blind re-run Humanities + blind-run Law) as the closeout. Decision doc: `findings/no_db_universal_skill/2026-07-03-core-done-go-no-go.md`. No skill files touched. |
| Task T | Eval-protocol fix + hard-faculty recall closeout (clears §4 criterion 1) | ✅ | Domi | (1) **Protocol fix committed** — runbook steps 2–3 reconciled: personas now built from each GT file's full `Sample interest:` line (grep-extracted, no-peeking carve-out), not the README one-liner. (2) **Humanities corrected re-score: 3/5→5/5 = 100%** (transparent — this conversation is un-blind on Humanities; both misses flip to Include once the dropped "history of the field" + "theory of emotions" clauses are restored → protocol fix validated). (3) **Law blind run: 3/5 = 60% recall, 3/3 = 100% precision.** Discovery found all 5 GT chairs; the 60% is a *downstream filter* miss — **Remmert** was excluded at the §5 topical-justification step from her multi-strand title without Pass-2 enrichment, but her actual focus (*Allgemeine Grundrechtslehren*) is a core constitutional-law/human-rights match → genuine false-negative. **Outcome: NO-GO still stands (transformed).** Original Humanities blocker resolved, but now **5 of 6** faculties clear 80% (Law is the sole miss), so criterion 1's strict per-faculty reading is not yet met. Names **Task U** (§5 enrich-before-exclude fix + Law re-run). Write-up: `findings/no_db_universal_skill/2026-07-03-task-t-recall-closeout.md`. Skill files untouched this task (fix deferred to Task U). |
| Task U | §5 enrich-before-exclude fix + Law re-run (the remaining path to GO) | ✅ | Domi | (1) **Skill fix committed** — added an "Enrich before excluding" row to `search-strategy.md` §5 (symmetric dual of the Butz worked example) + a matching one-liner in `SKILL.md` Step 7: do not exclude a candidate from a title-only reading when its title names a core-interest field amid off-interest strands; run Pass-2 enrichment first. (2) **Law blind re-run: 4/5 = 80% recall, 4/4 = 100% precision** (found von Bernstorff, Nettesheim, Finck, **Remmert**; missed Saurer). Remmert's dense multi-strand title still reads economic/municipal on its face, but Pass-2 enrichment of her own Schwerpunkte surfaced "Allgemeine Grundrechtslehren" — a core constitutional-law/human-rights match — and she was included. Droege and Seiler were also enriched (not title-judged) and correctly excluded, independently matching the GT file's own exclusion notes. Saurer's own page shows no constitutional/human-rights/tech focus even after enrichment — an honest, defensible remaining miss, not the same defect class as Remmert. **Outcome: §4 criterion 1 now MET — all 6 measured faculties clear 80% (2 of 6 hard). Go/no-go flipped to GO.** Write-ups: `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md` (2026-07-04 log entry), `2026-07-03-core-done-go-no-go.md` (GO banner). Output: `dist/live-validation/law-skill.md`. `pytest -q` 29 passed/8 skipped; release build OK. |
| Task L | BW company backbone — extend to all Tübingen faculties + routing features (Phase 5) | ✅ | Domi | Live-researched all 7 faculties + ZITh (the `tuebingen-degree-programs.md` file the task brief pointed at turned out to be CS-only — corrected via Domi's live steer to research the actual faculty structure first). Derived a 13-employment-field taxonomy, gap-analyzed the existing backbone against it, and added 6 new sections (Chemie/Materialwissenschaft, extended Umwelt/Energie/Geowissenschaften, Wirtschaft/Consulting/Versicherung, Sozialwissenschaften/Marktforschung, Bildung/EdTech, Medien/Verlage/Sprache, Sport/Gesundheitstechnologie) with 16 new live-verified entries (every URL opened via WebFetch), plus a `Thesis-Kultur` column across all 13 tables and a Studiengangs-Routing table mapping every field to its backbone sections/tags. Rejected two candidates after failed verification (an acquired consultancy resolving to an unrelated same-named firm; an unconfirmed legal-tech HQ) rather than guess. Honestly documents fields that stayed thin despite real search effort (Recht/Legal Tech: 0 entries, Sozialwissenschaften: 1, Sport: 2) and one pre-existing 30%-cap breach (Informatik/AI, ~36% — predates this task, left alone as out of scope). EdTech persona smoke test returned only 2–3 candidates (below the 5–20 target) — an honest reflection of a thin field, correctly handled by the skill's existing "ask to broaden scope" fallback, not a bug. `pytest -q` 29 passed/8 skipped; release build OK. Full write-up: `findings/no_db_universal_skill/2026-07-04-taskL-taxonomy-and-gap-analysis.md`. |

### Phase 5 — Independent validation, scope experiment & distribution (scoped 2026-07-05)

Scoped by the [independent 1.0-readiness review](findings/no_db_universal_skill/2026-07-05-fable-1.0-readiness-review.md);
full justification and evidence per task lives there. Task letters continue from Task U
(no collision with the post-Phase-3 hardening table above).

| Task | Step | Status | Owner | Notes / difficulties |
|---|---|---|---|---|
| V | Blind live run, Theology faculty — repairs the Phase 4 hard-faculty blindness gap | ⬜ open | — | Ground truth exists (`skills/tests/eval_ground_truth/theology.md`), never opened mid-run. Cheapest remaining task (~20 min via the live-eval runbook). Also exercises the known N.N.-vacant-chair honesty case. Recommended first task on re-entry. |
| W | Scope-erosion experiment (gesamtplan §3 Idee 6 / §6 T3) — 2×2 {tool, baseline} × {Tübingen, TUM or KIT}, foreign GT curated by a second person | ⬜ open | — | The project's central scientific claim is untested. Trimmed version (one foreign university, one faculty, ~6-chair GT) estimated at 2–4 working days. Named by the review as the single highest-value remaining task. |
| X | Independent scoring pass — second person re-scores ~20% of surfaced options against existing live-eval outputs | ⬜ open | — | Every recall/precision/steering number to date is single-agent authored and scored; cheapest mitigation the gesamtplan already prescribed (§7) and never executed. |
| Y | Non-circular company ground truth (gesamtplan T4) | ⬜ open | — | Company recall/thesis-signal numbers measure "does the skill find what's in the backbone," not "does the backbone reflect reality." Alternative: explicitly demote company numbers to "plumbing check" in the write-up instead of running this task. |
| Z | Protocolled external test (3–5 students, incl. non-CS) on the shipped release artifact + one distribution channel (Fachschaft Informatik first) | ⬜ open | — | Closes Design-Entscheidungen.md TODOs 1 ("Hoch/Ja") and 2 ("Hoch/Ja"). Nobody outside the project has run the shipped `build_skill_release.py` artifact; Gehler's informal test used a dev checkout with no protocol. |
| AA | Hygiene sweep: fix the wrong-person paper index, the CS-only degree-programs file, portability contradictions, backbone link audit, small wording defects; also covers a post-M1–M3 live runbook re-exercise | ⬜ open | — | Bundle of small, independently-cheap fixes named by the review §7/O1–O6; none block the other Phase 5 tasks but should not be forgotten before a real 1.0 tag. |

**Gate Phase 5 (draft, to be confirmed on re-entry):** Task V done (clean hard-faculty
blind number exists) · Task W done with either outcome reported (Δ_in ≫ Δ_out confirmed,
or an honest negative result discussed) · Tasks X/Y done or explicitly and visibly
demoted in the write-up · Task Z done (external test run, one channel contacted) · Task AA
swept. Not all six need to complete for a defensible thesis submission — see the review's
§0 bottom line for which items are strictly blocking vs. optional.

---

## Open decisions

- **Coverage target:** ≥70% recall — confirmed as the standing target (Task H
  and Task I validated it; same target adopted for Phase 2).
- **Discovery skill name:** `find-university-chairs` stays as-is. Phase 2
  introduces `find-company-thesis-options` as a parallel skill. No rename planned.
  *(resolved 2026-06-28)*
- **Company list source (Phase 2):** Cyber Valley Industry Partners (primary,
  ~80–100 AI/ML entries) + ~20–30 manual BW R&D additions (automotive, medtech,
  software, industrial, energy). Bundled as a tagged Markdown reference file.
  Full rationale: `findings/no_db_universal_skill/2026-06-28-phase2-company-decisions.md`.
  *(resolved 2026-06-28)*

---

## Known difficulties / risks

- **Web-search coverage gaps** — chairs with weak/outdated web presence are
  silently missed. Mitigation: faculty-backbone crawl (Task B) + honest in-output
  caveat.
- **Beating plain Claude** — must be shown empirically, not assumed (Tasks G/H).
- **Profile must actually steer the search** — if the interview doesn't change the
  queries, the skill adds nothing (Tasks C/D).
- **Company discovery is a different, harder problem** — deliberately deferred to
  Phase 2.
- **Personal data (GDPR)** — surfaced researcher names + areas are public academic
  data; nothing student-private is ever stored (profile stays in-context only).

---

## Log

- **2026-09-05** — **`npx skills` install path cleaned up after Beat's feedback.**
  Beat's mail called the install instructions far too long and asked us to use
  <https://github.com/vercel-labs/skills> for all local agents. The one-command route
  already existed (INSTALL.md Route C, Step 0) but was dirty: the CLI also scans
  `.claude/skills/` and `.codex/skills/`, so it found **12** skills — the ten public ones
  plus the repo-internal `create-thesis-sim-student` and `run-thesis-simulations`, which
  `--skill '*'` happily installed into a student's client. Marked both (in each agent
  directory) with `metadata.internal: true`, which the CLI honours for the picker *and*
  the `'*'` wildcard (`src/skills.ts`, `src/add.ts` in vercel-labs/skills); the key is
  part of the Agent Skills frontmatter spec, so both skills still load repo-locally.
  Verified end-to-end: `npx skills@latest add <repo> --list` now reports exactly 10, and
  a real `--skill '*' --agent claude-code` install produces ten skill folders with their
  `references/` intact. Added `skills/tests/test_skills_cli_install.py` (fails if a
  maintainer skill loses the flag) and extended `qa.yml`'s path filter to the two agent
  skill directories. INSTALL.md itself untouched — shortening it is a separate call.
  Branch `feat/skills-cli-install`.

- **2026-07-05** — **Independent 1.0-readiness review completed and actioned; project
  re-paused with Phase 5 fully scoped.** Ran a from-scratch, deliberately skeptical review
  (`findings/no_db_universal_skill/2026-07-05-fable-1.0-readiness-review.md`) assessing
  1.0-readiness for both a thesis committee and real students, per this repo's own
  precedent of catching and reversing premature "green" calls (2026-06-28 CI-hygiene
  incident). Headline finding: the two hard-faculty numbers that produced the 2026-07-04
  GO (Humanities 100%, Law 80%) are not clean blind measurements — Humanities is a
  transparent re-score by an un-blind session, and the Law re-run's session had already
  read the document naming the missed chair and the fix. Every genuinely blind
  hard-faculty run to date scored 60%. The GO is not reversed (Task U's underlying skill
  fix is real and independently corroborated) but is flagged **provisional**. The review
  also assessed the project's central scientific claim (gesamtplan §3 Idee 6 — narrow
  scope beats plain Claude, breadth erodes the advantage) as directionally right but
  over-claimed in its SLLN framing, and confirmed the scope-erosion experiment (gesamtplan
  T3) needed to test it directly has still never been run — named as the single
  highest-value remaining task. Actioned the review's punch list into this project's own
  planning structure: (1) **MASTERPLAN.md** §8 got the provisional-GO caveat, and a new
  §9 scopes **Phase 5 as Tasks V–AA** (blind Theology run, scope-erosion experiment,
  independent scoring pass, non-circular company GT, protocolled external test +
  distribution, hygiene sweep) — replacing the previous "not yet scoped" placeholder; old
  §9 renumbered to §10. (2) **This file** got the same caveat threaded through the
  "Current phase" banner, the Phase 4/5 summary paragraphs, and a new Phase-5 task table
  mirroring the Phase 2/3 table format. (3) **`docs/thesis-report/03-hardening-and-
  evaluation/README.md` and `04-open-work/README.md`** were corrected — both still stated
  a stale 2026-07-03 snapshot (recall bar "not yet met", Task S "no data at all yet") that
  had been superseded by Task T/U/S but never synced into the thesis-facing narrative;
  both now state the current GO-provisional status directly and link the review. (4) The
  previously-untracked Task M plan file
  (`findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md`, `??` in
  `git status` despite being linked from three STATUS.md entries and two commit messages)
  was added to git in this pass. No skill files, reference files, or eval artifacts were
  touched — this was a read-only review followed by a pure documentation/planning update,
  exactly as the review's own mandate required. `pytest -q` and
  `python3 scripts/build_skill_release.py` unaffected (no code/skill changes). **Project
  re-paused here** — see "Current phase" above for the exact re-entry point; recommended
  next task on resume is **Task V**, then **Task W**.

- **2026-07-05** — **Task M2 (recommend & drill-down step in `thesis-finder`) done**, committed
  on `feat/no-db-universal-skill`. Inserted a new step between the option-map delivery and the
  `draft-thesis-contact` offer in both flows: New User Step N5 (offer step renumbered to N6)
  and Returning User Step R6 (offer step renumbered to R7, only runs if R4 produced a fresh
  map). The step recommends 1-2 top options from the map with a rationale grounded only in
  the map's existing fields, asks whether the student wants to go deeper or keep exploring,
  and — if deeper — reuses the `find-recent-papers` pattern from Task M3 to surface 1-2
  papers plus a "what you'd likely work on/learn" summary derived only from the map and the
  papers (Active Candidates status updated to "Recommended"). Both M1 and M3 log entries were
  already present (see below). **This closes out the Task M (Gehler feedback) plan** — M1,
  M2, M3 all done; M4 stays dropped per Domi's 2026-07-05 decision. Full plan:
  [2026-07-05-taskM-gehler-feedback-plan.md](findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md).

- **2026-07-05** — **Task M3 (paper-first gate in `draft-thesis-contact`) done**, committed
  on `feat/no-db-universal-skill`. Added a workflow step before drafting: if 1-2 relevant
  recent papers for the target person/lab aren't already in-session, call `find-recent-papers`
  to get them. Output section now includes the surfaced papers plus a recommendation that the
  student skim them first (avoids reading as generic, shows genuine engagement). Existing
  drafting rules (modest claims, no invented openings/funding/capacity) untouched. Task M1 was
  already done (see entry below). Next up: Task M2 (recommend + drill-down step in
  `thesis-finder`), per
  [2026-07-05-taskM-gehler-feedback-plan.md](findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md).

- **2026-07-05** — **Task M1 (upfront framing message in `thesis-finder`) done**, committed
  on `feat/no-db-universal-skill`. Added a one-time framing message before Step N1's
  interview in the New User Flow: states what the skill does, that answer detail level is
  the student's choice, and that the university/company/both track choice comes after the
  profile is built. Grepped `thesis-finder/SKILL.md` for Master-specific wording per the task
  brief — none found, so no further wording fixes were needed. Step N2, routing logic, and
  `build-student-profile` untouched. Next up: Task M3 (paper-first gate in
  `draft-thesis-contact`), per
  [2026-07-05-taskM-gehler-feedback-plan.md](findings/no_db_universal_skill/2026-07-05-taskM-gehler-feedback-plan.md).

- **2026-07-04** — **Project paused.** Full review pass over the current state before
  stepping away for a while: git tree confirmed clean (`git status` → nothing to commit),
  branch `feat/no-db-universal-skill` 41 commits ahead of origin, not pushed; `pytest -q`
  29 passed/8 skipped and `build_skill_release.py` both re-verified green. Two loose ends
  from the cleanup pass were resolved before pausing: the fully-merged `plan/gesamtplan-
  2026-07-02` branch pointer was deleted (dead weight, no data loss), and an untracked root
  file (`Feedback_Gehler.md` — informal end-user test notes) was moved to
  `docs/thesis-report/04-open-work/2026-07-04-feedback-gehler.md` with a synthesis paragraph
  in that section's README rather than left as unstructured clutter. Added an explicit ⏸
  pause banner to the top of "Current phase" (this file) as the designated re-entry point,
  naming the Feedback-Gehler file as the concrete next task. No skill logic changed in this
  pass — pure state verification and documentation.

- **2026-07-04** — **Task L (BW company backbone — extend to all Tübingen faculties) done,
  merged into `feat/no-db-universal-skill`.** Domi's live steer corrected the task brief:
  `tuebingen-degree-programs.md` (the file Step 1 pointed at) only lists the 6 CS-department
  programs, not a university-wide list — researched all 7 faculties + ZITh live via WebFetch
  instead, cross-checked against the existing `tuebingen-faculty-backbone.md`. Derived a
  13-employment-field taxonomy (Informatik/AI, Ingenieurnahe Systeme, Medtech, Chemie,
  Psychologie, Bildung, Umwelt/Energie/Geo, Wirtschaft/Consulting, Sozialwissenschaften,
  Medien/Sprache, Recht, Sport, and an explicit Theologie/Philosophie no-fit field), gap-
  analyzed the ~90-entry backbone against it, then added 16 new live-verified entries across
  6 new sections plus a `Thesis-Kultur` column and Studiengangs-Routing table. Rejected two
  candidates after live verification failed (an acquired management consultancy whose jobs
  page now resolves to an unrelated same-named Hagen tax firm; an unconfirmed legal-tech HQ)
  rather than guess — the backbone's "never invent a URL/location" rule held under pressure.
  Documented honest, real gaps instead of padding: Recht/Legal Tech (0 entries — matches the
  task brief's own expectation that company-supervised Jura theses are structurally rare),
  Sozialwissenschaften/Marktforschung (1 entry — most BW social-science jobs are public-
  sector/NGO, outside this company-only backbone's scope), Sport (2), Wirtschaft (4). Also
  surfaced and left transparently flagged, not silently fixed: Informatik/AI already exceeds
  the 30%-of-backbone cap (~36%) from before this task — real Cyber-Valley density, not
  padding, and out of scope to trim without risking the Phase 3/4 eval baseline. EdTech
  persona smoke test returned 2–3 candidates (below the 5–20 target) — confirmed this is the
  skill's existing "ask to broaden scope" disambiguation rule working as designed on a
  genuinely thin field, not a defect. `pytest -q` 29 passed/8 skipped; `build_skill_release.py`
  green, both re-checked after merge to `feat/no-db-universal-skill`. Worktree
  `study-os-thesis-taskL` and branch `task/L-company-backbone` removed post-merge. Full
  write-up: `findings/no_db_universal_skill/2026-07-04-taskL-taxonomy-and-gap-analysis.md`.

- **2026-07-04** — **Task U (§5 enrich-before-exclude fix + Law re-run) done — §4 go/no-go
  FLIPPED TO GO.** (1) **Skill fix committed:** added an "Enrich before excluding" rule to
  `find-university-chairs/references/search-strategy.md` §5 — the symmetric dual of the
  existing Butz over-inclusion worked example. Do not exclude a candidate at the
  topical-justification step from a *title-only* reading when the title names a
  core-interest field amid off-interest strands; run Pass-2 enrichment on the chair's
  actual research focus first. Added a matching one-liner to `SKILL.md` Step 7. (2) **Law
  blind re-run: 3/5 → 4/5 = 80% recall, 3/3 → 4/4 = 100% precision.** Same persona as Task
  T's blind run, reused verbatim (only the `Sample interest:` grep re-confirmed; no
  GT chair rows opened until scoring). All 7 public-law chairs Pass-2 enriched this time,
  not title-judged. **Remmert now surfaces:** her dense multi-strand title ("Staats- und
  Verwaltungsrecht, Öffentliches Wirtschaftsrecht, Kommunalrecht") still reads
  economic/municipal on its face, but enrichment of her own Schwerpunkte page found
  "Allgemeine Grundrechtslehren" (fundamental-rights doctrine) plus active GG-commentary
  work — a core constitutional-law/human-rights match — and she was included. Droege and
  Seiler were also enriched (not title-judged) and still correctly excluded, independently
  matching the GT file's own "off-interest, not noise" notes exactly — confirms the fix
  didn't just flip Remmert by loosening the filter generally. **Saurer remains the one
  miss** — his own chair page shows no constitutional-law/human-rights/tech-regulation
  content even after enrichment (Umweltrecht/Infrastrukturrecht/Rechtsvergleichung is his
  genuine core); an honest, defensible remaining gap, not the same title-surface defect
  class as Remmert. (3) **All 6 measured faculties now clear 80% recall** (CS 100%, Medicine
  ≥83%, Psychology ≥83%, WiSo ≥83%, Humanities 100%, Law 80%), with 2 of 6 being hard
  faculties — **§4 criterion 1 is MET.** Flipped the go/no-go verdict banner in
  `2026-07-03-core-done-go-no-go.md` to **GO**, updated the aggregate scorecard
  (`2026-07-03-eval-aggregate-scorecard.md`) to match. `pytest -q` 29 passed/8 skipped;
  `build_skill_release.py` green. Write-ups: `2026-07-02-live-eval-runbook.md` (2026-07-04
  entry), `2026-07-03-core-done-go-no-go.md` (GO banner). Output:
  `dist/live-validation/law-skill.md`.

- **2026-07-03** — **Task T (eval-protocol fix + hard-faculty recall closeout) done — NO-GO
  still stands, transformed.** (1) **Protocol fix committed:** the runbook built personas from
  the eval README's lossy one-line summaries; reconciled runbook steps 2–3 so personas are now
  built from each GT file's full `Sample interest:` line (grep-extracted, with an explicit
  no-peeking carve-out for that single line) — an eval-harness fix, not a skill change. (2)
  **Humanities corrected re-score: 3/5 → 5/5 = 100%** (precision 100%). Transparent, not a fresh
  blind run — this conversation was un-blind on Humanities (task context required reading the
  prior blind entry, which names all 5 GT chairs). Both prior misses flip to Include once the
  full sample interest restores the dropped "…history of the field (ancient philosophy, Kant /
  German Idealism)" (→ Corcilius) and "theory of emotions" (→ Döring) clauses. This **decisively
  validates the protocol fix**: the whole Humanities 60% was a lossy-README artifact. (3) **Law
  blind run: 3/5 = 60% recall, 3/3 = 100% precision.** This was the genuinely-blind faculty this
  round (only its sample-interest line read before Pass 1). Discovery recall was 5/5 — Pass 1
  enumerated all five public-law GT chairs; the 60% is a **downstream filtering** miss. Root cause
  is a **real skill finding, not a GT artifact:** Remmert and Saurer were excluded at the §5
  topical-justification step *without Pass-2 enrichment*, from a surface reading of their dense
  multi-strand German chair titles. Post-scoring enrichment of **Remmert** ("Staats- und
  Verwaltungsrecht, Öffentliches Wirtschaftsrecht, Kommunalrecht") showed her actual Schwerpunkte
  are **Allgemeine Grundrechtslehren** (fundamental-rights doctrine, current GG-commentary work) —
  a squarely-core constitutional-law/human-rights match → genuine false-negative. Had the skill
  enriched before excluding, recall would be ≥4/5 = 80%. This is exactly the hardness `law.md` was
  built to probe (map "constitutional law" onto dense German formulas). **Verdict:** the *original*
  blocker (Humanities 60%) is resolved, but the blind Law run surfaced a *new, narrower* defect, so
  now **5 of 6** measured faculties clear 80% (Law is the sole miss) — criterion 1's strict
  per-faculty reading still not met. Not a GO (same anti-premature-GREEN discipline as before; Phase 2
  still GREEN, no schedule pressure). Named **Task U** (add §5 enrich-before-exclude rule → re-run
  Law → flip to GO if it clears 80%). Skill files untouched this task, so pytest/release-build still
  green from the last task. Write-ups: `findings/no_db_universal_skill/2026-07-03-task-t-recall-closeout.md`,
  runbook log `2026-07-02-live-eval-runbook.md` (two 2026-07-03 entries), decision-doc update banner
  in `2026-07-03-core-done-go-no-go.md`.

- **2026-07-03** — **§4 Go/No-Go call: NO-GO** (judgment over existing evidence, no new
  live run). With Tracks 1–4 all complete, made the explicit "core is done" decision the
  roadmap's §5 dependency graph had been deferring. Scored roadmap §4's five criteria against
  the aggregate scorecard: steering (Task P), output quality (Task S), and edge-case
  robustness (Task R) all **met**; precision **strong where measured** but only 2/5 faculties
  formally scored; the **recall criterion is NOT met** and fails on two independent counts —
  (a) only **5** faculties have a live number, so "≥6 faculties" cannot be claimed at all, and
  (b) **no hard faculty** has a clean live ≥80% (Humanities 60%, Law/Theology unrun). Crucially,
  the Humanities 60% is root-caused to the **eval protocol, not the skill**: personas are built
  from the README's lossy one-line sample-interest summaries, dropping a clause in the GT file's
  full sample interest — the live crawl actually found all 5 GT chairs. **Not converted to a GO**
  for two reasons: (1) precedent — this project was already burned by a premature "gate GREEN"
  declared on partial evidence (see the 2026-06-28 CI-hygiene entry); (2) no schedule pressure —
  Phase 2 (companies) is already GREEN, so nothing downstream waits on this gate, meaning there's
  no cost to closing the gap properly instead of booking it. Named the closeout as **Task T**
  (fix the eval-protocol lossy-summary gap → blind-re-run Humanities under the corrected protocol
  → blind-run Law to reach ≥6 measured faculties), done-when ≥6 faculties have a live recall
  number with ≥1 hard faculty ≥80%. Deliverable is the decision itself — **no skill files
  touched**, so pytest/release-build untouched and still green from the last task. Full reasoning:
  `findings/no_db_universal_skill/2026-07-03-core-done-go-no-go.md`.

- **2026-07-03** — **Task S (output & interview quality pass) done.** Reviewed the 5
  full discovery transcripts (`dist/live-validation/{cs,medicine,psychology,wiso,
  humanities}-skill.md`) against the roadmap's 5 output-quality criteria. Pros/cons:
  mostly honest and specific (one narrow lapse — wiso-skill, 2/7 options missing the
  field). Conversation starters: consistently chair-specific, not templated (humanities
  the strongest, naming an actual 2025 paper by title). Coverage caveat: present on
  5/5 full outputs. Dated evidence: **repeated gap** — cs-skill and wiso-skill omit the
  field from every option (2 of 5 transcripts), while medicine/psychology/humanities
  comply; not explained by chronology, so treated as a spec-compliance gap and fixed
  with one worked example added to `find-university-chairs/SKILL.md` Step 8. Interview
  convergence: no happy-path transcript existed anywhere in the repo (every discovery
  transcript starts from an already-built persona, never an actual interview), so ran
  one live — 6 turns to a clean six-dimension profile with a cooperative persona,
  contrasting with edge case 2's 8-turn adversarial non-convergence. No fix needed
  there; confirms the design. Full write-up:
  `findings/no_db_universal_skill/2026-07-03-task-s-output-quality.md`. Per the
  roadmap's dependency graph (§5), Track 4 is now fully done — §4's "core is done" gate
  should get an explicit go/no-go call next.

- **2026-07-03** — **Eval Scorecard.** Aggregated every recall/precision/steering/robustness
  number produced so far (Task H/I/I-fix, Phase-2 Task 2-E, Roadmap-J run 1, Task O re-run,
  Task P, Task Q run 1, Task R) into one document,
  `findings/no_db_universal_skill/2026-07-03-eval-aggregate-scorecard.md` — pure aggregation,
  no new live run, every number cited to its source file. Structured per the roadmap's five
  quality axes (recall, precision, steering, robustness, output quality). Headline finding:
  the roadmap's own "core is done" recall bar (≥80% recall across ≥6 faculties incl. one hard
  faculty, `core-optimization-roadmap.md` §4) is **not yet met** — only 5 faculties
  (Medicine, Psychology, WiSo, CS, Humanities) have any live recall number at all, and
  Humanities — the only hard faculty tested — sits at 60%, below bar (root-caused to an
  eval-protocol gap, not a skill defect; see Task Q run 1 above). Law and Theology have
  ground truth but no live run yet. Precision has only been formally measured for 2 of 5
  faculties. Task S (output/interview quality) has zero data points. Updated
  `docs/thesis-report/03-hardening-and-evaluation/README.md` and `04-open-work/README.md` to
  reflect that Task Q's blind run and Task R both actually completed (both had been written
  as "deferred"/"not started" before this pass caught up with the parallel session's work).

- **2026-07-03** — Documentation pass, no skill-logic changes. (1) Closed a silent
  visibility gap found while reconciling Task Q: `core-optimization-roadmap.md` defines
  Track 2 (backbone audit & repair / weak-web-presence fallback / query-skeleton iteration)
  and Track 4's Task R (edge-case behavior) and Task S (output & interview quality) — none
  of the three appeared in STATUS.md's task table, as either open or done, so a reader of
  STATUS.md alone would not know they were planned-but-not-started work. Added all three as
  ⬜ open rows with a note that Track 2 was implicitly skipped because Task I already cleared
  ≥70% recall (the roadmap's own dependency graph only routes to Track 2 when recall is low).
  (2) Added a "Phase 4 — Hardening" pointer section to MASTERPLAN.md so the stable plan
  reflects that a post-Phase-3 hardening track exists, without duplicating its detail — same
  pattern as the existing phase sections. (3) Created `docs/thesis-report/`: a curated,
  chronologically-organized account of the project's genesis and decisions for the thesis
  submission, assembled from ~25 previously scattered root/docs/findings files. Historical
  root-level files (`VISION_NO_DB.md`, `PROJECT_CONTEXT.md`, `25.06Besprechung.md`,
  `Ideen_Domi_02_07.md`, `docs/research/`, `Mails (1).docx`, `Plan.docx`) were physically
  moved (`git mv`, history preserved) into dated subfolders; living docs (this file,
  MASTERPLAN.md, README.md, AGENTS.md, CLAUDE.md, CHANGELOG.md, Design-Entscheidungen.md)
  stayed in place and are linked, not copied. `findings/no_db_universal_skill/*` was left
  untouched — already dated and chronological, just linked more heavily. (4) Removed local-only
  junk with zero git footprint (`ruvector.db`, `.claude-flow/`, `.swarm/` — pre-pivot
  vector-DB leftover and tool-state caches, none tracked or referenced); flagged three tracked,
  zero-inbound-reference docs (`WORKFLOW.md`, `COMBINED_PR_GUIDE.md`, `ISSUE_ROUTER.md`) as
  deletion candidates for Domi to confirm rather than removing them unasked. Next: a fresh
  conversation runs the deferred Task Q blind live run (hard faculty, `law` recommended).

- **2026-07-03** — Task Q (Track 4, **hard-faculty ground truth** — robustness, the
  last unproven axis in the roadmap's "core is done" definition §4). Extended eval
  ground truth beyond the 4 structurally-easy faculties (Med/Psych/WiSo/CS) to the
  hard ones, all built by crawling the **official faculty backbone** (WebFetch/WebSearch
  on the uni-tuebingen.de listing pages), not by running the skill — so these files stay
  a valid, skill-independent benchmark. Four new files under
  `skills/tests/eval_ground_truth/`:
  - **`humanities.md`** — Philosophische Fakultät → FB5 → Philosophisches Seminar;
    sample interest phil. of mind / metaphysics / cognitive science. Core GT: Sattig
    (theoretical phil.), Wong (phil. of cognitive science), Corcilius (ancient),
    Schlösser (Kant/German Idealism), Döring (ethics/emotions, honorary — flagged for
    the affiliation-currency check). Hardness = *large three-level faculty*: chairs sit
    two levels below the backbone page in a Seminar, so discovery must drill the tree.
  - **`law.md`** — Juristische Fakultät → Öffentliches Recht. Core GT: von Bernstorff
    (constitutional/international/human rights), Nettesheim (EU/international), Finck
    (**Recht der KI** — AI law/data protection), Saurer (environmental/comparative),
    Remmert (public economic law). Tax chairs (Droege, Seiler) documented as
    off-interest, not noise. Hardness = *dense German public-law chair-title formulas*
    the topic→query mapping must decode.
  - **`theology.md`** — Evangelisch-Theologische Fakultät; sample interest biblical
    studies / early-church history. Core GT: Leuenberger, Kamlah, Tilly, Landmesser,
    Drecoll, Witt (+ Zellentin adjacent). Lists chairs almost directly (structurally
    easy) **but is genuinely chair-poor for some interests** — see below.
  - **`interdisciplinary.md`** — one persona spanning **three faculties + interfaculty
    centers**: ethics/law/governance of AI. Anchors: Finck (Law), Heesen + Ammicht Quinn
    (IZEW/interfaculty ethics), Hardt (MPI-IS Social Foundations of Computation —
    fairness/FAccT), Wong (Philosophy — foundations). Tests **routing breadth** (does
    discovery span all three faculties, incl. off-backbone interfaculty centers) rather
    than within-faculty depth. README gained a per-faculty-coverage routing-metric note.

  **Task-P caveat #3 confirmed as a live robustness finding.** Protestant Theology has
  several **vacant (N.N.) chairs** — including **Systematische Theologie II (Ethik und
  Christliche Gesellschaftslehre)** and Fundamentaltheologie/Religionsphilosophie. So for
  a theological-ethics or philosophy-of-religion persona the directly-relevant chair is
  currently *unstaffed*: honest discovery should report "no staffed chair for this exact
  focus at this faculty," not misroute to a filled-but-off-topic chair. This is the
  chair-scarcity limit Task P predicted (a small faculty may not have enough distinct
  *staffed* groups for two profiles to diverge) — recorded as robustness/coverage, **not**
  a steering or recall failure. The biblical-studies GT above is deliberately chosen from
  the well-staffed cluster to keep the recall metric clean; the vacancy point lives in
  `theology.md` Notes.

  **Blind live run deferred — on purpose.** The runbook's core discipline is that GT
  authoring and the skill arm must be blind to each other; authoring all this GT in this
  conversation contaminates any same-session skill run. So the first live recall/precision
  read on a hard faculty is handed to a **fresh** conversation (next task), which should
  run the skill arm without opening these GT files until scoring. Deliverable this session
  is the GT itself. `python3 -m pytest -q` and `python3 scripts/build_skill_release.py`
  still green.

- **2026-07-03** — Task R (Track 4, **edge-case behavior**), following Task Q run 1.
  Three edge cases exercised live, per roadmap §3. **(1) Niche no-match:**
  rocket-engine/spacecraft-propulsion engineering — confirmed live that Tübingen has
  no engineering faculty and neither Physics nor Chemistry has a propulsion/
  combustion group; the honest output says so plainly and names universities that
  do have this (TU Berlin, TU Braunschweig, TUM, Uni Stuttgart) instead of padding
  with a distant weak match. **(2) Shallow/resistant student:** rather than assert
  the gate holds, simulated an 8-turn adversarial interview (repeated "just give me
  a name" pressure, "no preference"/"none" non-answers) against
  `build-student-profile`'s actual rules. The gate held throughout — no premature
  `find-university-chairs` call — and the simulation surfaced that
  `find-university-chairs`'s own independent Step 1 depth re-check (not just trust
  in `build-student-profile`'s handoff) is a real, exercised robustness property,
  not just a paper guarantee. **(3) Interdisciplinary routing:** ran the
  `interdisciplinary.md` persona (ethics/law/governance of AI spanning Law,
  Humanities/IZEW, Science-ML) live — **5/5 GT anchors surfaced, 3/3 faculties/
  centers covered** (Finck/Law, Heesen+Ammicht Quinn/IZEW, Wong/Philosophy,
  Hardt/MPI-IS) — routing did not collapse onto one discipline. Not a blind run by
  design (Task R tests routing breadth, not an unbiased recall number). **Two small
  spec gaps found and fixed**, both one-line additions: `find-university-chairs/
  SKILL.md` Step 8 now has an explicit zero-candidates rule; `build-student-profile/
  SKILL.md` now recommends forced-choice questions when open-ended ones produce
  refusals, plus an honest generic-pointer fallback instead of an endless interview
  loop for a student who never crosses the depth bar. All three edge cases passed
  the "degrade honestly" bar — no search-strategy or backbone defect found, both
  fixes were spec gaps for cases the design already handled correctly in spirit.
  Full write-up: `findings/no_db_universal_skill/2026-07-03-task-r-edge-cases.md`.
  Outputs: `dist/live-validation/{niche-no-match,interdisciplinary}-skill.md`.
  Per roadmap §5, Track 4 is now done; recommend **Task S** (output & interview
  quality pass) next. `python3 -m pytest -q` and
  `python3 scripts/build_skill_release.py` still green.

- **2026-07-03** — Task Q run 1 (Track 4, **first blind hard-faculty live run**,
  `humanities`). Fresh conversation, as planned by the deferral above. Chose
  `humanities` over `law` because it exercises the deep Faculty→FB5→Seminar
  drill-down — the actual untested robustness axis. Built the persona from only the
  eval README's one-line sample-interest summary (no GT file opened before the run).
  **Recall 3/5 = 60%** (Sattig, Wong, Schlösser found; Corcilius, Döring missed) —
  below the README's 70% target, but the live Pass-1 crawl actually found and
  evaluated all 5 GT chairs; 2 were then excluded because the README's abbreviated
  one-liner omits a clause in `humanities.md`'s real sample interest ("...with an
  interest in the history of the field"), so the persona built from it reasonably
  added a no-go against pure historical exegesis that the full GT profile doesn't
  actually have. **This is an eval-protocol finding (lossy one-line summary), not a
  search-strategy or backbone defect** — the backbone drill-down itself worked
  correctly on the first try. **Precision 3/3 = 100%**, and the run independently
  re-derived the GT file's own "deliberately excluded, not noise" judgments
  (Grabmayr, Schumski) via the skill's own no-go/topical-justification rules.
  One interfaculty backbone URL 404'd (second data point, after `cs`'s Cyber Valley
  404, that Track 2 backbone audit is worth doing). Output: `dist/live-validation/
  humanities-skill.md`. Full write-up: `findings/no_db_universal_skill/
  2026-07-02-live-eval-runbook.md` log. Recommend Track 4 Task R (edge-case behavior)
  next — this run surfaced no new skill defect to fix first. `python3 -m pytest -q`
  and `python3 scripts/build_skill_release.py` still green.

- **2026-07-02** — Task P (Track 3, **steering proof** — the roadmap calls this "the
  most important for the thesis claim"). First direct test that the 6-dimension
  interview actually changes the search rather than decorating a generic answer. Ran
  `cs` (FB-Informatik) live through `find-university-chairs/SKILL.md` with **two
  students with inverted profiles**: Persona A (causality + probabilistic/Bayesian ML;
  no-go computer vision + hardware) and Persona B (computer vision + representation
  learning; no-go heavy Bayesian theory + hardware). Same faculty, same Pass-1
  candidate set. Result: the two option maps are **near-disjoint** — vision chairs
  (Geiger, Black, Pons-Moll, Kühne, Bethge) top Persona B and are excluded from A;
  Bayesian/causality chairs (Schölkopf, Hennig, Macke, von Luxburg) top A and are
  excluded from B; only Brendel and Hein appear in both, and reframed/reranked. The
  top entries flip in exactly the direction each profile predicts, and conversation
  starters fully diverge. **Verdict: steering confirmed (strong)** — the profile is
  not decorative; this is the first empirical defense of the "better than plain
  Claude" claim. Steering is carried by search-strategy §1 (interest→topic query) +
  §5 (topical-justification filter); the §7 no-go *table* did **not** carry it (neither
  "CV" nor "heavy Bayesian" is a codified §7 row — both applied via §7's general rule),
  a minor doc gap logged as follow-up, not fixed here. Honest limits: single agent
  designed/ran/judged both runs (confirmation-bias risk, mitigated by grounding every
  chair→persona call in live-verified facts); personas were built to diverge (proves
  the mechanism *can* steer, not that it steers on near-identical profiles); one
  faculty. Outputs `dist/live-validation/cs-persona-{A,B}-skill.md`; write-up
  `findings/no_db_universal_skill/2026-07-02-task-p-steering-proof.md`. Next: Track 4
  Task Q (hard-faculty ground truth). `pytest -q` 29 passed/8 skipped; release build OK.

- **2026-07-02** — Task O (Track 3, relevance/no-go tightening + affiliation-currency
  check), driven directly by Roadmap-J run 1's finding below. Three doc changes in
  `skills/find-university-chairs/`: (1) search-strategy.md §5 gets a new "topical
  justification" quality filter — a chair's inclusion must be justified by its own
  stated research matching the profile, not by sharing a faculty page section with
  relevant chairs (Butz worked example added); (2) §7's "pure math proofs" no-go
  wording sharpened — foundational/theoretical-but-not-proof-only work (Williamson's
  case) is ambiguous by default, kept-and-flagged rather than left undefined; (3) new
  §4.7 affiliation-currency query skeletons + a SKILL.md Step 5 sub-step 2f upgrade —
  a distinct check from the existing recency check, since a backbone page can look
  active while the PI has physically relocated. Re-ran the Roadmap-J runbook live for
  `cs`, same persona, no-peeking discipline actually held this time (reconstructed the
  persona from this run's own compact summary + the process-only
  `2026-06-28-live-validation-protocol.md`, without opening `eval_ground_truth/`).
  **Recall held at 5/5 = 100%.** **Precision rose from 9/12 (75%) to 10/10 (100%):**
  Butz and Williamson are now excluded before the map is built instead of surfacing
  with a caveat; Oh's KAIST relocation (confirmed again via live search) is caught by
  the new codified 2f check rather than depending on the agent noticing, and is
  flagged/excluded from the actionable list per SKILL.md's "do not silently drop"
  instruction. Honest caveat: this is one faculty, one persona, one run — it shows the
  three known noise sources are fixed, not that the filter generalizes cleanly to
  faculties/personas that haven't been tested yet (e.g. Humanities/Law chair pages may
  bundle differently than FB-Informatik's "Maschinelles Lernen" section did). MPI-IS's
  `is.mpg.de/departments` bot-block persisted a third run running — untouched by this
  task, still a Track 2 candidate. Full write-up:
  `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md` (second entry).
  `pytest -q` 29 passed/8 skipped; `build_skill_release.py` OK.

- **2026-07-02** — First live exercise of the Roadmap-J runbook, faculty `cs`.
  Reused the Task I-fix persona verbatim for comparability. Ran Pass 1 live
  (FB-Informatik page fetched fine; MPI-IS `is.mpg.de/departments` bot-blocked
  again; Cyber Valley `research-groups` URL 404'd this time — both required a
  web-search fallback per researcher name, same gap as Task I-fix). **Recall
  5/5 = 100%** — no regression vs. Task I-fix. **Precision 9/12 = 75%** — the
  first precision number ever recorded for this skill. Two entries are genuine
  over-surfacing (Butz: cognitive science, not AI/ML; Williamson: weak topical
  fit, borderline pure-math no-go). One is a more interesting failure mode:
  **Prof. Seong Joon Oh's STAI group relocated to KAIST in February 2026, but
  the live FB-Informatik backbone page still lists it under Tübingen with no
  relocation notice** — the skill's existing 2f "existence/activity check"
  checks for recent publications/news, which the old page still has, so it
  would not have caught this. Zell was correctly excluded pre-scoring via the
  hardware/embedded no-go (3 robotics labs, FPGA project — non-ambiguous).
  **Honesty note:** the runbook's no-peeking rule was not observed this run —
  the CS ground-truth file and Task I-fix's named results were read during
  general context-gathering before Pass 1 started. The recall number is
  probably still representative (the FB-Informatik page organically listed
  the GT names in its own "Maschinelles Lernen" section, they weren't
  specifically searched for), but it isn't a blind result — flagged clearly in
  the runbook log so it isn't mistaken for a clean measurement. Result and
  full reasoning: `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md`.
  **Points to Track 3 (Task O — relevance/no-go tightening)** as the next
  optimization track: tighten relevance filtering so faculty-page section
  membership alone doesn't surface a domain-mismatched chair, and extend the
  2f check to verify current institutional affiliation (not just publication
  recency) so a relocated PI isn't silently presented as available.
  `pytest -q` and `python3 scripts/build_skill_release.py` re-confirmed green
  after these doc-only changes.

- **2026-07-02** — Roadmap-J + Roadmap-K done (core-optimization-roadmap Track 1,
  items after Task I). Discovered a letter collision first: the roadmap's own
  "Task J" (lightweight live-eval runbook) and "Task K" (precision metric) were
  never built under those names — a different, unrelated fix (canonical six
  profile dimensions) got logged as "Task J" earlier today. Relabeled the roadmap
  items `Roadmap-J`/`Roadmap-K` in the task table to keep both traceable without
  renaming the already-completed J. (Roadmap-J) Wrote
  `findings/no_db_universal_skill/2026-07-02-live-eval-runbook.md`: a cheap
  (~15–20 min) checklist to re-validate one faculty live after a skill change —
  reuse the existing persona, no-peeking, skill arm only (no fresh baseline),
  score recall + precision, append one log line — versus the full 4-faculty,
  both-arms `2026-06-28-live-validation-protocol.md` meant for one-time
  validation. Not yet exercised. (Roadmap-K) Recall alone rewards over-surfacing,
  so added a precision metric to `skills/tests/eval_ground_truth/README.md`:
  precision = surfaced options judged relevant / total surfaced options, judged
  against the MAP's own "Relevance rationale" field rather than strict
  ground-truth membership (the ground truth is deliberately non-exhaustive, so a
  correct-but-unlisted option is still relevant, not noise). No fixed precision
  target set yet — deferred until the new runbook produces a few live data
  points. `pytest -q` → 29 passed, 8 skipped; `build_skill_release.py` OK.

- **2026-07-02** — Task J done. `build-student-profile/SKILL.md` workflow step 4
  required a different six-item list ("interests, liked/disliked courses, skills,
  experience, preferred thesis style, no-gos") than the gate every discovery skill
  actually checks (Interests, Methods, Domain, Thesis style, Skills, No-gos) —
  Methods and Domain were missing entirely, so a profile built standalone via this
  skill could look "complete" and still fail the `find-university-chairs` /
  `find-company-thesis-options` prerequisite gate. Added a single canonical
  definition (`## Canonical Six Dimensions`, each with a 1-line description) to
  `student-profile-schema.md`; corrected workflow step 4 in `build-student-profile/
  SKILL.md` to reference it; courses/experience kept as elicitation avenues (how
  Methods/Domain/Skills get filled), not as separate dimensions; Output section now
  explicitly emits the compact 6D summary alongside the existing rich fields.
  `thesis-finder`, `find-university-chairs`, `find-company-thesis-options` already
  used the correct 6 terms — no changes needed there. `pytest -q` → 29 passed, 8
  skipped; `build_skill_release.py` OK. Commits: `3483629`, `2d6a9c5`.

- **2026-06-28** — **CI / engineering-hygiene fix.** Review found the deterministic
  package suite was actually **RED**: `python -m pytest -q` (run by `qa.yml` and
  `package-skills.yml`) reported **9 failures**, and the release artifact could not be
  built. Earlier "gate GREEN" verdicts only ran the eval-harness tests
  (`test_codex_multiturn_eval.py`, 12/12) + a manual smoke trace — the package/release
  tests were never run after the no-DB pivot. Two root causes fixed: (1) **Real skill
  bugs** — `find-university-chairs` (6×) and `find-company-thesis-options` (4×) embedded
  section anchors *inside* the backtick of a `references/…` link
  (`` `references/…md §1` ``), which broke `build_skill_release.py`'s reference validator
  (`BuildError`) and `test_referenced_skill_resources_exist`; moved the ` §N` outside the
  backtick. `thesis-finder` description lacked the `Use when …` trigger; added it.
  (2) **Stale DB-era tests** — `test_skill_package.py` was never migrated from the pre-pivot
  world: `EXPECTED_SKILLS` still listed the deleted `match-thesis-advisors` /
  `update-openalex-paper-index` and omitted `thesis-finder` / `find-company-thesis-options`;
  `test_required_markdown_database_indexes_exist` and the professor-seed-index test asserted
  the very `professors/INDEX.md` the pivot removed; privacy/evidence assertions checked
  pre-Task-A/D wording. Migrated the suite to the no-DB contract (corrected skill set;
  replaced the inverted DB-index tests with `test_discovery_skills_carry_no_runtime_seed_data`,
  which guards that seed dirs stay *out* of the runtime skill; updated the static-acceptance
  fixture to the current build-profile → thesis-finder → discovery → contact/directions flow).
  The CI **architecture** (qa / package-skills / codex-multiturn-evals workflows + the
  release builder) fits the portable-skill product and was kept as-is. Result:
  `pytest -q` → **29 passed, 8 skipped**; `build_skill_release.py` produces tar.gz + zip
  with the correct 8 skills. Files changed: 2 discovery SKILL.md, thesis-finder SKILL.md,
  `test_skill_package.py`.

- **2026-06-28** — Phase 3 **complete — gate GREEN.** (3-A) Backbone updated: Aleph Alpha entry replaced with "Cohere GmbH (formerly Aleph Alpha GmbH) ⚠" plus merger caveat; §5 Software/Enterprise expanded from 3 to 7 entries (added IONOS, Haufe, GFT, Schwarz IT). (3-B) `skills/thesis-finder/SKILL.md` created as thin 4-step orchestrator: profile check → track choice → route to find-university-chairs / find-company-thesis-options / both → offer draft-thesis-contact. (3-C) `AGENTS.md` student workflow updated to current skill set; find-company-thesis-options and thesis-finder fully documented; retired skills (match-thesis-advisors, update-openalex-paper-index) annotated as retired. README.md got a student-facing top section (what it is, how to use it, what it gives, what it doesn't). (3-D) Smoke test traced C1 profile through all 15 steps across both tracks — all PASS; zero dead references. Phase 3 gate: all 6 criteria GREEN. Branch ready for review/merge. Distribution to Fachschaft/Hennig/Ersti-Heft is the next human action. Commits: see git log.

- **2026-06-28** — Phase 2 kick-off **done**. Resolved two open STATUS.md decisions: (1) company
  backbone source → Cyber Valley Industry Partners + ~20–30 manual BW R&D additions, tagged
  Markdown file, ~100–130 entries; (2) output schema → company option map with always-present
  fields (name, sector, size, location, relevance, pros/difficulties, contact path) and
  may-be-missing fields (thesis signal, coordinator name), stronger coverage caveat than uni
  version. Wrote `2026-06-28-phase2-company-decisions.md` and `2026-06-28-phase2-build-plan.md`
  (Tasks 2-A through 2-E with ready-to-paste agent prompts). Discovery skill name decision
  closed: `find-university-chairs` stays as-is, new `find-company-thesis-options` is a parallel
  skill. Phase 2 task table added to STATUS. Commits: `ce04977`, `STATUS update`.

- **2026-06-28** — Task I-fix **done** (two bugs from Task I corrected). (1) Added 2e PI-verification step to SKILL.md Step 5: each named professor must be confirmed on the unit's own staff page before attribution; added §4.6 person-verification query skeletons to search-strategy.md. (2) Added MPI-IS (`is.mpg.de/departments`) and ELLIS/Cyber Valley as first-class Pass-1 sources to SKILL.md Step 4, search-strategy.md §2, and backbone drill-down table. Re-validated Psychology and CS live (no peeking): Psych primary 100%/strict 83%, CS primary 100%/strict 100% — both clear ≥70%. **Phase-1 gate is now GREEN.** Full results: `findings/no_db_universal_skill/2026-06-28-I-fix-revalidation.md`. Commit: `c1cc302`.

- **2026-06-28** — Task 2-D + 2-E **done**. (2-D) Built `skills/tests/eval_ground_truth/company_seed/`: 3 profiles (C1 ML/automotive, C2 medtech, C3 software/enterprise) × 5–6 verified companies each; confirmation URLs verified live; README defines recall + thesis-signal metrics. (2-E) Live validation GREEN: 100% recall on all 3 profiles vs 74% baseline mean (+26pp delta); thesis-signal accuracy 94% (1 TeamViewer over-classification). Key caveats: circular recall (GT/backbone share the same source), weak C1 delta (+17pp, baseline already knows Bosch/ZF/Mercedes), Aleph Alpha backbone entry stale post-April-2026-merger. Full results: `findings/no_db_universal_skill/2026-06-28-phase2-live-eval-results.md`. **Phase-2 gate: GREEN.** Phase 3 (distribution/orchestration planning) is the next step. Commits: `9f03e8f`, `a0ddf16`, `15e8d02`.

- **2026-06-28** — Task I (live validation) **run**. Built one persona per faculty
  from the *sample interest* only, then ran the discovery skill end-to-end with live
  `WebSearch`/`WebFetch` (skill arm) and a clean no-skill prompt (baseline arm) for
  medicine, psychology, wiso, cs — **all 8 arm outputs written before opening any
  ground-truth chair list** (no peeking; artifacts in `dist/live-validation/`).
  **Results:** primary recall (README name-surfacing) mean **~82%** skill vs **~17%**
  real baseline (+65pp); per-faculty Med 100%, WiSo 100%, Psych 67%, CS 60%. Strict
  person-level recall mean **~65%** (Psych only 17%). Real baseline is **not 0%** —
  plain Claude names Ziemann/Schlumberger/Abels/Hein — so the fixture's 96%-vs-0% was
  doubly optimistic. Honest defects: (1) Psychology PI **misattribution** — named
  Karnath for "Diagnostik und Kognitive Neuropsychologie" when it's **Hans-Christoph
  Nürk**; (2) CS **under-crawls MPI-IS** — missed Schölkopf (Empirical Inference) and
  Martius (Autonomous Learning). Profile steering visibly works (demoted oncology /
  IR / globalization-ethics correctly). **Verdict: AMBER** — aggregate gate met and
  the skill genuinely beats plain Claude, but Psych & CS miss 70% and need two skill
  fixes (person-attribution discipline; explicit MPI-IS/ELLIS crawl leg) before the
  gate turns green. Full writeup:
  `findings/no_db_universal_skill/2026-06-28-live-eval-results.md`.

- **2026-06-28** — Reassessed Task H. The eval ran in fixture mode only: the
  skill-arm conversations were hand-authored with the ground-truth names already
  in them, and the baseline arm was a scripted strawman (its "0%" run actually
  gave reasonable advice, e.g. naming the HIH). The 96%-vs-0% gap is therefore
  circular and does not validate live skill behaviour or a real advantage over
  plain Claude. Revised the Phase 1→2 gate to require a **live** measurement.
  Opened Task I (live validation) with a no-peeking protocol at
  `findings/no_db_universal_skill/2026-06-28-live-validation-protocol.md`.
  Decision: do Task I before Phase 2 (companies), so we don't build on an
  unvalidated university arm.

- **2026-06-27** — Task H done. Created fixture pairs for psychology (6 chairs), WiSo (7 chairs),
  and CS/ML (7 researchers) using scripted conversations. Extended the runner with
  PSYCHOLOGY_, WISO_, CS_GROUND_TRUTH constants, FACULTY_CONFIGS dict, score_structure()
  optional ground_truth param (backward-compatible), _run_single_faculty_comparison(),
  run_all_faculties_comparison(), and --discovery-comparison now runs all 4 faculties.
  12/12 tests still pass. Results: medicine 83% (5/6), psychology 100% (6/6),
  wiso 100% (7/7), cs 100% (7/7); baseline 0% all faculties; mean 96%. All four
  meet ≥70% target. One honest miss: Tabatabai (medicine, neurooncology — appropriate
  given neurodegeneration persona). Findings in
  findings/no_db_universal_skill/2026-06-27-eval-results.md.
  Phase 1 gate criteria met: no-DB, 4 ground-truth faculties, harness compares skill vs.
  baseline, recall ≥70%. Ready for Phase 2.

- **2026-06-27** — Task G done. Ported (already present) harness and extended it for discovery eval:
  Added `neuro-student` persona (Neurowissenschaften MSc, Parkinson's/Alzheimer's interest);
  `medicine-discovery-skill` and `medicine-discovery-baseline` scenarios; scripted fixture
  conversations for both arms; extended rubric with `discovery_coverage`, `discovery_relevance`,
  `discovery_structure` metrics; added `score_coverage()`, `score_relevance()`, `score_structure()`,
  `run_discovery_comparison()`, `--discovery-comparison` CLI flag to the runner.
  5 new tests added (12/12 total pass). First fixture run: skill arm 83% recall (5/6 HIH chairs),
  baseline 0% recall — gap +83pp. Comparison artifact written to
  `dist/codex-multiturn-evals/discovery-comparison/comparison.md`.
  Note: harness fixture mode requires no Codex/API; live Codex runs need `--runner codex-*`.

- **2026-06-27** — Task F done. Created eval ground truth for 4 faculties under
  `skills/tests/eval_ground_truth/`: Medicine (6 Hertie Institute professors, sample
  interest: neurodegenerative diseases + clinical brain research), Psychology (6
  Fachbereich Psychologie chairs, sample interest: cognitive neuroscience + decision-
  making), WiSo (7 chairs across Politikwissenschaft + Wirtschaftswissenschaft, sample
  interest: comparative politics + political economy). CS already covered by cs_seed/.
  Wrote README.md defining the recall metric: recall = surfaced / total ground-truth
  chairs, ≥70% target, step-by-step scoring guide, and what counts as "surfaced".
  All names verified against official uni-tuebingen.de and hih-tuebingen.de pages on
  2026-06-27. Four commits (one per faculty file + one for README).

- **2026-06-28** — `thesis-finder` made true single entry point. Step 1 now builds
  the student profile inline (one question per turn) instead of deferring to
  `build-student-profile`. Updated AGENTS.md (Student Workflow + thesis-finder
  guardrails), README.md (skill flow diagram), and thesis-finder/SKILL.md frontmatter
  + description. `build-student-profile` remains available as a standalone skill.

- **2026-06-27** — Task E done. Deleted `skills/match-thesis-advisors/` and
  `skills/update-openalex-paper-index/` (4 files; git history preserves them).
  Moved curated CS seed data (professors/, chairs/, researchers/) from
  `skills/find-university-chairs/references/` to
  `skills/tests/eval_ground_truth/cs_seed/` — now eval-only ground truth for
  Task F. Fixed two stale runtime references: `find-recent-papers/SKILL.md`
  (dead path to professors/INDEX.md) and `design-agent-skill/SKILL.md`
  (references to retired skills + seed-index-as-runtime-source).
  Final `grep -ri "backend|database|celery|fastapi|seed list" skills/` shows
  only prohibition statements, negations, and test files — no runtime deps.

- **2026-06-27** — Task D done. Rewrote `skills/find-university-chairs/SKILL.md` into a
  faculty-agnostic thesis-option discovery skill. Key changes: (1) description updated
  to cover all disciplines; (2) hard profile gate — all 6 dimensions required, else
  defers to build-student-profile; (3) faculty routing via search-strategy.md §2;
  (4) Pass 1 backbone crawl via tuebingen-faculty-backbone.md; (5) Pass 2 live
  enrichment using query skeletons from search-strategy.md §3–4; (6) quality filters,
  dedup rules, no-go exclusion (§5–7); (7) MAP output grouped by interest dimension
  with pros/cons, dated evidence, conversation starter, no-go flags; (8) honest
  coverage caveat; (9) all runtime references to seed files removed.

- **2026-06-27** — Task C done. Created
  `skills/find-university-chairs/references/search-strategy.md`: a reusable
  instruction set that turns a student profile into precise queries for all
  Tübingen faculties. Contains: (1) profile dimension → query variable mapping
  (interests/methods/domain/thesis-style/skills/no-gos); (2) faculty routing
  table (18 interest rows → primary + secondary faculty); (3) two-pass strategy
  (Pass 1: backbone crawl via `tuebingen-faculty-backbone.md` to get structured
  chair set; Pass 2: live enrichment for relevance, recency, openings); (4) 18
  query skeleton templates in 5 categories; (5) quality filters (source authority,
  date evidence, specificity); (6) dedup rules; (7) no-go exclusion table with
  detection signals; (8) required output structure; (9) two worked examples
  (Ethical AI/Education, Clinical Neuroscience) that can be followed by hand.

- **2026-06-27** — Task B done. Created
  `skills/find-university-chairs/references/tuebingen-faculty-backbone.md`: a
  reviewable table of all 7 Tübingen faculties + the Center for Islamic Theology,
  each with ≥1 official `uni-tuebingen.de` listing URL (Medicine on
  `medizin.uni-tuebingen.de`), page language, how chairs are listed, and a
  2026-06-27 last-checked date. Documented the two/three-level
  faculty→Fachbereich→chair nesting and per-department drill-down pattern. Spot-checked
  6 URLs live (faculties index, science & humanities Fachbereiche, WiSo Fächer, law
  Lehrstühle, Protestant-theology Lehrstühle) — all resolve and list real units.

- **2026-06-27** — Task A done. Edited `skills/build-student-profile/SKILL.md`: added one-question-per-turn rule, precise-answer instruction, and no-search gate (all six profile dimensions required before discovery). Surgical changes only; no other behavior modified.

- **2026-06-26** — Pivoted to the database-less, university-wide direction.
  Created branch `feat/no-db-universal-skill` off
  `codex/chair-discovery-eval-from-valentin`. Wrote
  [VISION_NO_DB.md](docs/thesis-report/01-the-pivot/2026-06-26-vision-no-db.md) and the findings set under
  `findings/no_db_universal_skill/` (concept-and-risks, exact build plan).
  Rewrote MASTERPLAN around Phase 1 = university discovery (Tasks A–H) and reset
  this STATUS. Located Max's multiturn eval harness on branch
  `eval/auto_eval_agents` (commit `ed341a7`) for the skill-vs-baseline comparison.
  Old DB data-foundation epic (issues #45–#51) is superseded; to be closed and
  replaced by issues mirroring Tasks A–H.

---

## Archived: former DB data-foundation phase (superseded 2026-06-26)

The previous Phase 1 built a scraped researcher tree (Prof → PhD → Paper) for CS
Tübingen with monthly refresh automation (issues #45–#51). It is superseded by the
database-less direction. The curated 3-pilot-chair ground truth and CS chair data
are retained as **eval-only** material (Task F). History remains in git.
