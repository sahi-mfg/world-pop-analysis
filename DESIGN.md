---
version: alpha
name: WorldPop Explorer
description: Quiet light analytics screen for exploring population growth inside any area on a map. One warm data hue, ink chrome, figures set as type.
colors:
  primary: "#C2410C"
  on-primary: "#FFFFFF"
  primary-tint: "#FBEEE8"
  ink: "#141413"
  muted: "#5C5D58"
  faint: "#6B6C66"
  neutral: "#F6F6F4"
  surface: "#FFFFFF"
  raised: "#F2F2EF"
  active: "#EBEBE7"
  border: "#E6E6E1"
  rule: "#F0F0EC"
  control: "#CFD0CA"
  data-neutral: "#B9BAB3"
  grid: "#E8E8E3"
  error: "#B42318"
  error-tint: "#FEF1EF"
typography:
  title:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: -0.01em
  section:
    fontFamily: IBM Plex Sans
    fontSize: 15px
    fontWeight: 600
    lineHeight: 1.4
  figure-lead:
    fontFamily: IBM Plex Sans
    fontSize: 32px
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: -0.015em
    fontFeature: '"tnum" 1'
  figure:
    fontFamily: IBM Plex Sans
    fontSize: 22px
    fontWeight: 500
    lineHeight: 1.2
    fontFeature: '"tnum" 1'
  body:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: IBM Plex Sans
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4
  small:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
rounded:
  chip: 4px
  control: 6px
  card: 8px
spacing:
  unit: 4px
  gap: 16px
  card-pad: 20px
  canvas-pad: 24px
  sidebar: 248px
  control-height: 32px
  row-height: 40px
components:
  nav-item:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: 40px
  nav-item-active:
    backgroundColor: "{colors.active}"
    textColor: "{colors.ink}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: 20px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    height: 32px
    padding: 12px
  button-secondary-hover:
    backgroundColor: "{colors.raised}"
  segmented:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    height: 32px
  segmented-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  table-header:
    textColor: "{colors.faint}"
    typography: "{typography.small}"
    height: 36px
  map-callout:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.chip}"
    padding: 8px
  chart-bar:
    backgroundColor: "{colors.data-neutral}"
    rounded: 2px
  chart-bar-peak:
    backgroundColor: "{colors.primary}"
    rounded: 2px
  chart-gridline:
    backgroundColor: "{colors.grid}"
    height: 1px
  panel-edge:
    backgroundColor: "{colors.border}"
    height: 1px
  table-row-rule:
    backgroundColor: "{colors.rule}"
    height: 1px
  control-outline:
    backgroundColor: "{colors.control}"
    height: 1px
  error-notice:
    backgroundColor: "{colors.error-tint}"
    textColor: "{colors.error}"
    rounded: "{rounded.card}"
---

# WorldPop Explorer

## Overview

An analytics tool, not a landing page. Someone opens it to answer one question:
**how fast has the population grown inside this area since 2000?** Everything on the
screen serves that answer, in this reading order: the area's name, one sentence stating
the finding, the map that shows where, the figures, the two charts that show how, and the
table that proves it.

The character is a printed atlas: paper-white ground, black ink, and a single vermilion
used the way a cartographer uses red: only on the thing being measured. The map is the
product's signature: the measured rectangle carries its own population callout, so the
answer sits on the place itself.

Quiet is the starting point, not the goal. The screen earns its richness from real data at
real size, never from ornament.

## Colors

One ground, one ink, one hue.

