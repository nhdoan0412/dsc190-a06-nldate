"""Specification for common absolute and relative date expressions."""

from datetime import date

import pytest

from nldate import parse

BASE = date(2026, 11, 9)  # Monday


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("today", date(2026, 11, 9)),
        ("TOMORROW", date(2026, 11, 10)),
        ("yesterday", date(2026, 11, 8)),
        ("the day after tomorrow", date(2026, 11, 11)),
        ("the day before yesterday", date(2026, 11, 7)),
        ("next Tuesday", date(2026, 11, 10)),
        ("last Friday", date(2026, 11, 6)),
        ("this Monday", date(2026, 11, 9)),
        ("in 3 days", date(2026, 11, 12)),
        ("4 weeks ago", date(2026, 10, 12)),
        ("two weeks from tomorrow", date(2026, 11, 24)),
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("1 year and 2 months after yesterday", date(2028, 1, 8)),
        ("3 days after next Friday", date(2026, 11, 16)),
        ("next month", date(2026, 12, 9)),
        ("last year", date(2025, 11, 9)),
        ("start of next month", date(2026, 12, 1)),
        ("end of this month", date(2026, 11, 30)),
        ("2025-12-01", date(2025, 12, 1)),
        ("12/01/2025", date(2025, 12, 1)),
        ("December 1st, 2025", date(2025, 12, 1)),
        ("1 December 2025", date(2025, 12, 1)),
        ("Dec 1, 2025", date(2025, 12, 1)),
        ("November 20", date(2026, 11, 20)),
    ],
)
def test_parses_dates(expression: str, expected: date) -> None:
    assert parse(expression, today=BASE) == expected


@pytest.mark.parametrize(
    "expression", ["", "   ", "not a date", "February 30, 2025", "in lots of days"]
)
def test_invalid_dates_raise_value_error(expression: str) -> None:
    with pytest.raises(ValueError):
        parse(expression, today=BASE)


def test_today_defaults_to_real_current_date() -> None:
    assert parse("today") == date.today()


def test_months_are_clamped_at_month_end() -> None:
    assert parse("1 month after January 31, 2026", BASE) == date(2026, 2, 28)


def test_leap_year() -> None:
    assert parse("February 29, 2024", BASE) == date(2024, 2, 29)


def test_abbreviated_month_with_period() -> None:
    assert parse("Dec. 1, 2025") == date(2025, 12, 1)
