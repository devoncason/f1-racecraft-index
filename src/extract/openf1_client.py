import json
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.openf1.org/v1"


def fetch_openf1(
    endpoint: str,
    params: dict[str, Any] | None = None,
    *,
    optional: bool = False,
    timeout: int = 30,
    retries: int = 2,
) -> list[dict[str, Any]]:
    """Fetch records from an OpenF1 endpoint.

    Some OpenF1 endpoints are not populated for every race weekend. Optional
    endpoints return an empty list instead of stopping the whole pipeline.
    """
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    params = params or {}

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if optional and response.status_code in {204, 404}:
                print(f"Warning: no data returned for optional endpoint '{endpoint}' with params {params}")
                return []
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data
            raise ValueError(f"Unexpected JSON payload for {endpoint}: {type(data)}")
        except requests.RequestException as exc:
            last_error = exc
            if optional and getattr(exc.response, "status_code", None) in {204, 404}:
                print(f"Warning: no data returned for optional endpoint '{endpoint}' with params {params}")
                return []
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
            raise

    if last_error:
        raise last_error
    return []


def save_json(records: list[dict[str, Any]], output_path: Path) -> None:
    """Save API records as pretty-printed JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(records):>5} records to {output_path}")


def safe_slug(value: str | int | None) -> str:
    """Return a simple filename-safe label."""
    if value is None:
        return "unknown"
    text = str(value).strip().replace(" ", "_")
    keep = [char for char in text if char.isalnum() or char in {"_", "-"}]
    return "".join(keep) or "unknown"
