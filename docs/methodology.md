# Methodology

## Research Question

Why did a driver or team overperform or underperform on a given Formula 1 weekend, and was the result driven more by pace, strategy, race events, or execution?

## MVP Racecraft Index

The first version of the Racecraft Index is an explainable score that uses:

- Positions gained/lost versus starting grid
- Positions gained/lost versus qualifying
- Net overtakes
- Pit-stop count compared with race average
- Finish/DNF status

Positive scores suggest overperformance. Negative scores suggest underperformance.

## Current Formula

racecraft_index_mvp =
(2.0 × positions_gained_vs_grid)
+ (0.75 × positions_gained_vs_quali)
+ (0.50 × net_overtakes)
- (0.75 × pit_stop_delta_to_race_avg)
+ DNF penalty

## Interpretation

This score is not meant to replace expert race analysis. It is a first-pass ranking system that identifies drivers and weekends that deserve closer investigation.
