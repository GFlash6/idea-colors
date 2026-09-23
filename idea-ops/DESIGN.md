# Idea Ops Design

## World

A quiet urban control map for thoughts: ideas are stations, execution is movement, and meaningful relationships form routes. The interface feels like a well-kept operations desk, not a decorative mind map or generic kanban board.

## Palette and material

- Warm paper ground `#F3F0E8`; ink `#1E2422`; white work surface `#FCFBF7`.
- Primary route green `#176B52`; active blue `#246BCE`; blocked vermilion `#C64B35`; parked ochre `#9A7424`.
- Flat color and crisp 1px rules. Shadows only for lifted overlays, never routine containers.

## Typography

Use a system sans stack for Chinese and Latin UI. Titles are compact and confident; labels use ordinary casing. IDs and timestamps may use the system monospace because they are machine identifiers.

## Composition

- Desktop: narrow navigation/status rail, wide idea list, contextual detail inspector.
- Mobile: status filters become a horizontal strip; list and detail become sequential views.
- A thin route line runs through status counts and continues into relation rows. It is functional wayfinding, not background decoration.
- The list is the primary working surface; a relation map is contextual and never displaces readable records.

## Components and state

- Controls use 10–12px corners; compact filters may be capsules.
- Every idea row exposes title, status, next action or blocker, and updated time.
- Selected rows use a pale route tint plus a solid station marker.
- Blocked items reserve vermilion for the marker and blocker text, not the whole surface.
- Focus rings are high-contrast green with visible offset.

## Motion

Use 180–220ms state transitions. Selecting an idea draws its route line once; reduced-motion users receive an immediate state change. No decorative entrance sequence.

## Voice

Chinese, concise, operational, and concrete. Prefer “下一步” and “具体阻塞” over motivational language.
