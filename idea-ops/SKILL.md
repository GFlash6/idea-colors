---
name: idea-ops
description: Capture early ideas and goals through conversation, progressively break them into achievable steps, and show them on the existing editable idea canvas. Also track progress, resistance, blockers, relationships, and reviews. Use when the user wants to remember an idea, clarify what to build and why, break an idea down, draw its execution path, or continue an existing idea. Do not use for ordinary task lists with no idea-development context.
---

# Idea Ops

Turn a high-volume stream of ideas into a trustworthy local operating system. Store facts first; help the user choose what to advance only during review.

## Conversation routing

- “我有个想法 / 帮我记下来”: capture a durable idea brief using the intake workflow below. A vague idea is enough to start.
- “帮我拆解 / 一步步怎么实现 / 画出来”: load the child skill [idea-breakdown/SKILL.md](subskills/idea-breakdown/SKILL.md), then save the proposed steps into this idea's existing canvas.
- “记录并拆解展示”: run intake and the child skill in one turn. Saving and drawing the requested plan needs no extra approval.
- “先记着，不要拆”: capture only. Do not turn early exploration into a commitment to execute.
- On continuation, read the existing idea before updating it; retain its ID, history, and manually positioned nodes.

## Storage

Use `scripts/idea_ops.py` (CLI or its server API) for workspace mutations. It stores data at `<workspace>/.ideas/ideas.json` and regenerates `<workspace>/.ideas/DASHBOARD.md`. Default `<workspace>` to the current working directory unless the user names another location.

Before the first mutation, run `init`. Do not hand-edit the JSON unless repairing corruption. Read [references/schema.md](references/schema.md) only when repairing data, migrating it, or adding a new relation type.

## Browser interface

Default to `file://` for both everyday use and displaying conversationally recorded ideas. After completing workspace mutations, run:

```powershell
python <skill>/scripts/idea_ops.py --root <workspace> offline
```

This writes `assets/offline-inbox.js` with the current workspace snapshot and opens the existing `assets/index.html` file directly. It starts no server. Use `--no-open` when a browser tool will navigate to the printed file URL. Reuse the exact original HTML path and browser profile to retain the user's existing local records. Refresh an already-open file page after preparing a new handoff. The inbox contains the last prepared workspace; previously accepted browser records remain in local storage.

The page adds new IDs, recognizes repeated handoffs, and updates an existing project only when browser content has not diverged from the last accepted snapshot. Manual node positions survive updates. Conflicting projects are retained locally with a visible notice; never claim they have synchronized. Missing projects do not imply deletion, and locally deleted projects are not silently resurrected. Invalid local storage stops writes instead of resetting to an empty database.

Browser edits remain in browser-local storage. The home page's “导出本地备份” downloads a JSON file; it does not silently write back to the workspace. Before continuing a browser-edited idea through Codex, read the user-provided exported file, compare it with the workspace, and merge the requested records through `scripts/idea_ops.py` functions or CLI, preserving IDs and graph validity. Do not blindly replace the database or infer deletion from omission. If the same field has incompatible edits, preserve both and ask which version to retain. Prepare `offline` again after resolving the changes. Be explicit that this is local handoff, not live bidirectional synchronization.

The interface is a two-pane layout: a project list on the left and a detail workspace on the right. The top contains the brand, a compact status filter, and a single capture bar for new root ideas.

Each project is rendered as a horizontal multi-branch event map: time flows left to right, each branching path opens above or below the trunk, and converging paths rejoin at the midpoint. Nodes are large colored circles labeled with their text and record type directly beneath them; edges are uniform curved lines connecting one event to the next. Node colors follow the record type: blue for steps, green for progress, orange for resistance, red for blockers, violet for decisions, and cyan for lessons. The map scrolls horizontally as it grows. Selecting a node attaches the next record after it and highlights it with a ring.

Only one input form is used for adding records: choose a type, write the text, and submit. New records are attached after the currently selected node by default; choosing multiple parent nodes in the detail panel creates a merge/convergence. Project metadata (title, status, next action, blocker) is edited inline.

Render only user-added records. Creating or linking records must not create synthetic history entries. Cycles are rejected. The newest record is selected by default, and the graph scrolls to keep it visible.

The simplified browser view no longer renders cross-idea relations or idea-to-idea `flows-to` links. Those relations are still preserved in the workspace file and remain available through the CLI.

Only use `serve` when the user explicitly requests server mode or live browser/CLI synchronization. A request to record, break down, draw, or open an idea is not authorization to make server mode the default.

Follow the browser skill to open the printed **file URL**, select the intended project and its “画布” tab, and check the saved title, nodes, and edges. If browser policy blocks local-file automation, respect the block and provide the local HTML link for the user to open; do not switch automation surfaces or start a port as a workaround. Report unavailable visual verification truthfully. Do not replace the editable canvas with a static diagram.

## Core workflow

### Capture

When the user expresses an idea they want retained:

