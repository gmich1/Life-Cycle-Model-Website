# Split-Screen Two-Instance Comparison — Design

**Date:** 2026-07-18
**Status:** Approved (design), pending implementation plan
**Scope:** Frontend only — no backend / model changes.

## Problem

The page runs one simulation at a time. To compare two scenarios a user has to
run one, remember or screenshot the numbers, then re-enter everything for the
second. We want a **toggle at the top** that switches between **one** and **two**
independent simulation instances shown side by side in the same tab, so two
scenarios can be configured and run at once and read against each other.

## Decisions (from brainstorming)

1. **Two independent instances.** Each has its own form, its own Submit, its own
   `/api/run` call, its own progress bar and results. Neither blocks the other;
   they can run at the same time.
2. **The second (red) instance remembers itself.** It is created the first time
   the user switches to two-instance mode, starting at fresh defaults. After that
   it stays mounted; toggling back to one hides it (it is not destroyed), so its
   inputs and results survive a round-trip through single mode.
3. **One page scroll.** The two instances sit in normal page flow; the whole page
   scrolls as one, so they inherently scroll together. No JS scroll-sync.
4. **Red = form UI chrome only.** The second instance recolors its interface
   (header, section titles, buttons, active preset pills, input focus rings,
   results-table header, progress bar) from Imperial blue to red. The generated
   life-cycle **charts are left as the backend draws them** (matplotlib defaults,
   identical in both instances). No backend change.
5. **Three-band layout.** Forms sit side by side, charts side by side beneath
   them, and the **results tables are stacked full width — even on wide screens**
   (two ~13-column tables cannot sit side by side). The stacked tables are told
   apart by their color-coded header rows (blue vs red).
6. **Collapse to one column on narrow screens.** All three bands collapse to a
   single column while keeping the band grouping — blue form, red form, blue
   charts, red charts, blue table, red table — reusing the existing fit-to-screen
   grid behavior.
7. **Per-instance detail pages.** Each instance's charts are stored and linked
   separately, so one run never overwrites the other's detail page (see below).

## Architecture

### Component extraction

The current `Inputs` component is one self-contained simulation (preset bar,
form, submit-to-`/api/run`, progress, results, currency/salary display). It is
extracted verbatim into a reusable component and the old file becomes a thin
container.

- **`src/pages/SimulationPanel.js`** — the current `Inputs` body and *all* its
  state (`result`, `charts`, `startAge`, `currency`, `salary`, `error`,
  `loading`, `progress`, `activePreset`). One new prop:
  - `variant`: `'blue'` (default) | `'red'`. Selects the theme class and the
    detail-page/localStorage variant.
  Single responsibility: run one simulation. It stays self-contained — form,
  charts, and results table (with its currency conversion) are all rendered by
  this one component, so the currency/salary selectors keep driving the table
  exactly as they do today. To let the container place those pieces into
  different layout bands (see Layout), the panel's render is organised into three
  area-tagged sections — `.panel-form`, `.panel-charts`, `.panel-table` — and the
  panel wrapper uses `display: contents` so those sections become items of the
  container's grid. (Custom-property inheritance still cascades through a
  `display: contents` element, so the red variable override keeps working.)
- **`src/pages/Inputs.js`** — becomes the container. It renders:
  - the **instance toggle** at the very top (above both panels), and
  - a single CSS grid that lays the panels' sections out in three bands (see
    Layout).
  `App.js` still mounts `<Inputs>`, so nothing upstream changes.

### Instance toggle

A small segmented control centered at the top, styled in the app's blue chrome,
with two options — **`1 form`** and **`2 forms`** — defaulting to `1 form`. It
sets a container state value `instances` (`1` | `2`).

### "Remembers itself" mechanism

- On initial load, `instances === 1` and **only the blue panel is rendered** —
  the DOM contains exactly one form (keeps existing tests valid).
- The first time the user selects `2 forms`, the red panel mounts.
- Once mounted, the red panel is **never unmounted**; switching back to `1 form`
  hides it by setting its wrapper to `display: none` (which overrides the panel's
  `display: contents`, removing all three of its sections from the grid at once).
  Because it stays mounted, its uncontrolled inputs and React state persist.
- Implementation: track a `redEverShown` flag; render the red panel when
  `instances === 2 || redEverShown`, and hide it (`display: none`) when
  `instances === 1`.

## Red theming (CSS-variable override)

The stylesheet already reads `var(--imperial-blue)`, `var(--imperial-blue-dark)`,
and `var(--imperial-light-blue)` everywhere. The red panel re-declares those
three variables on its wrapper, and the cascade recolors every descendant with
**no per-rule rewriting**:

```css
.sim-panel--red {
  --imperial-blue: #C0272D;
  --imperial-blue-dark: #8B1E22;
  --imperial-light-blue: #E8686D;
}
```

Each panel is wrapped in `.sim-panel` (blue, using the `:root` defaults) or
`.sim-panel sim-panel--red`. The one hardcoded blue not driven by a variable —
the focus-ring `rgba(0, 145, 212, 0.25)` on `.field input:focus` — is promoted to
a variable (`--focus-ring`) so the red panel's focus rings are red too; the blue
default keeps the current value. Charts are backend PNGs and are unaffected.

