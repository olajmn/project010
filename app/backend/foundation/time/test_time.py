"""Small, direct checks for now(), week_windows(), and day_windows()."""

# Contents
#  1. now() checks
#  2. week_windows() / day_windows() checks

from datetime import datetime, timedelta

import pytest

from backend.foundation.time import day_windows, freeze_duration, now, week_windows
from backend.foundation.time.time_logic.frozen_duration import DAYS_PER_WEEK

# 1. now() checks


def test_now_is_naive_system_time() -> None:
    result = now()
    assert isinstance(result, datetime), f"now() returned {type(result)}, expected datetime"
    assert result.tzinfo is None, f"now() returned a timezone-aware datetime: {result!r}"
    real_now = datetime.now()
    assert abs(real_now - result) < timedelta(seconds=5), f"now() = {result}, system clock = {real_now}"


# 2. week_windows() / day_windows() checks


def _month_windows():
    month = freeze_duration("1 month")
    return month, week_windows(month)


def test_month_is_week_grain() -> None:
    month, windows = _month_windows()
    assert windows is not None, "1 month must be week grain"
    # N is round(calendar days / 7), and the span's calendar days depend on
    # today's date (a 31-day month counts 32 days, which rounds to 5).
    assert len(windows) in (4, 5), f"1 month should yield 4 or 5 weeks, got {len(windows)}"
    assert all("start_label" in w and "end_label" in w for w in windows)
    # Calendar weeks start on the span's start date (midnight), not the
    # raw freeze instant's clock time.
    assert datetime.fromisoformat(windows[0]["start"]).date() == datetime.fromisoformat(month["start"]).date()
    assert datetime.fromisoformat(windows[-1]["end"]) == datetime.fromisoformat(month["end"])


@pytest.mark.parametrize("weeks", (4, 6))
def test_n_weeks_give_n_windows(weeks) -> None:
    assert len(week_windows(freeze_duration(f"{weeks} weeks"))) == weeks


@pytest.mark.parametrize("span", ("2 hours", "1 year"))
def test_session_and_year_are_not_week_grain(span) -> None:
    assert week_windows(freeze_duration(span)) is None


def test_days_are_consecutive() -> None:
    # Consecutive calendar dates - no skipped weekdays.
    _, windows = _month_windows()
    for w in windows[:-1]:
        days = day_windows(w)
        assert len(days) == DAYS_PER_WEEK, f"full week should have {DAYS_PER_WEEK} days, got {len(days)}"
        for i in range(len(days) - 1):
            d0 = datetime.fromisoformat(days[i]["start"]).date()
            d1 = datetime.fromisoformat(days[i + 1]["start"]).date()
            assert d1 - d0 == timedelta(days=1), f"gap in days: {days[i]['start_label']} -> {days[i+1]['start_label']}"

    last_days = day_windows(windows[-1])
    assert len(last_days) >= DAYS_PER_WEEK
    for i in range(len(last_days) - 1):
        d0 = datetime.fromisoformat(last_days[i]["start"]).date()
        d1 = datetime.fromisoformat(last_days[i + 1]["start"]).date()
        assert d1 - d0 == timedelta(days=1)
