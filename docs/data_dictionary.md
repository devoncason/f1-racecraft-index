# Data Dictionary

## race_driver_features

| Column | Meaning |
|---|---|
| season_year | F1 season year |
| meeting_name | Grand Prix name |
| driver_name | Driver full name |
| team_name | Constructor/team name |
| quali_position | Qualifying result position |
| grid_position | Starting grid position or qualifying fallback |
| finish_position | Final race result position |
| positions_gained_vs_grid | Grid position minus finish position |
| overtakes_made | Count of overtakes made by the driver |
| overtaken_count | Count of times the driver was overtaken |
| net_overtakes | Overtakes made minus times overtaken |
| racecraft_index_mvp | First-version Racecraft Index score |
| racecraft_tier | Label based on score range |
| context_label | Race context label such as dry_no_sc |
| grid_source | Indicates whether grid position came from starting_grid or qualifying fallback |
| total_pit_stops | Number of pit stops recorded for the driver |
| avg_pit_lane_duration | Average pit lane duration for the driver |
| avg_stop_duration | Average stationary stop duration |
| longest_stint_laps | Longest stint length in laps |
| avg_lap_time | Average clean lap duration |
| best_lap_time | Fastest recorded clean lap |
| weather_wet_flag | 1 if rainfall was detected, else 0 |
| safety_car_flag | 1 if safety car context appeared in race control data |
| vsc_flag | 1 if virtual safety car context appeared |
| red_flag | 1 if red flag context appeared |
| race_control_incident_count | Count of race control records for the race session |
| pit_stop_delta_to_race_avg | Driver pit stop count minus race average pit stop count |
| finished_flag | 1 if the driver finished; 0 if DNF/DNS/DSQ |
| extraction_timestamp_utc | Timestamp when the output row was built |