## Layout, scroll, and mobile

Two-instance mode lays the two panels' sections out in **three bands** — forms
side by side, charts side by side beneath them, and the results tables stacked
full width. The tables stack **even on wide screens** (a single results table is
already ~13 columns and breaks out to `96vw`; two side by side cannot fit). The
tables are told apart by their **color-coded header rows** — blue panel's header
is blue, red panel's is red (a free consequence of the variant override) — so no
dividing line is needed.

Wide-screen shape:

```
  [ BLUE form   ]   [ RED form   ]     ← forms band (2 columns)
  [ BLUE charts ]   [ RED charts ]     ← charts band (2 columns)
  [ BLUE table — full width, blue header ]   ← tables band (stacked,
  [ RED  table — full width, red  header ]      full width)
```

- The container is one CSS grid using `grid-template-areas`. With the panels'
  `display: contents` wrappers, each panel contributes `.panel-form`,
  `.panel-charts`, `.panel-table` as grid items, assigned to named areas by
  variant:
  ```css
  .compare-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "blue-form   red-form"
      "blue-charts red-charts"
      "blue-table  blue-table"
      "red-table   red-table";
  }
  ```
  Section classes map to areas (`.panel-form.blue → blue-form`, `.panel-table.red
  → red-table`, …). The two table areas span both columns, so tables are full
  width and stacked.
- **One-instance mode:** the grid is a single column and only the blue panel's
  three sections show (`blue-form` / `blue-charts` / `blue-table`), i.e. exactly
  today's layout — including the table's existing `96vw` break-out, which is kept
  for single mode.
- **Narrow screens (both modes):** a media query switches to a single-column
  `grid-template-areas` that keeps the band grouping — blue form, red form, blue
  charts, red charts, blue table, red table:
  ```css
  grid-template-areas:
    "blue-form" "red-form"
    "blue-charts" "red-charts"
    "blue-table" "red-table";
  ```
  reusing the `min(…, 100%)` fit-to-screen fix.
- **Width:** two-instance mode widens the container beyond the single-mode
  `960px` cap (to ~`96vw`) so two form columns fit; single mode keeps the `960px`
  centered column unchanged.
- Everything is in normal page flow → one page scrollbar, both instances scroll
  together. No scroll-sync code.

## Per-instance detail pages

Each detail page (`public/algorithm.html` = Technical,
`public/algorithm_simple.html` = Simple) ends with a script that reads
`lifecycleCharts` from `localStorage` and swaps the data URIs into the page's
`<img>` elements. Today both instances would write the same key (last-write-wins).
Fix, without duplicating the ~9,000-line HTML files:

1. **Variant-scoped storage keys.** On a successful run a panel writes its charts
   to `lifecycleCharts:<variant>` — `lifecycleCharts:blue` or
   `lifecycleCharts:red`. The blue panel also writes the legacy `lifecycleCharts`
   key so any pre-existing no-param links keep working. Separate keys mean neither
   instance overwrites the other's charts.
2. **Variant on the detail links.** Each panel's *Simple* / *Technical* buttons
   carry a query param: blue → `/algorithm.html?variant=blue` and
   `/algorithm_simple.html?variant=blue`; red → the same with `variant=red`.
3. **Detail pages read the param.** The detail script becomes:
   ```js
   var variant = new URLSearchParams(location.search).get("variant");
   var key = variant ? "lifecycleCharts:" + variant : "lifecycleCharts";
   var charts = JSON.parse(localStorage.getItem(key) || "null");
   ```
   (rest unchanged). Same two physical files, parameterized by `?variant`, so
   each instance has its own detail-page URL showing its own charts.

## Files touched

- Create: `src/pages/SimulationPanel.js` (extracted from current `Inputs.js`).
- Modify: `src/pages/Inputs.js` → container (toggle + panel layout).
- Modify: `src/pages/Inputs.css` → add `.sim-panel--red` variable override,
  `--focus-ring` variable, the toggle styles, and the compare-grid layout.
- Modify: `public/algorithm.html`, `public/algorithm_simple.html` → 3-line
  variant-aware key selection.
- Modify: `src/pages/Inputs.test.js` → point the existing preset tests at
  `SimulationPanel`; add a toggle test.

## Testing

- **Existing preset tests** move to render `SimulationPanel` directly (same
  assertions — the form and presets are unchanged).
- **New: toggle behavior.** Rendering the container shows one form by default;
  selecting `2 forms` renders a second form; the second form is red
  (`.sim-panel--red` present); selecting `1 form` hides but does not unmount the
  second (its state persists — verify an edited value in the red form survives a
  `2 → 1 → 2` toggle).
- **New: variant wiring.** The red panel's detail links carry `?variant=red`; the
  blue panel's carry `?variant=blue`.
- Sanity (manual): run both panels, confirm two independent progress bars and two
  result sets; open each panel's detail pages and confirm they show that panel's
  charts, not the other's.

## Out of scope

- Recoloring the generated charts (would need backend/matplotlib changes).
- JS-synced independent scroll panes (we use one page scroll).
- More than two instances.
- Any merged/overlaid comparison view of the two result sets — they are read side
  by side, not combined.
- Backend, model, or `/api/run` changes of any kind.
