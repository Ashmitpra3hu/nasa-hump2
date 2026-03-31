# Second-Pass Webpage Scan

## Allowed Source

This scan is based only on the allowed page:

- `https://tmbwg.github.io/turbmodels/nasahump_val.html`

No other external webpage, paper, repository, issue, or PDF was consulted during this scan.

## Usable Physical And Setup Clues

The allowed page provides the following legitimate setup guidance:

- The case is the `2D NASA Wall-Mounted Hump Separated Flow Validation Case`.
- The recommended validation target for this task is the no-flow-control baseline.
- The case can be run with or without the plenum.
- The page explicitly states that, for the no-flow-control case, the plenum is not crucial to include.
- The freestream speed is approximately `34.6 m/s`.
- The Mach number is approximately `0.1`.
- The Reynolds number is stated as `936,000`.
- The hump chord is `420 mm`.
- The incoming fully turbulent boundary-layer thickness at `x/c = -2.14` is approximately `35 mm`, which the page notes is about `8%` of chord.
- The upstream run length is intended to allow the turbulent boundary layer to develop naturally before the hump.
- The upper boundary is modeled as an inviscid slip wall.
- The upper boundary also includes a contour to approximately account for blockage from the experimental end plates.
- The challenge of the case is tied to predicting smooth-body separation, separated shear-layer behavior, reattachment, and boundary-layer recovery.

## Geometry And Configuration Clues

- The hump is a wall-mounted Glauert-Goldschmied type body.
- The experiment is nominally two-dimensional and is treated as such for CFD validation.
- The page shows both with-plenum and no-plenum boundary-condition layout figures.
- The page explicitly distinguishes the no-plenum and with-plenum grid families.
- For this reconstruction, the no-plenum interpretation is the more defensible baseline unless later second-pass evidence from local files strongly argues otherwise.

## Station Locations Explicitly Listed On The Page

The page lists the profile stations of interest as:

- `x/c = -2.14`
- `x/c = 0.65`
- `x/c = 0.8`
- `x/c = 0.9`
- `x/c = 1.0`
- `x/c = 1.1`
- `x/c = 1.2`
- `x/c = 1.3`

These are directly usable for sampling-location design and for organizing plots.

## Visible Graph Categories On The Page

The page visibly presents the following graph families or visualization categories:

- `Cp` versus `x/c`
- `Cf` versus `x/c`
- `u`-velocity profile at `x/c = -2.14`
- `u`-velocity profiles at several downstream stations
- turbulent shear-stress profiles at several stations
- combined velocity / streamline visualization

These graph families define what the second pass should attempt to reproduce with self-generated CFD data.

## Turbulence-Model Behavior Clues

The page states that this case is difficult for known RANS models.

The most important behavior clue is:

- models tend to underpredict turbulent shear stress in the separated shear layer
- because of that, models tend to predict a separation bubble that is too long

This is useful because it gives a physically legitimate explanation for likely mismatch patterns without requiring any forbidden target-data extraction.

## What The Page Allows Us To Use Honestly

- freestream speed
- Reynolds number
- chord length
- upstream boundary-layer thickness target at `x/c = -2.14`
- slip-wall and blockage-contour guidance for the upper boundary
- no-plenum versus with-plenum framing
- station locations
- graph-type inventory
- the general expectation that RANS models struggle with shear stress and bubble length

## What The Page Does Not Allow Us To Use As Numerical Targets

The page also shows or links experimental plots and data files, but under the strict rules for this task the following are not allowed for second-pass tuning:

- digitizing visible curves
- reading numerical target points by hand from images
- tracing screenshot shapes
- interpolating synthetic target curves from the plots
- copying benchmark files from linked data sources

Therefore the page can guide setup and graph categories, but not provide traced target numbers for fitting.

## Key Ambiguities That Remain

- The exact hump contour is not specified numerically on the visible page text.
- The exact upper-boundary contour is not given numerically in the visible page text.
- The exact inflow velocity-profile shape and turbulence-profile shape are not given numerically in the visible page text.
- The exact preferred turbulence model is not mandated; the page only lists model families and “what to expect” result sections.
- The exact convergence depth needed for an acceptable baseline is not specified.

## Consequences For Second-Pass Refinement

Because of those ambiguities, the second pass should:

- improve only what can be justified from the page and local repo materials
- label every assumption explicitly
- avoid pretending to know exact geometry or target curves that were not provided in allowed text
- use evaluation against the local benchmark workflow to judge whether physically motivated refinements actually help
