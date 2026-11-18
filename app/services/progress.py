"""Pure academic progress calculations shared by services and scripts."""


def percentage(completed: int, total: int) -> int:
    """Return a rounded whole-number percentage, or zero when no items exist."""
    return round(completed / total * 100) if total else 0
