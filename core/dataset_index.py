"""Dataset preprocessing and indexing for reusable face search.

This module provides a one-time preparation step that scans a dataset
folder, detects faces, extracts embeddings, and caches pre-rendered
images so that subsequent searches only need to compute query
embeddings and run matching — skipping the expensive detection phase.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from core.face_service import detect_faces, load_image
from core.file_scanner import scan_images
from core.matcher import CandidateFace


@dataclass
class PreparedDataset:
    """Immutable snapshot of a preprocessed dataset.

    Holds all information needed for repeated searches without
    re-reading or re-detecting faces in the dataset images.
    """

    candidate_faces: list[CandidateFace]
    total_photos: int
    photos_with_faces: int
    failed_images: int
    preparation_time: float
    # Mapping: safe temp path → original upload name (for display).
    name_map: dict[str, str] = field(default_factory=dict)
    # Pre-rendered PIL images keyed by safe temp path (survives temp cleanup).
    image_cache: dict[str, Image.Image] = field(default_factory=dict)


def prepare_dataset(
    model: object,
    dataset_dir: Path,
    name_map: dict[str, str] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> PreparedDataset:
    """Scan *dataset_dir*, detect faces, and build a reusable index.

    Args:
        model: Prepared InsightFace ``FaceAnalysis`` instance.
        dataset_dir: Root directory containing dataset images.
        name_map: Optional mapping of safe-path → original-name.
        on_progress: ``(current, total)`` callback per image.

    Returns:
        A :class:`PreparedDataset` with all candidate embeddings.

    Raises:
        ValueError: If no images are found in *dataset_dir*.
    """
    import cv2

    start = time.time()

    image_paths = scan_images(dataset_dir)
    if not image_paths:
        raise ValueError(f"No images found in dataset folder: {dataset_dir}")

    candidate_faces: list[CandidateFace] = []
    photos_with_faces = 0
    failed_images = 0
    total = len(image_paths)
    image_cache: dict[str, Image.Image] = {}

    for idx, img_path in enumerate(image_paths):
        if on_progress:
            on_progress(idx + 1, total)

        image = load_image(str(img_path))
        if image is None:
            failed_images += 1
            continue

        # Cache the original image as PIL for later bbox drawing
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_cache[str(img_path)] = Image.fromarray(rgb)

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

    elapsed = time.time() - start

    return PreparedDataset(
        candidate_faces=candidate_faces,
        total_photos=total,
        photos_with_faces=photos_with_faces,
        failed_images=failed_images,
        preparation_time=round(elapsed, 2),
        name_map=name_map or {},
        image_cache=image_cache,
    )