1. List/search existing ideas first to distinguish continuation from a new idea. Capture immediately with a concise title; do not require a questionnaire before saving.
2. Preserve the user's original expression and a compact brief in `summary`: 原始想法、具体想做什么、为谁/解决什么问题、目标与成功标准、已知条件/限制、待澄清、AI建议. Include only relevant sections; unknown goals or criteria remain “待明确”. Attribute suggestions explicitly instead of presenting them as the user's words. This summary appears in the existing project overview and can be edited there.
3. Ask only the next question that materially changes the goal or feasible path, usually one or two at a time. Use what the conversation already contains. Save what is known while waiting; merge later answers into the same summary without discarding meaningful context. When intent changes materially, record the reason as a decision rather than silently rewriting history.
4. Default status to `inbox`. Do not force priority, estimates, or a full plan during capture.
5. Add a concrete `next_action` only when the user supplied one or it is an obvious, reversible first probe.
6. Return the saved title, goal and next action briefly, with a link to the workspace dashboard or opened canvas. If decomposition was requested, continue into the child skill before concluding.

```powershell
python <skill>/scripts/idea_ops.py --root <workspace> capture --title "..." --summary "..." --next-action "..." --after IDEA-PREVIOUS-STEP
```

### Execution flows, branches, and convergence

Model both ideas and their execution steps as nodes in a directed flow. `flows-to` points to a next step and `comes-from` is its inverse. Multiple outgoing `flows-to` links form branches at any depth. Multiple incoming `comes-from` links form a convergence step. Reject links that create cycles.

For example: `AI keyboard → purchase materials → {chips, components, enclosure} → PCB fabrication → soldering → {board A issue, board B issue} → verification`. Keep a step as one node when it has one status, blocker, and next action; split it when parts can progress or fail independently.

### Advance or record reality

Use `update` for current state and `log` for history. A status change does not replace the log of what happened.

- Allowed statuses: `inbox`, `exploring`, `active`, `blocked`, `parked`, `done`, `dropped`.
- When setting `blocked`, record a specific blocker with `--blocker`; name the missing decision, resource, dependency, evidence, or external event.
- Record encountered friction with `log --kind resistance`. Record planned steps with `log --kind step`. Record a hard stop with `log --kind blocker` and synchronize the current blocker/status when appropriate.
- Keep exactly one smallest useful next action for `exploring`, `active`, and `blocked` ideas. For a blocked idea, the next action should reduce, route around, or monitor the blocker.

```powershell
python <skill>/scripts/idea_ops.py --root <workspace> update IDEA-ID --status blocked --blocker "Waiting for API access" --next-action "Ask the owner for sandbox credentials"
python <skill>/scripts/idea_ops.py --root <workspace> log IDEA-ID --kind resistance --text "Setup took longer because the SDK lacks examples"
python <skill>/scripts/idea_ops.py --root <workspace> log IDEA-ID --kind progress --text "Branches converged" --after LOG-BRANCH-A --after LOG-BRANCH-B
python <skill>/scripts/idea_ops.py --root <workspace> link-log IDEA-ID LOG-SOURCE LOG-TARGET
python <skill>/scripts/idea_ops.py --root <workspace> unlink-log IDEA-ID LOG-SOURCE LOG-TARGET
python <skill>/scripts/idea_ops.py --root <workspace> delete-log IDEA-ID LOG-ID
python <skill>/scripts/idea_ops.py --root <workspace> move-log IDEA-ID LOG-ID 420 180
```

### Connect

Link ideas only when the relationship changes understanding or action. Use one of:

- `related`: useful context, symmetric.
- `supports`: evidence or capability strengthens another idea.
- `conflicts`: pursuing both creates a real trade-off, symmetric.
- `depends-on`: the source needs the target first; use for idea-level blocking.
- `duplicate-of`: the source repeats the target; keep one canonical idea.
- `flows-to`: the target is a next execution step; several targets branch and several sources may converge on one target.

The script maintains inverse links. Never create a relation merely because two ideas share a broad topic.

```powershell
python <skill>/scripts/idea_ops.py --root <workspace> link IDEA-A supports IDEA-B
```

### Review

Run `list` or `show` to gather facts. For daily review, triage new items, inspect blockers, and choose no more than three active ideas. For weekly review, also merge duplicates, park stale low-value ideas, and inspect dependency/conflict chains.

Base recommendations on value, evidence, effort, reversibility, current momentum, and blocker cost. Never silently change status during a review; present proposed changes unless the user asked to apply them.

Read [references/practice-patterns.md](references/practice-patterns.md) when designing a new review policy or diagnosing why the system has become noisy.

## Operating rules

- Separate capture from commitment: an idea in `inbox` is remembered, not promised.
- Separate resistance from blockers: resistance raises cost; a blocker prevents the next meaningful step.
- Prefer observable statements: “needs legal approval from X” beats “bureaucracy”.
- Preserve history. Mark ideas `dropped` or `parked` instead of deleting them unless the user explicitly requests deletion.
- Detect likely duplicates by listing/searching first; ask or explain when merging is ambiguous.
- Do not invent progress, blockers, evidence, or relationships. Mark inferences as proposals.

## Effective vs ineffective records

| Effective | Ineffective |
|---|---|
| `blocked: waiting for vendor rate-limit increase; next: test batch size 20` | `blocked: technical issue` |
| `resistance: interview recruiting costs ~2 hours/person` | `this is hard` |
| `IDEA-A depends-on IDEA-B` because B supplies required data | linking everything with the same tag |
| capture to `inbox`, decide during review | marking every exciting idea `active` |
| `dropped` with a decision log | deleting failed ideas and losing the lesson |
