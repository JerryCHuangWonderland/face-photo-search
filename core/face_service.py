"""Face detection and embedding extraction using InsightFace."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import cv2
import numpy as np

# Suppress FutureWarning from insightface's internal use of a deprecated
# scikit-image API (SimilarityTransform.estimate → from_estimate).
warnings.filterwarnings(
    "ignore",
    message=r".*`estimate` is deprecated.*",
    category=FutureWarning,
)

import insightface  # noqa: E402  (must come after the filter)

from core.config import MODEL_NAME, DET_SIZE, PROVIDERS


@dataclass
class DetectedFace:
    """A single face detected in an image."""

    bbox: list[int]
    embedding: np.ndarray


def load_model(model_name: str = MODEL_NAME) -> insightface.app.FaceAnalysis:
    """Load and prepare the InsightFace model.

    Supports both old (<=0.2) and new (>=0.7) insightface API.

    Args:
        model_name: Name of the InsightFace model pack.

    Returns:
        A prepared ``FaceAnalysis`` instance.
    """
    import inspect

    init_sig = inspect.signature(insightface.app.FaceAnalysis.__init__)
    if "providers" in init_sig.parameters:
        # insightface >= 0.7
        app = insightface.app.FaceAnalysis(
            name=model_name,
            providers=PROVIDERS,
        )
        app.prepare(ctx_id=0, det_size=DET_SIZE)
    else:
        # insightface <= 0.2 — no providers param; use ctx_id=-1 for CPU
        app = insightface.app.FaceAnalysis(name=model_name)
        app.prepare(ctx_id=-1, det_size=DET_SIZE)
    return app


def detect_faces(
    model: insightface.app.FaceAnalysis,
    image: np.ndarray,
) -> list[DetectedFace]:
    """Detect all faces in *image* and return bounding boxes with embeddings.

    Args:
        model: A prepared ``FaceAnalysis`` model.
        image: BGR image as a NumPy array (OpenCV format).

    Returns:
        List of ``DetectedFace`` objects.
    """
    faces = model.get(image)
    results: list[DetectedFace] = []
    for face in faces:
        bbox = [int(v) for v in face.bbox]
        embedding: np.ndarray = face.embedding
        results.append(DetectedFace(bbox=bbox, embedding=embedding))
    return results


def load_image(path: str) -> np.ndarray | None:
    """Read an image from disk using OpenCV.

    Uses ``np.fromfile`` + ``cv2.imdecode`` to support file paths
    containing non-ASCII characters (e.g. Chinese) on Windows, where
    ``cv2.imread`` silently fails on such paths.

    Args:
        path: File system path to the image.

    Returns:
        BGR image array, or ``None`` if the file could not be read.
    """
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None
