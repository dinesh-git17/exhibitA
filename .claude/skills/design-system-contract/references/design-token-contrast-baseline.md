# Design Token Contrast Baseline

Use this reference when enforcing DSC021 and DSC022.

## Token Principles

- Keep visual decisions in semantic tokens, never in view code.
- Define color tokens as paired light/dark values.
- Keep typography as semantic roles, not per-view size declarations.
- Keep spacing on a 4pt base rhythm.

## Required Exhibit A Tokens

- `goldLeaf`
- `dustyRose`
- `sealBurgundy`
- `warmInk`
- `fadedInk`
- `shadowWarm`
- One background token whose dark value is `#1E1B16`

## WCAG AA Thresholds

- Body text: `4.5:1` minimum contrast ratio.
- Large text: `3.0:1` minimum contrast ratio.

Use relative luminance contrast:

`(L1 + 0.05) / (L2 + 0.05)`

Where `L1` is lighter luminance and `L2` is darker luminance.

## Implementation Expectations

- Parse semantic text tokens against semantic background tokens for both light and dark modes.
- Reject unparseable color values for contrast checks.
- Reject any ratio below the required threshold for the token role.
