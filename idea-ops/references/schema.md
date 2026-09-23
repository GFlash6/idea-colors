# Data schema

Read this only for repair, migration, or relation-extension work.

`<workspace>/.ideas/ideas.json` is UTF-8 JSON:

```json
{
  "version": 1,
  "ideas": [
    {
      "id": "IDEA-20260914-103015",
      "title": "Short actionable title",
      "summary": "Original context",
      "status": "inbox",
      "next_action": "Smallest useful probe",
      "blocker": "",
      "created_at": "2026-09-14T10:30:15+08:00",
      "updated_at": "2026-09-14T10:30:15+08:00",
      "relations": [
        {"type": "depends-on", "target": "IDEA-20260914-102000"}
      ],
      "logs": [
        {"id": "LOG-20260914-110500", "at": "2026-09-14T11:05:00+08:00", "kind": "progress", "text": "完成首版布局验证", "source": "user", "after": [], "position": {"x": 90, "y": 140}},
        {"id": "LOG-20260914-111000", "at": "2026-09-14T11:10:00+08:00", "kind": "blocker", "text": "主控芯片缺货", "source": "user", "after": ["LOG-20260914-110500"]}
      ]
    }
  ]
}
```

Invariants:

- IDs are unique and stable.
- Every relation target exists and is not the source itself.
- Relations are unique by `(type, target)`.
- `flows-to↔comes-from` represents execution order. Multiple outgoing edges branch; multiple incoming edges converge; flow edges must remain acyclic.
- Inverses are maintained: `related↔related`, `conflicts↔conflicts`, `supports↔supported-by`, `depends-on↔unlocks`, `duplicate-of↔has-duplicate`, `flows-to↔comes-from`.
- `blocked` requires non-empty `blocker`; leaving `blocked` clears the current blocker but preserves logs.
- Only an explicit `log` action appends history. Creating, editing, or linking ideas does not append synthetic logs.
- New user-added logs carry `source: "user"`. Legacy system-generated logs may remain in stored data for compatibility but are not shown in the browser history graph.
- Every user log has a unique `id` and an `after` list containing zero or more existing log IDs from the same idea. Several logs naming one predecessor branch; one log naming several predecessors converges. The graph never infers edges.
- A user-positioned log may carry finite canvas coordinates in `position: {"x": number, "y": number}`; missing positions use automatic layout until the user drags the node.
- Timestamps are local ISO 8601 values with timezone offsets.
