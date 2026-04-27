import pandas as pd


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def add_racecraft_index(features: pd.DataFrame) -> pd.DataFrame:
    """Add a transparent MVP Racecraft Index to driver-weekend rows.

    This is not meant to be a perfect driver-rating model. It is a practical,
    explainable portfolio metric that helps identify drivers worth deeper review.
    Positive values suggest overperformance relative to starting context; negative
    values suggest underperformance.
    """
    df = features.copy()

    for col in [
        "positions_gained_vs_grid",
        "positions_gained_vs_quali",
        "overtakes_made",
        "overtaken_count",
        "total_pit_stops",
        "finished_flag",
    ]:
        if col not in df.columns:
            df[col] = 0
        df[col] = _numeric(df[col]).fillna(0)

    df["net_overtakes"] = df["overtakes_made"] - df["overtaken_count"]

    if "race_session_key" in df.columns and "total_pit_stops" in df.columns:
        race_avg_stops = df.groupby("race_session_key")["total_pit_stops"].transform("mean")
        df["pit_stop_delta_to_race_avg"] = df["total_pit_stops"] - race_avg_stops
    else:
        df["pit_stop_delta_to_race_avg"] = 0

    dnf_penalty = (1 - df["finished_flag"]) * -5

    df["racecraft_index_mvp"] = (
        (2.0 * df["positions_gained_vs_grid"])
        + (0.75 * df["positions_gained_vs_quali"])
        + (0.50 * df["net_overtakes"])
        - (0.75 * df["pit_stop_delta_to_race_avg"])
        + dnf_penalty
    ).round(2)

    def tier(score: float) -> str:
        if score >= 6:
            return "strong_overperformance"
        if score >= 2:
            return "moderate_overperformance"
        if score > -2:
            return "neutral"
        if score > -6:
            return "moderate_underperformance"
        return "strong_underperformance"

    df["racecraft_tier"] = df["racecraft_index_mvp"].apply(tier)
    return df
