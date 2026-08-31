# Icons

15 generated SVGs (+ 1 unused `unknown.svg` kept for completeness): one bin-shaped icon per
fraction × 3 states.

- `<fraction>_outline.svg` — scheduled: colored outline, transparent body (fraction's brand
  color, matching the fraction colors used by the smieci.example.com web app).
- `<fraction>_filled.svg` — tomorrow: filled with the fraction's color.
- `<fraction>_blink.svg` — today: filled + an SVG `<animate>` pulsing the opacity.

Served locally by the integration at `/api/smieci_wroclaw/icons/<file>.svg` (registered in
`__init__.py`) and set as each relevant entity's `entity_picture` — this works even if
smieci.example.com itself is unreachable, since HA serves them from its own instance.

Regenerate with the generator this was produced from (not checked in — a short Node script
building a bin body + lid path per fraction color, plus a simple per-fraction material glyph:
recycling triangle for plastics, dots for mixed, a leaf for bio, a folded document for paper, a
bottle for glass). Colors must stay in sync with the main web app's fraction colors and this integration's
`const.py` `FRACTIONS` list if either changes.
