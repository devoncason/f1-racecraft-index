CREATE TABLE IF NOT EXISTS race_driver_features (
    season_year INTEGER,
    meeting_key INTEGER,
    meeting_name TEXT,
    country_name TEXT,
    location TEXT,
    race_session_key INTEGER,
    qualifying_session_key INTEGER,
    session_date_start TEXT,
    driver_number INTEGER,
    driver_name TEXT,
    team_name TEXT,
    quali_position INTEGER,
    grid_position INTEGER,
    grid_source TEXT,
    finish_position INTEGER,
    positions_gained_vs_quali INTEGER,
    positions_gained_vs_grid INTEGER,
    total_pit_stops INTEGER,
    avg_pit_lane_duration REAL,
    avg_stop_duration REAL,
    longest_stint_laps REAL,
    total_stints INTEGER,
    avg_lap_time REAL,
    best_lap_time REAL,
    clean_lap_count INTEGER,
    weather_wet_flag INTEGER,
    avg_air_temperature REAL,
    avg_track_temperature REAL,
    safety_car_flag INTEGER,
    vsc_flag INTEGER,
    red_flag INTEGER,
    race_control_incident_count INTEGER,
    overtakes_made INTEGER,
    overtaken_count INTEGER,
    net_overtakes INTEGER,
    pit_stop_delta_to_race_avg REAL,
    points REAL,
    finished_flag INTEGER,
    context_label TEXT,
    racecraft_index_mvp REAL,
    racecraft_tier TEXT,
    extraction_timestamp_utc TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_race_driver_features_unique
ON race_driver_features (race_session_key, driver_number);

CREATE INDEX IF NOT EXISTS idx_race_driver_features_driver
ON race_driver_features (driver_name);

CREATE INDEX IF NOT EXISTS idx_race_driver_features_context
ON race_driver_features (season_year, context_label);

CREATE TABLE IF NOT EXISTS driver_context_summary (
    season_year INTEGER,
    driver_name TEXT,
    team_name TEXT,
    race_count INTEGER,
    avg_grid_position REAL,
    avg_finish_position REAL,
    total_positions_gained_vs_grid REAL,
    avg_positions_gained_vs_grid REAL,
    avg_racecraft_index REAL,
    best_racecraft_index REAL,
    worst_racecraft_index REAL,
    total_overtakes_made REAL,
    total_overtaken_count REAL,
    avg_pit_stops REAL,
    finish_rate REAL,
    wet_race_count REAL,
    safety_car_race_count REAL
);
