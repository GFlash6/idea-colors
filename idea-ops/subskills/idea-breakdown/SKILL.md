---
name: idea-breakdown
description: Child skill of idea-ops that progressively turns an early idea and goal into achievable steps, dependencies, and acceptance criteria on the existing editable idea canvas. Use for requests to break an idea down, explain the implementation path, or draw its steps.
---

# 想法拆解与画布展示

Use this as a child workflow of [Idea Ops](../../SKILL.md). The parent supplies intake, workspace resolution, storage, and browser access. Paths below are relative to the parent skill directory. This is a workflow module, not a request to spawn a subagent.

## 从目标倒推，逐步展开

1. Read the idea brief and existing nodes first. Establish the intended outcome, an observable success criterion, known resources, and uncertainty. If the idea is vague, propose the smallest validation experiment before a detailed implementation plan. Keep missing constraints visible; do not invent dates, budget, tools, or user commitments.
2. Identify the smallest useful first version. Create a short path of meaningful outcomes, then expand the nearest actionable outcome into steps a person or Codex can actually perform. Leave distant or uncertain stages coarse. Do not prescribe a fixed step count or generate a huge task tree just because it is possible.
3. Each actionable step must say what to do, what it produces, and how to tell it is done. Split a step further when it contains independent work or its starting action is unclear. Record prerequisites only when they are real dependencies. If execution cannot begin, identify the smallest action that resolves the uncertainty.
4. Distinguish sequential work, independently executable branches, and merges that need all their incoming prerequisites. Alternative approaches are choices: label them as alternatives and add a decision step; do not draw an AND-merge that suggests every alternative must be implemented.
5. Set one smallest next action. Planning alone does not change the idea to `active` or mark work complete. If the user only asked for a plan, stop after saving and displaying it; implementation requires an execution request.

## 映射到现有画布

Keep one idea as one project; its steps are `logs` inside that project. Do not use `capture --after` or idea-level `flows-to` for these steps: the current canvas renders log-level `after` edges, not cross-idea relations.

- Proposed work: `kind: step`, text starts with `【AI建议·待执行】` and a short action title. Follow it with newlines for `产出：…`, `验收：…`, and relevant `前提：…` / `待确认：…`. The existing node card displays and edits the full text. Do not add unsupported schema fields for titles or acceptance criteria.
- Goal/approach choices: `kind: decision`, clearly marked as user-stated or proposed. A goal is not a completed progress event.
- Actual progress, resistance, blockers, and lessons use the existing matching types only when supported by the conversation. A potential risk is text on a proposed step, not an invented blocker event.
- Use `after: []` for roots, one real predecessor for sequential steps, a shared predecessor for branches, and several predecessors for a real convergence. Retain stable IDs and manual positions. Let existing automatic layout position new nodes.
- The legacy storage writes explicit records as `source: user` even when Codex enters them. This field does not prove authorship. Preserve the `AI建议` label in text; never describe such nodes as user-confirmed or completed merely because they were saved.

## 持久化和展示

1. Use the parent's selected store. In workspace mode, run `init`, `list` / `show`, then `capture` or `update --summary` as needed. Pass multiline content as an argument through a safe subprocess argument list or a structured API body; never interpolate conversational text into shell code.
2. Append nodes with `log IDEA-ID --kind step --text TEXT [--after LOG-ID ...]`. `log` prints a message, not the new node ID: run `show IDEA-ID` and inspect the saved record before linking descendants. In server mode, the equivalent `POST /api/ideas/IDEA-ID/log` returns the updated idea. Do not guess IDs or add independent branches concurrently.
3. Before each retry, read current records to avoid duplicate steps. On a repeated request, reuse matching saved nodes. For edits use server `POST /api/ideas/IDEA-ID/log-update` with `{log, kind, text}`; this preserves its ID and edges. Keep completed history and explicit user edits. Mark a replaced proposal as superseded instead of deleting it without a deletion request. For topology changes use existing link/unlink operations and check cycles.
4. Update `next_action` with the first executable step. If maintaining the overview's `next_steps` list, preserve existing entries and `done` values; read and merge through the existing API rather than replace the whole list from memory. That list does not automatically mirror canvas nodes, so do not claim it does.
5. Read the saved project back: confirm the brief, AI labels, acceptance criteria, valid predecessor IDs, branch/merge semantics, and absence of duplicates. Run `offline` after the final workspace write, then use the parent's file-URL workflow to open the same project's canvas and inspect it. Do not launch `serve` merely to show the result. Existing file-URL data must instead be edited and verified in that standalone page.
6. Return a concise explanation of the goal, the first next action, and where the editable canvas is open. Report partial saving or unavailable visual verification truthfully; do not claim to have drawn the result based solely on a textual plan.

## 行为验收示例

- “有个想法，用小工具帮我记灵感，先记着”：parent captures known intent and unknown success criteria; no automatic plan.
- “把这个想法拆成能做的步骤并画出来”：save a proposed minimal path with outputs and checks; parallel work shares a parent and joins only at a genuine dependency; open the editable canvas.
- “刚才的步骤再细一点”：read existing IDs, expand the selected uncertain/actionable part, preserve other nodes and user positions; repeating the request creates no duplicate plan.
- “验证发现数据拿不到”：record the actual finding and blocker when applicable, propose an unblock action, revise affected future steps without marking planned steps as completed.
