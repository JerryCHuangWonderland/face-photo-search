"""Recursively scan a folder and collect valid image file paths."""

from pathlib import Path

from core.config import SUPPORTED_IMAGE_FORMATS


def scan_images(folder: str | Path) -> list[Path]:
    """Recursively scan *folder* and return paths to supported image files.

    Args:
        folder: Root directory to scan.

    Returns:
        Sorted list of ``Path`` objects pointing to valid image files.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Dataset folder not found: {folder}")

    image_paths: list[Path] = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            image_paths.append(path)

    return image_paths
