# No-Interpolation Declaration

This second-pass reconstruction follows a strict no-cheating rule.

## Explicit Declarations

- No image digitization was used.
- No manual tracing of webpage curves was used.
- No manual reading of target points from webpage screenshots was used.
- No interpolation, spline fitting, or synthetic target-curve generation was used to fake agreement with the allowed webpage plots.
- No benchmark data were typed in by hand from images.
- No graph was adjusted to visually mimic the webpage.

## What The Second-Pass Graphs Are Allowed To Use

Every second-pass graph must come directly from one or more of the following:

- OpenFOAM field outputs generated locally in this repository
- OpenFOAM function-object sampling or post-processing results generated locally
- direct post-processing scripts written during this task
- machine-readable local evaluation files already present in the repository

## What The Allowed Webpage Is Used For

The allowed NASA hump validation webpage is used only for:

- case framing
- physical/setup clues
- station-location identification
- graph-category identification
- turbulence-model expectation clues
- documentation of what types of validation plots should be recreated

It is not used as a source of traced numerical target curves.
