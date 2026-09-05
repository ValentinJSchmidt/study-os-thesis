---
name: run-thesis-simulations
description: Run and evaluate all repo-local thesis-finder simulation commands. Use when asked to run the thesis simulation suite, evaluate thesis-finder personas, execute all thesis-sim commands, or produce conversation and rating artifacts.
metadata:
  internal: true
---

# Run Thesis Simulations

Run every repo-local `thesis-sim-*` command as an end-to-end `thesis-finder`
simulation, save the complete conversations, evaluate each run, and write a
central evaluation summary.

## Inputs

- Optional user request limiting the run to selected students or clients.
- Repo-local command files:
  - Claude: `.claude/commands/thesis-sim-*.md`
  - Codex: `.codex/prompts/thesis-sim-*.md`

## Workflow

1. Decide the artifact root.
   - Default: `.simulations/current`.
   - For before/after architecture comparisons, use
     `.simulations/baseline/{timestamp}` for the pre-change run and
     `.simulations/rules-only/{timestamp}` for the post-change run.
2. Discover simulation commands.
   - Prefer the command directory for the active client:
     - Claude: `.claude/commands/thesis-sim-*.md`
     - Codex: `.codex/prompts/thesis-sim-*.md`
   - If the active client's directory is missing or empty, use the other one.
   - Sort commands by filename for deterministic order.
   - Exclude orchestration commands or non-student commands; run only files
     matching `thesis-sim-*.md`.
3. For each command file:
   - Read the complete file.
   - Treat the command content as a **harness-private** specification. It is
     never part of the prompt or visible context for the assistant under test.
   - Run the conversation with a black-box split:
     - The harness knows the persona, hidden profile, disclosure rules, rubric,
       artifact paths, and stop conditions.
     - The assistant under test sees only the normal student-facing transcript:
       the initial user message plus later student replies.
     - Generate assistant turns from a fresh assistant context that has access to
       the repository's normal thesis skills, but does not receive the command
       file, hidden profile, expected-good-behavior notes, rubric, scores,
       artifact requirements, or any statement that it is being simulated or
       evaluated.
     - Generate student turns separately from the harness-private persona.
   - Use the repository's actual thesis skills in the assistant-under-test
     context when the visible student conversation triggers them.
   - Do not write fictional student data to real runtime state. The current
     `thesis-finder` skill is fresh-session only: the assistant under test
     should not read, write, summarize, or resume `~/.claude/thesis-finder/session.md`
     or local fallback session files. Record a session-persistence check in the
     artifact instead of would-be session content.
4. Save the complete conversation.
   - Directory: `{artifact-root}/convo`
   - Filename format: `{student-slug}_conversation_dd.MM.YYYY-HH-mm-ss.md`
   - Use the lowercase student name or command slug, for example
     `maja_conversation_28.07.2026-22-10-06.md`.
   - Generate the timestamp at write time.
   - If a filename collision occurs because two files are written in the same
     second, wait until the next second and retry. Do not add student names or
     counters to the filename.
5. Evaluate the conversation using `references/evaluation-rubric.md`.
   - Directory: `{artifact-root}/rating`
   - Filename format: `{student-slug}_rating_dd.MM.YYYY-HH-mm-ss.md`
   - Use the same student slug as the conversation file.
   - Each rating file must identify the student/command inside the Markdown
     body, not in the filename.
   - Use the same collision rule as conversation files.
   - Include diagnostic fields:
     `Verified URLs: N`, `Unconfirmed claims: N`, `Wall-clock seconds: N`
     when measurable, `Company/CS misrouting: yes|no` for Jan, Simon, and
     Maja, and `Both tracks or structural company limit: yes|no` for Tina.
6. After all individual ratings are saved, write one central evaluation file.
   - Directory: `{artifact-root}/rating`
   - Filename format: `central_rating_dd.MM.YYYY-HH-mm-ss.md`
   - Title it `# Central Thesis Simulation Evaluation`.
   - Summarize pass/fail, scores, recurring skill failures, and recommended
     improvements across all students.
7. For before/after comparisons, run
   `python scripts/compare_command_simulation_performance.py --baseline-dir .simulations/baseline/{timestamp} --candidate-dir .simulations/rules-only/{timestamp}`
   and include the comparison verdict in the central summary.

## Conversation Artifact Requirements

