# nldate

A small, dependency-free Python library for common English date expressions.

## Usage

```python
from datetime import date
from nldate import parse

reference = date(2026, 11, 9)
assert parse("next Tuesday", today=reference) == date(2026, 11, 10)
assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)
assert parse("two weeks from tomorrow", today=reference) == date(2026, 11, 24)
```

Supported forms include ISO dates, US numeric dates, English month-name dates, weekdays,
relative days, named periods, compound offsets, and the start or end of a month or year.
Unknown and invalid expressions raise `ValueError`.

## Quality checks

```bash
uv run pytest
uv run mypy src/
uv run ruff check
uv run ruff format --check
```
