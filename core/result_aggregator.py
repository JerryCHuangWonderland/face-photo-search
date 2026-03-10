"""Merge duplicate photo matches and assign final rankings."""

from __future__ import annotations

from core.matcher import MatchResult


def aggregate_results(matches: list[MatchResult]) -> list[MatchResult]:
    """Merge matches that refer to the same photo, keeping the highest score.

    When a photo appears multiple times (e.g. different faces matched
    different query embeddings), only the entry with the highest
    ``best_score`` is retained.

    After de-duplication the results are sorted by descending score and
    each entry receives a 1-based rank.

    Args:
        matches: Raw match results (may contain duplicates per photo).

    Returns:
        De-duplicated, ranked list of ``MatchResult`` objects.
    """
    best_by_photo: dict[str, MatchResult] = {}

    for match in matches:
        existing = best_by_photo.get(match.photo_path)
        if existing is None or match.best_score > existing.best_score:
            best_by_photo[match.photo_path] = match

    sorted_results = sorted(
        best_by_photo.values(),
        key=lambda m: m.best_score,
        reverse=True,
    )

    for idx, result in enumerate(sorted_results, start=1):
        result.rank = idx

    return sorted_results
