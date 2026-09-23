# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: static HTML, CSS, and JavaScript served by the existing Python standard-library script so the skill remains portable and dependency-free.

## Users

Inferred from the user's brief: one person who produces many ideas every day and needs to capture them quickly, understand their execution state, record resistance and blockers, and connect related ideas.

## Product Purpose

Make ideas easy to remember without treating every idea as a commitment, then make the few active ideas easier to advance through explicit next actions, blockers, history, and relationships.

## Positioning

The same local idea graph is operable both through Codex conversation and a browser interface; neither surface creates a competing data store.

## Operating Context

The user captures ideas throughout the day, triages the inbox, advances a small active set, records friction as it occurs, and periodically reviews blocked, duplicated, parked, and connected ideas.

## Capabilities and Constraints

- Persist to the existing `<workspace>/.ideas/ideas.json` schema.
- Provide capture, search/filter, detail editing, resistance/blocker logging, and relation creation in the browser.
- Run locally without third-party packages or a cloud account.
- Chinese is the primary interface language; stored status and relation values remain schema-compatible English identifiers.
- Desktop-first and usable on mobile web.

## Evidence on Hand

The existing `SKILL.md`, schema reference, practice-pattern reference, Python CLI, and its tested JSON/database invariants. No commercial claims, brand assets, or user research beyond the conversation are available.

## Product Principles

- Capture first; decide commitment later.
- Show the smallest next action and the real blocker before decorative metrics.
- Preserve history and relationships rather than overwriting context.
- Keep local ownership and zero external dependencies.

## Accessibility & Inclusion

Keyboard-visible focus, semantic controls, readable contrast, reduced-motion support, and responsive layouts are required.