Conversation files are primarily for human and LLM review. Use the readable
turn-based report format as the default:

- `# Thesis Simulation Conversation`
- `Command: ...`, `Student: ...`, `Timestamp: ...`, and `Track chosen: ...`
- `## Test Setup`
- `## Full Simulated Conversation Transcript`
  - Use numbered turn headings such as `### Turn 1: User` and
    `### Turn 2: Assistant`.
  - Keep the transcript easy to read as a dialogue. Do not hide evidence in
    later artifact-only sections if it is required for the student-facing skill
    output.
- `## Completed Six-Dimension Student Profile`
- `## Protocol Followed`
- `## University Chair Options`, if explored
- `## Company Thesis Options`, if explored
- `## Recommended Top Option` or explicit no-fit result
- `## Drill-Down After Student Selection`, if the student asked to go deeper
- `## Final Thesis Topic Plus Chair`, if evidence supports one
- `## Outreach Angle`
- `## Validation`
- `## Sources Used`
- `## Session Persistence Check`

The `## Validation` section must make artifact checks explicit:

- `Pre-write validation: PASSED|FAILED`
- `Evidence visible in student-facing transcript: yes|no`
- `Verified URLs counted from Assistant turns: N`
- `Option-map fields present: yes|no`
- `Topic menus / possible thesis angles present: yes|no`
- `Drill-down branch followed after go-deeper: yes|no|not requested`
- `Session persistence avoided: yes|no`
- `Harness mode: black-box subagent | in-process fallback | other`
- concise validation errors if any

When live discovery produces a university option map, the student-facing
Assistant turn must visibly include official URL, relevant person, unit type,
relevance rationale, pros/likely difficulties, method fit, dated evidence,
conversation starter, and no-go flags for each included option. Strong or
recommended options must also include possible thesis angles/topic menu; thin
options must say that evidence is insufficient for concrete angles. When live
discovery produces a company map, the Assistant turn must visibly include
company, division/team when known, sector tags, size, confirmed BW location or
scope, relevance rationale, pros/likely difficulties, method fit, contact path
or official URL, research focus or `not found`, thesis signal, and no-go flags.
Strong or recommended company options must also include possible thesis
angles/topic menu; thin options must say that evidence is insufficient for
concrete angles.
Sources listed only in `## Sources Used` do not count for evidence discipline.

If any user turn after the recommendation says they want to "go deeper",
"go deeper before outreach", "learn more", or equivalent, the next assistant
turn must visibly perform the drill-down before offering `draft-thesis-contact`.
A valid drill-down includes a heading or clearly labeled section such as
`## Deeper Look: ...`, evidence anchors or an explicit "not found" statement,
what the student would likely work on or learn, feasibility checks, 2-4 topic
variants, and one first-meeting question. A generic outreach angle or immediate
`draft-thesis-contact` offer does not count and must make pre-write validation
fail.

## Rating Artifact Requirements

Each individual rating file must include:

- command filename and student name
- timestamp
- short verdict
- score table using the rubric
- evidence-grounded notes for each score
- issues, failure modes, or missing evidence
- concrete skill/package improvement suggestions

If any assistant turn or artifact checks old thesis-finder sessions, reads a
runtime session file, resumes old candidates, writes session state, or records
would-be session content, mark pre-write validation failed and score
**Workflow compliance** no higher than 1.

When the transcript skips the go-deeper branch after the student requested it,
score **Workflow compliance** no higher than 1 and **Conversation usefulness**
no higher than 1, even if the option map itself is well evidenced.

## Evidence And Safety Rules

- Do not invent chairs, companies, thesis openings, datasets, contacts,
  supervision capacity, application deadlines, or source evidence.
- Treat "no realistic company track" as a valid outcome for departments where
  company theses are structurally weak.
- For rules-only backbone evaluations, judge whether live discovery found
  profile-relevant verified candidates without relying on static company or
  faculty URI lists.
- Do not assume computer science, machine learning, or company fit. Route by
  the simulated student's department and profile.
- Keep generated fictional data only under the selected artifact root's
  `convo/` and `rating/` subdirectories, for example
  `.simulations/current/convo`, `.simulations/baseline/{timestamp}/rating`, or
  `.simulations/rules-only/{timestamp}/rating`. These paths must be gitignored.
- If web access is unavailable but the command requires live evidence, mark the
  affected ratings down under evidence discipline and state the limitation.
