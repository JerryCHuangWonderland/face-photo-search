"""Configuration constants for the face photo search system."""

# Supported image file extensions
SUPPORTED_IMAGE_FORMATS: set[str] = {".jpg", ".jpeg", ".png"}

# InsightFace model name
MODEL_NAME: str = "buffalo_l"

# Detection input size
DET_SIZE: tuple[int, int] = (640, 640)

# Execution provider for ONNX Runtime (CPU-only)
PROVIDERS: list[str] = ["CPUExecutionProvider"]

# Default cosine similarity threshold
DEFAULT_THRESHOLD: float = 0.45

# UI slider range for threshold adjustment
SLIDER_MIN: float = 0.2
SLIDER_MAX: float = 0.8
SLIDER_STEP: float = 0.05

# Output paths
OUTPUT_DIR: str = "outputs"
RESULTS_FILENAME: str = "results.json"
