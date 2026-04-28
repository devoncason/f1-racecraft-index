from __future__ import annotations

from typing import Any

from src.config import RAW_DATA_DIR, RAW_DIR
from src.extract.openf1_client import fetch_openf1, safe_slug, save_json


def _session_name(session: dict[str, Any]) -> str:
    return str(session.get("session_name") or "").strip()


def _find_session(sessions: list[dict[str, Any]], target: str) -> dict[str, Any]:
    target_lower = target.lower()
    exact_matches = [s for s in sessions if _session_name(s).lower() == target_lower]
    if exact_matches:
        return exact_matches[0]

    contains_matches = [s for s in sessions if target_lower in _session_name(s).lower()]
    if contains_matches:
        return contains_matches[0]

    available = ", ".join(_session_name(s) for s in sessions)
    raise ValueError(f"Could not find a '{target}' session. Available sessions: {available}")


def _filter_meetings(
    meetings: list[dict[str, Any]],
    *,
    country: str | None = None,
    meeting_name: str | None = None,
) -> list[dict[str, Any]]:
    filtered = meetings
    if country:
        needle = country.casefold()
        filtered = [
            m for m in filtered
            if needle in str(m.get("country_name") or "").casefold()
            or needle in str(m.get("meeting_name") or "").casefold()
            or needle in str(m.get("location") or "").casefold()
        ]
    if meeting_name:
        needle = meeting_name.casefold()
        filtered = [m for m in filtered if needle in str(m.get("meeting_name") or "").casefold()]
    return filtered


def select_meeting(year: int, country: str | None = None, meeting_name: str | None = None) -> dict[str, Any]:
    """Select one meeting for a year/country/optional meeting name."""
    meetings = fetch_openf1("meetings", {"year": year})
    save_json(meetings, RAW_DATA_DIR / f"meetings_{year}_ALL.json")

    matches = _filter_meetings(meetings, country=country, meeting_name=meeting_name)
    if not matches:
        raise ValueError(f"No meeting found for year={year}, country={country}, meeting_name={meeting_name}")

    if len(matches) > 1 and not meeting_name:
        options = [f"{m.get('country_name')} - {m.get('meeting_name')} ({m.get('location')})" for m in matches]
        raise ValueError(
            "More than one meeting matched. Add --meeting-name to choose one. Options: " + "; ".join(options)
        )

    return matches[0]


def fetch_weekend(year: int, country: str, *, meeting_name: str | None = None) -> dict[str, Any]:
    """Fetch raw OpenF1 data for a single race weekend."""
    meeting = select_meeting(year, country, meeting_name)
    return fetch_weekend_by_meeting(meeting)


def fetch_weekend_by_meeting(meeting: dict[str, Any]) -> dict[str, Any]:
    meeting_key = int(meeting["meeting_key"])
    year = int(meeting["year"])
    country = str(meeting.get("country_name") or meeting.get("location") or "unknown")
    meeting_label = safe_slug(meeting.get("meeting_name") or country)

    print(f"Pulling OpenF1 data for {year} {meeting.get('meeting_name')} ({country})...")
    save_json([meeting], RAW_DATA_DIR / f"selected_meeting_{meeting_key}.json")

    sessions = fetch_openf1("sessions", {"meeting_key": meeting_key})
    save_json(sessions, RAW_DATA_DIR / f"sessions_{meeting_key}.json")

    qualifying_session = _find_session(sessions, "Qualifying")
    race_session = _find_session(sessions, "Race")
    qualifying_session_key = int(qualifying_session["session_key"])
    race_session_key = int(race_session["session_key"])

    save_json([qualifying_session], RAW_DATA_DIR / f"selected_qualifying_session_{qualifying_session_key}.json")
    save_json([race_session], RAW_DATA_DIR / f"selected_race_session_{race_session_key}.json")

    # OpenF1 does not use separate qualifying_result and race_result endpoints.
    # We call the available session_result endpoint, but save the files using
    # the filenames expected by the rest of this project.
    endpoint_plan = [
        # output_name, api_endpoint, session_key, optional
        ("drivers", "drivers", race_session_key, False),
        ("qualifying_result", "session_result", qualifying_session_key, False),
        ("starting_grid", "starting_grid", race_session_key, True),
        ("race_result", "session_result", race_session_key, False),
        ("laps", "laps", race_session_key, False),
        ("stints", "stints", race_session_key, True),
        ("pit", "pit", race_session_key, True),
        ("position", "position", race_session_key, True),
        ("intervals", "intervals", race_session_key, True),
        ("weather", "weather", race_session_key, True),
        ("race_control", "race_control", race_session_key, True),
        ("overtakes", "overtakes", race_session_key, True),
    ]

    for output_name, api_endpoint, session_key, optional in endpoint_plan:
        label = f"{output_name}_{session_key}"
        print(f"Fetching {label} from OpenF1 endpoint '{api_endpoint}'...")
        records = fetch_openf1(api_endpoint, {"session_key": session_key}, optional=optional)
        save_json(records, RAW_DATA_DIR / f"{label}.json")

    print(f"Finished pulling {year} {meeting_label}.")
    return {
        "meeting_key": meeting_key,
        "race_session_key": race_session_key,
        "qualifying_session_key": qualifying_session_key,
    }


def fetch_season(year: int, *, max_weekends: int | None = None) -> list[dict[str, Any]]:
    """Fetch every race meeting available from OpenF1 for a season."""
    meetings = fetch_openf1("meetings", {"year": year})
    save_json(meetings, RAW_DIR / f"meetings_{year}_ALL.json")

    if max_weekends:
        meetings = meetings[:max_weekends]

    results = []
    for meeting in meetings:
        try:
            results.append(fetch_weekend_by_meeting(meeting))
        except Exception as exc:
            print(f"Warning: skipped meeting {meeting.get('meeting_name')} because of error: {exc}")
    return results
