---
name: my-skill
description: "<What the skill does, in one sentence>. Use when <the task, files, or stack that should trigger it>."
metadata:
  title: "My Skill"
  category: "Engineering"
  tier: practice
  trigger_keywords: "keyword one, keyword two, keyword three"
---

<!--
Skeleton for a new skill. Copy this folder to skills/<name>/ (the folder name and `name` must
match: lowercase letters, digits, single hyphens), then fill every section.

Frontmatter rules (checked by `python tools/skillpack validate`):
- description: what it does AND when to use it, <= 300 characters. Agents choose skills from
  this line alone; a vague or long description gets the skill skipped or crowded out.
- metadata.tier: one of the tiers in catalog.json (persona, process, practice, supporting,
  cloud-gcp, constitution, meta).
- metadata.category: Process & Governance, Engineering, Quality, Operations, Data-ML,
  Management, Engineering/Management, Cloud Provider – GCP.
- metadata.routing (optional): a short note shown in the orchestrator index.
- metadata.install: "optional" (optional) installs the skill only on request (--with).

Body rules: the nine sections below, in this order, under 500 lines. Put long material in
references/ (read on demand) and executable checks in scripts/, linked by relative path.
Refer to other skills by backticked folder name. No project specifics (names, hosts, ports,
tables, incidents): they belong in a project copy's tailoring block.
Then run: python tools/skillpack build && python tools/skillpack validate
Delete this comment.
-->

## Role Identity

<Who this skill is, in two or three sentences: the question it owns and what it leaves to other skills.>

## Responsibilities

- <Concrete duty, phrased as an action, with the one-line reason it matters.>

## Technical Skill Set

- <Tools, standards, and techniques, each with when to reach for it.>

## Decision-Making Lens

- <How it weighs trade-offs; what it optimises for; what it refuses to trade away.>

## Trigger Signals

- **Keywords:** <phrases in a request>.
- **Files/paths:** <globs or folders>.
- **Project context:** <stack signals>.

## Collaboration Behavior

- <Which skills it co-loads with, hands off to, or defers to, by backticked name.>

## Output Style / Conventions

- <What its output looks like: formats, required sections, evidence it must show.>

## Anti-Patterns

- <Specific mistakes to refuse, each with why.>

## Stack Detection & Adaptation

- <How it detects the project's stack and adapts; what it verifies as current rather than assuming.>
