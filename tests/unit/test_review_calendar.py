from datetime import UTC, date, datetime

import pytest

from app.repositories.review_missions import review_due_date


@pytest.mark.parametrize(("instant", "expected"), [
    (datetime(2026, 11, 17, 23, 59, 59, tzinfo=UTC), date(2026, 11, 20)),
    (datetime(2026, 11, 18, 0, 0, tzinfo=UTC), date(2026, 11, 20)),
    (datetime(2026, 11, 18, 2, 59, 59, tzinfo=UTC), date(2026, 11, 20)),
    (datetime(2026, 11, 18, 3, 0, tzinfo=UTC), date(2026, 11, 21)),
    (datetime(2027, 1, 1, 0, 0, tzinfo=UTC), date(2027, 1, 3)),
])
def test_review_due_date_uses_sao_paulo_calendar(instant, expected):
    # Explicit expectations: do not repeat the production conversion in the test.
    assert review_due_date(instant) == expected
