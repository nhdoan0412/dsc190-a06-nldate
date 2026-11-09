"""Parse common English date expressions into datetime.date objects."""

import calendar
import re
from datetime import date, datetime, timedelta

_WEEKDAYS = {
    name: i
    for i, names in enumerate(
        [
            ("monday", "mon"),
            ("tuesday", "tue", "tues"),
            ("wednesday", "wed", "weds"),
            ("thursday", "thu", "thur", "thurs"),
            ("friday", "fri"),
            ("saturday", "sat"),
            ("sunday", "sun"),
        ]
    )
    for name in names
}
_NUMBERS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}
_UNIT = r"(?:years?|months?|weeks?|days?)"
_NUMBER = r"(?:\d+|[a-z]+(?:[- ][a-z]+)?)"
_DURATION_ITEM = re.compile(rf"(?P<number>{_NUMBER})\s+(?P<unit>{_UNIT})\b")


def _number(text: str) -> int | None:
    if text.isdecimal():
        return int(text)
    if text in _NUMBERS:
        return _NUMBERS[text]
    words = text.replace("-", " ").split()
    if len(words) == 2 and words[0] in _NUMBERS and words[1] in _NUMBERS:
        return _NUMBERS[words[0]] + _NUMBERS[words[1]]
    return None


def _duration(text: str) -> tuple[int, int, int] | None:
    """Return (months, weeks, days), or None for malformed durations."""
    text = text.strip()
    months = weeks = days = 0
    end = 0
    found = False
    for match in _DURATION_ITEM.finditer(text):
        between = text[end : match.start()]
        if between and re.fullmatch(r"(?:\s|,|\band\b)+", between) is None:
            return None
        value = _number(match.group("number"))
        if value is None:
            return None
        unit = match.group("unit")
        if unit.startswith("year"):
            months += 12 * value
        elif unit.startswith("month"):
            months += value
        elif unit.startswith("week"):
            weeks += value
        else:
            days += value
        end = match.end()
        found = True
    if not found or text[end:].strip():
        return None
    return months, weeks, days


def _shift(base: date, months: int = 0, weeks: int = 0, days: int = 0) -> date:
    """Shift calendar months with end-of-month clamping, then add days."""
    try:
        absolute_month = base.year * 12 + base.month - 1 + months
        year, month_zero = divmod(absolute_month, 12)
        month = month_zero + 1
        day = min(base.day, calendar.monthrange(year, month)[1])
        return date(year, month, day) + timedelta(weeks=weeks, days=days)
    except (OverflowError, ValueError) as error:
        raise ValueError("date out of range") from error


def _absolute(text: str, reference: date) -> date | None:
    """Recognize ISO, US numeric, and English month-name dates."""
    cleaned = re.sub(r"(?<=\d)(?:st|nd|rd|th)\b", "", text)
    cleaned = re.sub(r"\bsept\b", "sep", cleaned)
    cleaned = re.sub(r"[,]+", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    full_formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %Y",
        "%b %Y",
    )
    for fmt in full_formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.date()
        except ValueError:
            continue
    for fmt in ("%B %d", "%b %d", "%d %B", "%d %b"):
        try:
            parsed = datetime.strptime(f"{cleaned} {reference.year}", f"{fmt} %Y")
            return parsed.date()
        except ValueError:
            continue
    return None


def parse(s: str, today: date | None = None) -> date:
    """Interpret a common English date expression relative to ``today``."""
    reference = today if today is not None else date.today()
    text = " ".join(s.strip().lower().split())
    if not text:
        raise ValueError("empty date expression")

    fixed = {
        "today": 0,
        "now": 0,
        "tomorrow": 1,
        "yesterday": -1,
        "day after tomorrow": 2,
        "the day after tomorrow": 2,
        "day before yesterday": -2,
        "the day before yesterday": -2,
    }
    if text in fixed:
        return _shift(reference, days=fixed[text])

    weekday = re.fullmatch(r"(?:(next|last|previous|this|coming|on)\s+)?([a-z]+)", text)
    if weekday and weekday.group(2) in _WEEKDAYS:
        target = _WEEKDAYS[weekday.group(2)]
        modifier = weekday.group(1)
        if modifier in ("last", "previous"):
            delta = -((reference.weekday() - target) % 7 or 7)
        else:
            delta = (target - reference.weekday()) % 7
            if modifier == "next" and delta == 0:
                delta = 7
        return _shift(reference, days=delta)

    simple = re.fullmatch(r"(next|last|previous|this)\s+(day|week|month|year)", text)
    if simple:
        direction = (
            -1
            if simple.group(1) in ("last", "previous")
            else 0
            if simple.group(1) == "this"
            else 1
        )
        unit = simple.group(2)
        if unit == "day":
            return _shift(reference, days=direction)
        if unit == "week":
            return _shift(reference, weeks=direction)
        if unit == "month":
            return _shift(reference, months=direction)
        return _shift(reference, months=direction * 12)

    month_boundary = re.fullmatch(
        r"(?:(?:the )?(?:first day|start|beginning|last day|end) of )"
        r"(?:(this|next|last) )?(month|year)",
        text,
    )
    if month_boundary:
        direction = {"this": 0, "next": 1, "last": -1, None: 0}[month_boundary.group(1)]
        unit = month_boundary.group(2)
        is_end = any(word in text for word in ("end", "last day"))
        if unit == "month":
            first = _shift(reference.replace(day=1), months=direction)
            return _shift(first, months=1, days=-1) if is_end else first
        first = date(reference.year + direction, 1, 1)
        return date(first.year, 12, 31) if is_end else first

    # Explicit relative offsets are checked before absolute dates.
    match = re.fullmatch(r"in\s+(.+)", text)
    if match:
        amount = _duration(match.group(1))
        if amount is not None:
            return _shift(reference, *amount)

    match = re.fullmatch(r"(.+?)\s+(ago|from now|later|hence)", text)
    if match:
        amount = _duration(match.group(1))
        if amount is not None:
            direction = -1 if match.group(2) == "ago" else 1
            months, weeks, days = amount
            return _shift(
                reference,
                months=direction * months,
                weeks=direction * weeks,
                days=direction * days,
            )

    match = re.fullmatch(r"(.+?)\s+(before|after|from|prior to)\s+(.+)", text)
    if match:
        amount = _duration(match.group(1))
        if amount is not None:
            anchor = parse(match.group(3), reference)
            direction = -1 if match.group(2) in ("before", "prior to") else 1
            months, weeks, days = amount
            return _shift(
                anchor,
                months=direction * months,
                weeks=direction * weeks,
                days=direction * days,
            )

    absolute = _absolute(text.removeprefix("on "), reference)
    if absolute is not None:
        return absolute
    raise ValueError(f"unrecognized date expression: {s!r}")


def main() -> None:
    """Minimal command-line smoke check."""
    print(parse("today"))
