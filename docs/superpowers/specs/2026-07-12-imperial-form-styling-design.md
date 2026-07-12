# Imperial-Themed Grouped Input Form — Design

**Date:** 2026-07-12
**Component:** `frontend/src/pages/Inputs.js`
**Goal:** Restyle the 25-field model input form into grouped, boxed sections with a clean Imperial College London theme. Round all edges, including the results table.

## Problem

`Inputs.js` renders 25 number inputs as one flat `FIELDS.map(...)` list inside a dark, full-screen, vh-centered `.App-header` with white text and an oversized font. It is hard to scan, unthemed, and the parallel `DESCRIPTIONS` array is coupled to `FIELDS` by index.

## Theme — "Light Imperial"

Repurpose `.App-header` from a dark full-screen hero into a light page: white background, dark text, left-aligned content in a centered `max-width` column. Add a slim Imperial-blue header bar with the title "Life-Cycle Portfolio Model".

Palette (CSS variables in a new `Inputs.css`):

| Variable | Value | Use |
|---|---|---|
| `--imperial-blue` | `#003E74` | header bar, box headers, borders, submit button |
| `--imperial-blue-dark` | `#002A52` | hover / active states |
| `--imperial-light-blue` | `#0091D4` | focus rings, links |
| `--cool-grey` | `#EBEEEE` | box / input backgrounds |
| `--border-grey` | `#d5dade` | borders, table gridlines |
| `--text` | `#232333` | body text |
| `--muted` | `#5b6470` | field descriptions |
| `--radius` | `10px` | shared corner rounding |

Rounded corners (`--radius`, with smaller radii for inputs/cells) apply to boxes, inputs, buttons, and the results table (rounded outer frame via `border-radius` + `overflow: hidden` on a wrapper so header/rows clip cleanly).

## Structure — the "boxes"

Add a `group` key and fold each description into a `desc` key on every `FIELDS` entry (replacing the parallel `DESCRIPTIONS` array — confirmed with user). Render one `<fieldset>` box per group.

Six groups, in form order:

1. **Life horizon** — `tb`, `tr`, `td`
2. **Preferences** — `rho`, `delta`, `psi`
3. **Market & returns** — `r`, `mu`, `sigr`
4. **Income risk** — `smay`, `smav`, `corr_v`, `corr_y`
5. **Income profile & retirement** — `ret_fac`, `aa`, `b1`, `b2`, `b3`
6. **Solver settings** — `ncash`, `na`, `nc`, `n`, `maxcash`, `mincash`, `nsim`

Each box: white card, `--border-grey` border, subtle shadow, rounded corners, an Imperial-blue header (`<legend>` or styled heading). Inside: a responsive 2-column grid (`grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`) collapsing to 1 column on narrow screens. Grid cells top-align (`align-items: start`) so uneven descriptions stay tidy.

Each field cell: label on top, full-width number input (rounded, blue focus ring), description underneath in muted small text (always visible, per user choice).

## Buttons & results

- **Submit:** solid Imperial-blue, rounded, hover-darken to `--imperial-blue-dark`.
- **Algorithm Details** (two buttons): secondary outlined-blue style, grouped on one row.
- **Results table:** convert inline `thStyle`/`tdStyle` to CSS classes. Imperial-blue sticky header row with white text, zebra-striped rows, `--border-grey` gridlines, wrapped in a rounded, clipped, scrollable container.
- **Error message:** keep red, styled to match.

## Files touched

- **New:** `frontend/src/pages/Inputs.css`
- **Edit:** `frontend/src/pages/Inputs.js` — add `group`/`desc` to `FIELDS`, remove `DESCRIPTIONS`, restructure render into grouped `<fieldset>`s, replace inline `thStyle`/`tdStyle` objects with classNames, import `./Inputs.css`.
- **Edit:** `frontend/src/App.css` — lighten `.App-header` (white bg, dark text, top-aligned, normal font size) so the page reads as a light Imperial page.

## Non-goals (YAGNI)

- No tooltips / collapsible descriptions (user chose always-visible).
- No field validation changes, no logic changes to `handleSubmit`.
- No Imperial logo image (text wordmark only).
- No changes to `index.css` font stack.

## Testing / verification

- `npm start` in `frontend/`; visually confirm: six rounded boxes, 2-column grid collapsing on narrow width, Imperial-blue theme, blue focus rings, rounded submit/secondary buttons.
- Submit the form (backend on `localhost:8000`) and confirm the results table renders with rounded corners, blue sticky header, and zebra rows. If backend is unavailable, confirm the error path styles correctly.
