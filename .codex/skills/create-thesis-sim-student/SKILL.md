---
name: create-thesis-sim-student
description: Create new repo-local thesis-finder simulation student commands. Use when asked to add, scaffold, draft, or generate a new simulated thesis-finder student persona for Claude and Codex.
metadata:
  internal: true
---

# Create Thesis Simulation Student

Create one new thesis-finder simulation student in a uniform format, then write
matching repo-local commands for Claude and Codex after the user approves the
profile.

## Output Files

After approval, create both files:

- Claude command: `.claude/commands/thesis-sim-{slug}.md`
- Codex prompt: `.codex/prompts/thesis-sim-{slug}.md`

Both files must have identical body content except for client-specific path
placement. Use `references/student-command-template.md` as the template.

## Workflow

1. Gather or infer the requested student concept.
   - Accept a full profile, a short idea, or constraints such as "concise",
     "medicine", "theory-heavy", "no company fit", or "social sciences".
   - If required details are missing, make a reasonable draft instead of
     starting with a long questionnaire.
2. Draft the complete student profile first.
   - Do not write files yet.
   - Include all required profile fields from the schema below.
   - Make the student usable for any Tuebingen department; do not default to
     computer science, machine learning, or company theses.
   - Treat "no realistic company track" as a valid track preference.
3. Ask for approval.
   - End the draft response with a concise approval question.
   - If the user requests changes, revise the profile and ask again.
4. After explicit approval, create the command files.
   - Generate a lowercase slug from the student name or requested label.
   - Use only lowercase letters, digits, and hyphens.
   - If a command file already exists, stop and ask before overwriting.
   - Write both Claude and Codex files.
5. Verify.
   - Confirm both files exist.
   - Confirm the Claude and Codex command bodies are identical.
   - Confirm the command filenames match `thesis-sim-{slug}.md`.
   - Do not run the simulation unless the user asks.

## Student Profile Schema

Every drafted student must include:

- **Name**
- **Faculty / field**
- **Primary test focus**
- **Response style**
- **Initial user message**
- **Interests**
- **Methods**
- **Domain**
- **Thesis style**
- **Skills**
- **No-gos**
- **Hidden tension**
- **Disclosure rules**
- **Track preference**: university, company, both, or no realistic company track
- **Expected good behavior**: what a successful `thesis-finder` run should do

## Command Content Requirements

Each generated command must instruct the agent to:

- run a full end-to-end `thesis-finder` simulation
- simulate both sides until the natural endpoint
- answer in-character from the hidden profile
- build all six profile dimensions before discovery
- route by the student's department and evidence
- avoid assuming CS/ML/company fit
- avoid inventing chairs, openings, datasets, contacts, or advisor capacity
- avoid writing fictional student data into real runtime session files
- assert that no old thesis-finder session was read, resumed, or written
- include a session-persistence check in the report
- return a standalone Markdown report

## Safety Rules

- These are fictional simulation personas, not real students.
- Do not put private real student data into command files.
- Do not invent facts about Tuebingen departments, chairs, companies, or thesis
  availability while drafting the persona.
- Keep commands department-universal: humanities, law, theology, medicine,
  natural sciences, social sciences, economics, and computer science should all
  be representable.
