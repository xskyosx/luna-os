#!/usr/bin/env python3
"""LUNA OS optional, local-only Respect & Uplift check-in.

This records a person's voluntary self-ratings. It does not infer emotions,
score a Sister's feelings, monitor conversations, or claim to measure energy.
Python standard library only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG = Path(__file__).resolve().parent / "data" / "uplift_checkins.jsonl"


def record_checkin(
    before: int,
    after: int,
    *,
    consent: bool = False,
    log_path: Path | str = DEFAULT_LOG,
) -> dict[str, Any] | None:
    """Append one voluntary 1–5 self-report; do nothing without explicit consent."""
    if not consent:
        return None
    for label, value in (("before", before), ("after", after)):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"{label} must be an integer from 1 to 5")
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "before": before,
        "after": after,
        "change": after - before,
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read_summary(log_path: Path | str = DEFAULT_LOG) -> dict[str, int]:
    """Summarize saved check-ins without exposing notes or personal identifiers."""
    path = Path(log_path)
    if not path.exists():
        return {"checkins": 0, "average_change": 0, "uplifted": 0, "unchanged": 0, "lower": 0}
    changes: list[int] = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                item = json.loads(line)
                change = item.get("change")
                if isinstance(change, int) and not isinstance(change, bool) and -4 <= change <= 4:
                    changes.append(change)
    count = len(changes)
    return {
        "checkins": count,
        "average_change": round(sum(changes) / count) if count else 0,
        "uplifted": sum(change > 0 for change in changes),
        "unchanged": sum(change == 0 for change in changes),
        "lower": sum(change < 0 for change in changes),
    }


def main() -> None:
    print("LUNA OS — Respect & Uplift (optional self-check-in)")
    print("This is a private reflection, not a diagnosis or a measure of physical energy.")
    if input("Record a check-in locally? [y/N] ").strip().lower() != "y":
        print("No data recorded.")
        return
    try:
        before = int(input("How uplifted did you feel before? (1–5): "))
        after = int(input("How uplifted do you feel now? (1–5): "))
        entry = record_checkin(before, after, consent=True)
    except (ValueError, OSError) as exc:
        print(f"Could not save check-in: {exc}")
        return
    print(f"Saved locally. Change: {entry['change']:+d} (scale points).")
    print("You can stop using this at any time; delete data/uplift_checkins.jsonl to erase this log.")


if __name__ == "__main__":
    main()
