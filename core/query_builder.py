"""Process selfie images and build query embeddings."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import insightface

from core.face_service import detect_faces, load_image, DetectedFace


def _select_main_face(
    faces: list[DetectedFace],
    image_width: int,
    image_height: int,
) -> DetectedFace:
    """Select the largest face closest to the image centre.

    The heuristic scores each face by its area and penalises distance from
    the image centre so that the most prominent, central face wins.

    Args:
        faces: Detected faces in the selfie.
        image_width: Width of the source image in pixels.
        image_height: Height of the source image in pixels.

    Returns:
        The ``DetectedFace`` deemed to be the main subject.
    """
    centre_x = image_width / 2
    centre_y = image_height / 2

    best_face: DetectedFace | None = None
    best_score: float = -1.0

    for face in faces:
        x1, y1, x2, y2 = face.bbox
        face_cx = (x1 + x2) / 2
        face_cy = (y1 + y2) / 2
        area = (x2 - x1) * (y2 - y1)

        # Normalised distance from centre (0 = centre, 1 = corner)
        max_dist = (centre_x**2 + centre_y**2) ** 0.5
        dist = ((face_cx - centre_x) ** 2 + (face_cy - centre_y) ** 2) ** 0.5
        norm_dist = dist / max_dist if max_dist > 0 else 0.0

        # Favour large, central faces
        score = area * (1.0 - norm_dist)

        if score > best_score:
            best_score = score
            best_face = face

    assert best_face is not None
    return best_face


def build_query_embeddings(
    model: insightface.app.FaceAnalysis,
    selfie_paths: list[str | Path],
) -> list[np.ndarray]:
    """Extract one embedding per selfie image.

    For each selfie the largest / most-central face is selected.  Images
    that cannot be read or contain no detectable face are skipped with a
    warning printed to *stdout*.

    Args:
        model: Prepared InsightFace model.
        selfie_paths: Paths to selfie images.

    Returns:
        List of 512-d embedding vectors (one per valid selfie).
    """
    embeddings: list[np.ndarray] = []

    for path in selfie_paths:
        path = Path(path)
        image = load_image(str(path))
        if image is None:
            print(f"[WARN] Could not read selfie image: {path}")
            continue

        faces = detect_faces(model, image)
        if not faces:
            print(f"[WARN] No face detected in selfie: {path}")
            continue

        h, w = image.shape[:2]
        main_face = _select_main_face(faces, w, h)
        embeddings.append(main_face.embedding)

    return embeddings
