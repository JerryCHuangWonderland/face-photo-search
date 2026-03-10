"""Pipeline runner for the face photo search system.

Usage:
    python -m app.main --selfies <selfie_dir_or_files> --dataset <dataset_dir> [--threshold 0.45]
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tqdm import tqdm

from core.config import DEFAULT_THRESHOLD, SUPPORTED_IMAGE_FORMATS
from core.face_service import load_model, detect_faces, load_image
from core.file_scanner import scan_images
from core.matcher import CandidateFace, MatchResult, find_matches
from core.query_builder import build_query_embeddings
from core.result_aggregator import aggregate_results
from core.reporter import export_results, print_statistics, Statistics
from core.dataset_index import PreparedDataset


@dataclass
class PipelineResult:
    """Container returned by :func:`run_search_pipeline`."""

    results: list[MatchResult]
    stats: Statistics
    query_count: int


def _collect_selfie_paths(selfie_arg: list[str]) -> list[Path]:
    """Resolve selfie paths from CLI arguments.

    Each argument may be a file or a directory.  Directories are scanned
    (non-recursively) for supported images.
    """
    paths: list[Path] = []
    for item in selfie_arg:
        p = Path(item)
        if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            paths.append(p)
        elif p.is_dir():
            for child in sorted(p.iterdir()):
                if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    paths.append(child)
        else:
            print(f"[WARN] Skipping invalid selfie path: {p}")
    return paths


def run_search_pipeline(
    model: object,
    selfie_paths: list[Path],
    dataset_dir: Path,
    threshold: float = DEFAULT_THRESHOLD,
    on_progress: Callable[[int, int], None] | None = None,
) -> PipelineResult:
    """Run the face-search pipeline and return structured results.

    Unlike :func:`run_pipeline` this function accepts a pre-loaded model,
    returns a :class:`PipelineResult` instead of writing files, and
    reports progress via an optional callback — making it suitable for
    both CLI wrappers and the Streamlit UI.

    Args:
        model: Prepared InsightFace ``FaceAnalysis`` instance.
        selfie_paths: Paths to selfie image files.
        dataset_dir: Root directory of the photo dataset.
        threshold: Minimum cosine similarity for a match.
        on_progress: Optional ``(current, total)`` callback invoked once
            per dataset image during face detection.

    Returns:
        A :class:`PipelineResult` with ranked matches and statistics.

    Raises:
        ValueError: If no valid selfie faces or dataset images are found.
    """
    start_time = time.time()

    # Build query embeddings from selfies
    query_embeddings = build_query_embeddings(model, selfie_paths)
    if not query_embeddings:
        raise ValueError("No valid face detected in any selfie image.")

    # Scan dataset for images
    image_paths = scan_images(dataset_dir)
    if not image_paths:
        raise ValueError(f"No images found in dataset folder: {dataset_dir}")

    # Detect faces in every dataset image
    candidate_faces: list[CandidateFace] = []
    photos_with_faces: int = 0
    failed_images: int = 0
    total = len(image_paths)

    for idx, img_path in enumerate(image_paths):
        if on_progress:
            on_progress(idx + 1, total)

        image = load_image(str(img_path))
        if image is None:
            failed_images += 1
            continue

        faces = detect_faces(model, image)
        if faces:
            photos_with_faces += 1
            for face in faces:
                candidate_faces.append(
                    CandidateFace(
                        photo_path=str(img_path),
                        bbox=face.bbox,
                        embedding=face.embedding,
                    )
                )

    # Match against query embeddings and aggregate
    raw_matches = find_matches(query_embeddings, candidate_faces, threshold)
    results = aggregate_results(raw_matches)

    elapsed = time.time() - start_time
    stats = Statistics(
        total_photos_scanned=total,
        photos_with_faces=photos_with_faces,
        matched_photos=len(results),
        failed_images=failed_images,
        processing_time=round(elapsed, 2),
    )

    return PipelineResult(
        results=results,
        stats=stats,
        query_count=len(query_embeddings),
    )


def run_search_from_index(
    model: object,
    selfie_paths: list[Path],
    prepared: PreparedDataset,
    threshold: float = DEFAULT_THRESHOLD,
) -> PipelineResult:
    """Run search against a :class:`PreparedDataset` index.

    This skips dataset scanning and face detection entirely — only
    selfie processing, matching, and aggregation are performed.

    Args:
        model: Prepared InsightFace ``FaceAnalysis`` instance.
        selfie_paths: Paths to selfie image files.
        prepared: A previously built :class:`PreparedDataset`.
        threshold: Minimum cosine similarity for a match.

    Returns:
        A :class:`PipelineResult` with ranked matches and statistics.

    Raises:
        ValueError: If no valid selfie faces are found.
    """
    start_time = time.time()

    query_embeddings = build_query_embeddings(model, selfie_paths)
    if not query_embeddings:
        raise ValueError("No valid face detected in any selfie image.")

    raw_matches = find_matches(query_embeddings, prepared.candidate_faces, threshold)
    results = aggregate_results(raw_matches)

    elapsed = time.time() - start_time
    stats = Statistics(
        total_photos_scanned=prepared.total_photos,
        photos_with_faces=prepared.photos_with_faces,
        matched_photos=len(results),
        failed_images=prepared.failed_images,
        processing_time=round(elapsed, 2),
    )

    return PipelineResult(
        results=results,
        stats=stats,
        query_count=len(query_embeddings),
    )


def run_pipeline(
    selfie_paths: list[Path],
    dataset_dir: Path,
    threshold: float = DEFAULT_THRESHOLD,
) -> None:
    """Execute the full face-search pipeline.

    Steps:
        1. Load InsightFace model
        2. Build query embeddings from selfie images
        3. Scan dataset folder for images
        4. Detect faces in each dataset image
        5. Match candidate faces against query embeddings
        6. Aggregate results (de-duplicate, rank)
        7. Export results.json and print statistics
    """
    start_time = time.time()

    # --- Step 1: Load model ---
    print("[1/7] Loading InsightFace model …")
    model = load_model()

    # --- Step 2: Build query embeddings ---
    print(f"[2/7] Processing {len(selfie_paths)} selfie(s) …")
    query_embeddings = build_query_embeddings(model, selfie_paths)
    if not query_embeddings:
        print("[ERROR] No valid query embeddings. Aborting.")
        sys.exit(1)
    print(f"       → {len(query_embeddings)} query embedding(s) extracted.")

    # --- Step 3: Scan dataset ---
    print(f"[3/7] Scanning dataset folder: {dataset_dir}")
    image_paths = scan_images(dataset_dir)
    print(f"       → {len(image_paths)} image(s) found.")
    if not image_paths:
        print("[ERROR] No images found in dataset folder. Aborting.")
        sys.exit(1)

    # --- Step 4: Detect faces in dataset ---
    print("[4/7] Detecting faces in dataset images …")
    candidate_faces: list[CandidateFace] = []
    photos_with_faces: int = 0
    failed_images: int = 0

    for img_path in tqdm(image_paths, desc="Scanning faces", unit="img"):
        image = load_image(str(img_path))
        if image is None:
            failed_images += 1
            continue

        faces = detect_faces(model, image)
        if faces:
            photos_with_faces += 1
            for face in faces:
                candidate_faces.append(
                    CandidateFace(
                        photo_path=str(img_path),
                        bbox=face.bbox,
                        embedding=face.embedding,
                    )
                )

    print(f"       → {len(candidate_faces)} face(s) detected in {photos_with_faces} photo(s).")

    # --- Step 5: Compute similarity ---
    print(f"[5/7] Matching faces (threshold={threshold}) …")
    raw_matches = find_matches(query_embeddings, candidate_faces, threshold)
    print(f"       → {len(raw_matches)} raw match(es).")

    # --- Step 6: Aggregate results ---
    print("[6/7] Aggregating results …")
    results = aggregate_results(raw_matches)
    print(f"       → {len(results)} unique photo(s) matched.")

    # --- Step 7: Export ---
    elapsed = time.time() - start_time
    stats = Statistics(
        total_photos_scanned=len(image_paths),
        photos_with_faces=photos_with_faces,
        matched_photos=len(results),
        failed_images=failed_images,
        processing_time=round(elapsed, 2),
    )

    print("[7/7] Exporting results …")
    output_path = export_results(results, stats)
    print(f"       → Results written to {output_path}")

    print_statistics(stats)

    if not results:
        print("No matching photos found.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Face Photo Search — find photos of a person in a dataset."
    )
    parser.add_argument(
        "--selfies",
        nargs="+",
        required=True,
        help="Path(s) to selfie image files or directories containing selfies.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to the dataset folder to search.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Cosine similarity threshold (default: {DEFAULT_THRESHOLD}).",
    )

    args = parser.parse_args()

    selfie_paths = _collect_selfie_paths(args.selfies)
    if not selfie_paths:
        print("[ERROR] No valid selfie images provided.")
        sys.exit(1)

    dataset_dir = Path(args.dataset)
    if not dataset_dir.is_dir():
        print(f"[ERROR] Dataset directory not found: {dataset_dir}")
        sys.exit(1)

    run_pipeline(selfie_paths, dataset_dir, args.threshold)


if __name__ == "__main__":
    main()