- **Atlas paper (#F6F6F4):** the page ground and sidebar. A neutral, very slightly warm
  white, so white panels read as sheets laid on it.
- **Surface (#FFFFFF):** panels, the map frame, the table.
- **Ink (#141413):** all running text, figures and the area name.
- **Muted (#5C5D58) and faint (#6B6C66):** labels, axis ticks, sublines, captions. Both
  pass 4.5:1 on paper and on white.
- **Census vermilion (#C2410C):** the data hue. It marks the population line, the selected
  rectangle on the map and the fastest-growth bar. It never fills chrome, buttons or nav.
- **Vermilion tint (#FBEEE8):** the flat area under the population line and the inside of
  the selected rectangle.
- **Data neutral (#B9BAB3):** every bar that is not the finding.
- **Border (#E6E6E1), rule (#F0F0EC), control (#CFD0CA):** lines in three steps: panel
  edges, table rows, control outlines.
- **Error (#B42318) on error tint (#FEF1EF):** only inside a block whose data failed.

## Typography

One grotesk, **IBM Plex Sans**, an engineered face with the plain voice of a technical
atlas, self-hosted. Its figures are tabular by default while its punctuation stays
proportional, so columns align digit for digit without looking like a monospace.

- **Title (24/650):** the area's name, the screen's only h1.
- **Section (15/600):** panel titles.
- **Figure lead (32/500):** the latest population, the screen's answer. Nothing else on
  the screen is larger.
- **Figure (22/500):** sibling figures in the summary panel.
- **Body (14/400):** text, table cells, nav.
- **Label (13/500):** labels above figures, buttons.
- **Small (12/400):** axis ticks, table headers, captions, the source line.

Sentence case everywhere. No uppercase tracked labels, no italics, no second face.

## Layout

An **open plane**: a labelled 248px sidebar on the page ground, separated from the canvas
by a single 1px rule, and a fluid canvas with 24px padding.

- The title row holds the h1 and the finding sentence on the left, the period and sampling
  controls and the export action on the right.
- Row 1: the map (two thirds) beside the summary panel (one third). Both 380px tall so
  their bottoms align.
- Row 2: the population chart (two thirds) beside the growth chart (one third), equal
  heights.
- Row 3: the table, full width.
- One gap everywhere: 16px between panels, horizontally and vertically.
- At 1440×900, the title, map, figures and both charts are visible without scrolling.

On a phone (<1024px) the sidebar folds into a top bar with the product mark; the area
picker becomes a select beside the draw button, and every row stacks.

## Elevation & Depth

Flat. Panels are white on paper with a 1px border and no shadow. Only things that float
get a shadow: the select's menu, chart tooltips and the map callout (`0 4px 16px` at 10%
black). No blur, no glass, no glow.

## Shapes

Tight radii, chosen once: 8px panels, 6px controls, 4px chips and the map callout.
Chart bars are square at the baseline with a 2px top radius. The map rectangle is sharp.

## Components

- **Sidebar list:** areas as 40px rows (name in ink, country in muted on the right). The
  selected row takes the neutral active fill. "Draw an area" is the last row, with a
  16px outline icon.
- **Summary panel:** one panel divided by 1px rules. Label above value. The latest
  population leads at 32px; change, annual growth, doubling time and density follow at
  22px with their unit as a smaller muted suffix.
- **Charts:** straight 2px line, no point markers; 4 horizontal gridlines, no axis lines;
  round ticks with the top tick above the maximum; no legend for a single series. Bars
  are neutral except the peak, in vermilion, labelled in the panel subtitle.
- **Table:** 12px muted sentence-case headers, no band, 1px row rules, numbers
  right-aligned, a muted dash for missing values.
- **Loading:** the final layout with flat grey bars at each value's size. No shimmer.
- **Error:** inside the block that failed: one sentence naming what failed and the
  server's message, and a "Try again" text button.

## Do's and Don'ts

- Do put vermilion only on measured data and the selected area.
- Do keep every number in tabular figures, right-aligned in columns.
- Do name the baseline of every relative figure ("since 2000", "a year").
- Do print missing values as a muted dash, never as a zero.
- Don't add eyebrows, uppercase tracked labels, italics or a second typeface.
- Don't use gradients, shadows on resting panels, glass or blur.
- Don't put icons in tinted circles, sparklines on figures, or a legend on a single series.
- Don't set any figure larger than the latest population, or any title above 24px.
