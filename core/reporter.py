"""Export search results to JSON and compute run statistics."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

from core.config import OUTPUT_DIR, RESULTS_FILENAME
from core.matcher import MatchResult


@dataclass
class Statistics:
    """Summary statistics for a search run."""

    total_photos_scanned: int
    photos_with_faces: int
    matched_photos: int
    failed_images: int
    processing_time: float  # seconds


def export_results(
    results: list[MatchResult],
    stats: Statistics,
    output_dir: str | Path = OUTPUT_DIR,
) -> Path:
    """Write results and statistics to a JSON file.

    Args:
        results: Ranked match results.
        stats: Run statistics.
        output_dir: Directory to write the output file into.

    Returns:
        Path to the written JSON file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / RESULTS_FILENAME

    payload = {
        "results": [
            {
                "photo_path": r.photo_path,
                "best_bbox": r.best_bbox,
                "best_score": r.best_score,
                "matched_query_index": r.matched_query_index,
                "rank": r.rank,
            }
            for r in results
        ],
        "statistics": asdict(stats),
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return output_path


def print_statistics(stats: Statistics) -> None:
    """Print run statistics to stdout."""
    print("\n===== Search Statistics =====")
    print(f"  Total photos scanned : {stats.total_photos_scanned}")
    print(f"  Photos with faces    : {stats.photos_with_faces}")
    print(f"  Matched photos       : {stats.matched_photos}")
    print(f"  Failed images        : {stats.failed_images}")
    print(f"  Processing time      : {stats.processing_time:.2f}s")
    print("=============================\n")
