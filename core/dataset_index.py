"""Dataset preprocessing and indexing for reusable face search.

This module provides a one-time preparation step that scans a dataset
folder, detects faces, extracts embeddings, and caches pre-rendered
images so that subsequent searches only need to compute query
embeddings and run matching — skipping the expensive detection phase.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Any
from typing import Callable
from uuid import uuid4

import numpy as np
from PIL import Image

from core.config import DATASET_STORAGE_DIR
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
    dataset_name: str = ""
    # Mapping: safe temp path → original upload name (for display).
    name_map: dict[str, str] = field(default_factory=dict)
    # Pre-rendered PIL images keyed by safe temp path (survives temp cleanup).
    image_cache: dict[str, Image.Image] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetSummary:
    """Compact metadata for a persisted dataset index."""

    name: str
    created_at: str
    preparation_time: float
    total_photos: int
    photos_with_faces: int
    failed_images: int
    candidate_faces: int


@dataclass(frozen=True)
class DatasetPhotoInfo:
    """Photo entry stored inside a persisted dataset snapshot."""

    path: str
    display_name: str


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


def _dataset_root(base_dir: str | Path = DATASET_STORAGE_DIR) -> Path:
    """Return the configured dataset storage directory."""
    return Path(base_dir)


def validate_dataset_name(dataset_name: str) -> str:
    """Validate and normalize a dataset name used as a folder name."""
    normalized = dataset_name.strip()
    if not normalized:
        raise ValueError("Please enter a dataset name.")
    if any(sep in normalized for sep in ("/", "\\")):
        raise ValueError("Dataset names cannot contain folder separators.")
    if normalized in {".", ".."}:
        raise ValueError("Dataset name is invalid.")
    if re.search(r'[<>:"|?*]', normalized):
        raise ValueError(
            "Dataset names cannot contain these characters: < > : \" | ? *"
        )
    if normalized.endswith((" ", ".")):
        raise ValueError("Dataset names cannot end with a space or period.")
    return normalized


def _dataset_dir(dataset_name: str, base_dir: str | Path = DATASET_STORAGE_DIR) -> Path:
    """Return the directory path for a named dataset."""
    return _dataset_root(base_dir) / validate_dataset_name(dataset_name)


def _metadata_path(dataset_name: str, base_dir: str | Path = DATASET_STORAGE_DIR) -> Path:
    """Return the metadata file path for a named dataset."""
    return _dataset_dir(dataset_name, base_dir) / "metadata.json"


def _load_metadata(
    dataset_name: str,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> tuple[Path, dict[str, Any]]:
    """Load dataset metadata and return its parent directory with payload."""
    metadata_path = _metadata_path(dataset_name, base_dir)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Dataset metadata not found: {dataset_name}")

    with metadata_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    return metadata_path.parent, payload


def _write_metadata(metadata_path: Path, payload: dict[str, Any]) -> None:
    """Write dataset metadata back to disk."""
    with metadata_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def _sanitize_relative_name(name: str) -> Path:
    """Convert a user-facing upload name into a safe relative path."""
    parts = [part for part in Path(name.replace("\\", "/")).parts if part not in ("", ".")]
    safe_parts = [part for part in parts if part != ".."]
    if not safe_parts:
        return Path(f"image_{uuid4().hex}.jpg")
    return Path(*safe_parts)


def _make_unique_path(relative_path: Path, used_paths: set[str]) -> Path:
    """Ensure *relative_path* is unique within a dataset snapshot."""
    candidate = relative_path
    counter = 1
    key = candidate.as_posix().lower()
    while key in used_paths:
        candidate = relative_path.with_name(
            f"{relative_path.stem}_{counter}{relative_path.suffix}"
        )
        counter += 1
        key = candidate.as_posix().lower()
    used_paths.add(key)
    return candidate


def list_saved_datasets(
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> list[DatasetSummary]:
    """Return all saved dataset summaries sorted by name."""
    root = _dataset_root(base_dir)
    if not root.exists():
        return []

    summaries: list[DatasetSummary] = []
    for child in sorted(root.iterdir()):
        metadata_path = child / "metadata.json"
        if not child.is_dir() or not metadata_path.exists():
            continue

        _, payload = _load_metadata(child.name, base_dir)

        summaries.append(
            DatasetSummary(
                name=payload["name"],
                created_at=payload["created_at"],
                preparation_time=float(payload["preparation_time"]),
                total_photos=int(payload["total_photos"]),
                photos_with_faces=int(payload["photos_with_faces"]),
                failed_images=int(payload["failed_images"]),
                candidate_faces=int(payload["candidate_face_count"]),
            )
        )

    return summaries


def save_prepared_dataset(
    prepared: PreparedDataset,
    dataset_name: str,
    source_dir: Path,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> Path:
    """Persist a prepared dataset and a copy of its source photos."""
    dataset_dir = _dataset_dir(dataset_name, base_dir)
    if dataset_dir.exists():
        raise FileExistsError(f"Dataset already exists: {dataset_name}")

    photos_dir = dataset_dir / "photos"
    photos_dir.mkdir(parents=True, exist_ok=False)

    stored_name_map: dict[str, str] = {}
    path_map: dict[str, str] = {}
    used_paths: set[str] = set()

    for source_path in scan_images(source_dir):
        source_key = str(source_path)
        original_name = prepared.name_map.get(source_key, source_path.name)
        relative_name = _make_unique_path(_sanitize_relative_name(original_name), used_paths)
        destination = photos_dir / relative_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

        stored_rel_path = Path("photos") / relative_name
        path_map[source_key] = stored_rel_path.as_posix()
        stored_name_map[stored_rel_path.as_posix()] = original_name

    faces_payload: list[dict[str, Any]] = []
    embeddings: list[np.ndarray] = []
    for candidate in prepared.candidate_faces:
        stored_rel_path = path_map.get(candidate.photo_path)
        if stored_rel_path is None:
            continue
        faces_payload.append(
            {
                "photo_rel_path": stored_rel_path,
                "bbox": candidate.bbox,
            }
        )
        embeddings.append(np.asarray(candidate.embedding, dtype=np.float32))

    embedding_matrix = (
        np.stack(embeddings).astype(np.float32)
        if embeddings
        else np.empty((0, 0), dtype=np.float32)
    )
    np.save(dataset_dir / "embeddings.npy", embedding_matrix)

    metadata = {
        "name": dataset_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "preparation_time": prepared.preparation_time,
        "total_photos": prepared.total_photos,
        "photos_with_faces": prepared.photos_with_faces,
        "failed_images": prepared.failed_images,
        "candidate_face_count": len(faces_payload),
        "display_names": stored_name_map,
        "faces": faces_payload,
    }

    _write_metadata(dataset_dir / "metadata.json", metadata)

    return dataset_dir


def list_dataset_photos(
    dataset_name: str,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> list[DatasetPhotoInfo]:
    """List the original photos stored in a persisted dataset snapshot."""
    dataset_dir, metadata = _load_metadata(dataset_name, base_dir)

    photos: list[DatasetPhotoInfo] = []
    for rel_path, original_name in metadata["display_names"].items():
        photos.append(
            DatasetPhotoInfo(
                path=str((dataset_dir / rel_path).resolve()),
                display_name=original_name,
            )
        )

    photos.sort(key=lambda item: (item.display_name.lower(), item.path.lower()))
    return photos


def rename_saved_dataset(
    old_name: str,
    new_name: str,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> Path:
    """Rename a persisted dataset folder and update its metadata."""
    current_name = validate_dataset_name(old_name)
    updated_name = validate_dataset_name(new_name)

    if current_name == updated_name:
        return _dataset_dir(current_name, base_dir)

    current_dir = _dataset_dir(current_name, base_dir)
    if not current_dir.exists():
        raise FileNotFoundError(f"Dataset not found: {current_name}")

    updated_dir = _dataset_dir(updated_name, base_dir)
    if updated_dir.exists():
        raise FileExistsError(f"Dataset already exists: {updated_name}")

    current_dir.rename(updated_dir)
    metadata_path = updated_dir / "metadata.json"
    with metadata_path.open("r", encoding="utf-8") as fh:
        metadata = json.load(fh)

    metadata["name"] = updated_name
    _write_metadata(metadata_path, metadata)
    return updated_dir


def delete_saved_dataset(
    dataset_name: str,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> None:
    """Delete a persisted dataset and its stored photos."""
    dataset_dir = _dataset_dir(dataset_name, base_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_name}")

    shutil.rmtree(dataset_dir)


def load_prepared_dataset(
    dataset_name: str,
    base_dir: str | Path = DATASET_STORAGE_DIR,
) -> PreparedDataset:
    """Load a previously persisted dataset index from disk."""
    dataset_dir, metadata = _load_metadata(dataset_name, base_dir)

    embeddings = np.load(dataset_dir / "embeddings.npy")

    candidate_faces: list[CandidateFace] = []
    for index, face in enumerate(metadata["faces"]):
        photo_path = str((dataset_dir / face["photo_rel_path"]).resolve())
        embedding = (
            embeddings[index].astype(np.float32)
            if len(embeddings) > index
            else np.empty((0,), dtype=np.float32)
        )
        candidate_faces.append(
            CandidateFace(
                photo_path=photo_path,
                bbox=[int(value) for value in face["bbox"]],
                embedding=embedding,
            )
        )

    name_map = {
        str((dataset_dir / rel_path).resolve()): original_name
        for rel_path, original_name in metadata["display_names"].items()
    }

    return PreparedDataset(
        candidate_faces=candidate_faces,
        total_photos=int(metadata["total_photos"]),
        photos_with_faces=int(metadata["photos_with_faces"]),
        failed_images=int(metadata["failed_images"]),
        preparation_time=float(metadata["preparation_time"]),
        dataset_name=metadata["name"],
        name_map=name_map,
        image_cache={},
    )
