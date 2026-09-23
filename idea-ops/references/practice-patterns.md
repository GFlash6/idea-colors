# Practice patterns

Use this when changing review policy or diagnosing system decay.

The workflow combines patterns that have held up in mature systems:

- Linear separates intake/triage from committed workflow, keeps statuses finite, and models `blocked`, `blocking`, `related`, and `duplicate` as distinct relations.
- GitHub Issues separates structured fields from issue content, supports dependencies and sub-issues, and recommends focused views and work-in-progress limits.
- Notion supports self-relations and two-way relations, showing why inverse links should be maintained automatically.
- Atlassian treats a backlog as living and reprioritized from feedback; a static, rarely shared backlog is an explicit anti-pattern.

Sources:

- https://linear.app/docs/triage
- https://linear.app/docs/configuring-workflows
- https://linear.app/docs/issue-relations
- https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects
- https://www.notion.com/en-gb/help/relations-and-rollups
- https://www.atlassian.com/agile/scrum/backlogs/

## Failure patterns and corrections

| Failure | Correction |
|---|---|
| Capture requires a business case, score, and plan | Make title the only required user content; enrich later. |
| Every idea becomes active | Capture to inbox; cap active work at three during review. |
| Statuses encode every nuance | Keep seven lifecycle states; record nuance in logs. |
| “Blocked” becomes a synonym for difficult | Require a named stopping condition and a blocker-facing next action. |
| Relations become a topic-tag soup | Add a link only when it changes sequencing, evidence, or choice. |
| Duplicates fragment evidence | Point duplicates to one canonical idea and keep the history. |
| The backlog only grows | Triage daily; park/drop/merge during weekly review. |
| Updates overwrite the past | Keep current fields plus append-only event logs. |

