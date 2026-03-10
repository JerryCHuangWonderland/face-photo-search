"""Streamlit UI for the Face Photo Search System.

Run from the project root with::

    py -3.12 -m streamlit run app/ui.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import streamlit as st
from PIL import Image

# Ensure the project root is importable regardless of how Streamlit
# manipulates sys.path (it prepends the *script* directory, not the cwd).
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.config import DEFAULT_THRESHOLD, SLIDER_MIN, SLIDER_MAX, SLIDER_STEP
from core.face_service import load_model
from core.reporter import export_results
from app.main import run_search_pipeline


# ── Model caching ──────────────────────────────────────────────────────


@st.cache_resource(show_spinner="Loading face recognition model…")
def _get_model():
    """Load the InsightFace model once and cache across reruns."""
    return load_model()


# ── Helpers ────────────────────────────────────────────────────────────


def _save_uploads_to_dir(
    uploaded_files: list, dest_dir: Path, *, preserve_structure: bool = False
) -> list[Path]:
    """Persist Streamlit ``UploadedFile`` objects into *dest_dir*.

    Args:
        uploaded_files: List of Streamlit ``UploadedFile`` objects.
        dest_dir: Target directory (must already exist).
        preserve_structure: When ``True`` (used for directory uploads),
            the ``name`` field may contain a relative path like
            ``"subdir/photo.jpg"``.  Subdirectories are created
            automatically and duplicate basenames in different folders
            are preserved.

    Returns:
        List of saved file paths.
    """
    paths: list[Path] = []
    seen: set[str] = set()
    for uf in uploaded_files:
        rel = Path(uf.name)
        if preserve_structure and len(rel.parts) > 1:
            dest = dest_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Flat mode — guard against duplicate basenames
            stem, suffix = rel.stem, rel.suffix
            name = rel.name
            counter = 1
            while name in seen:
                name = f"{stem}_{counter}{suffix}"
                counter += 1
            seen.add(name)
            dest = dest_dir / name
        dest.write_bytes(uf.getvalue())
        paths.append(dest)
    return paths


def _draw_bbox(image_path: str, bbox: list[int]) -> Image.Image | None:
    """Load a photo and draw the matched-face bounding box.

    Uses ``np.fromfile`` + ``cv2.imdecode`` to support file paths
    containing non-ASCII characters (e.g. Chinese) on Windows.

    Returns:
        PIL RGB image with the bounding box drawn, or ``None`` if the
        file cannot be read.
    """
    import numpy as np

    try:
        data = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        img = None
    if img is None:
        return None
    h, w = img.shape[:2]
    x1, y1 = max(0, bbox[0]), max(0, bbox[1])
    x2, y2 = min(w, bbox[2]), min(h, bbox[3])
    thickness = max(2, min(h, w) // 200)
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), thickness)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def _cleanup_temp_dir(path: Path | None) -> None:
    """Safely remove a temporary directory and all its contents."""
    if path is not None and path.exists():
        shutil.rmtree(path, ignore_errors=True)


# ── Page layout ────────────────────────────────────────────────────────


def main() -> None:
    """Render the Streamlit application."""

    st.set_page_config(
        page_title="Face Photo Search",
        page_icon="📷",
        layout="wide",
    )

    st.title("📷 Face Photo Search")
    st.caption(
        "Upload one or more selfie images and select a dataset folder "
        "to find photos containing the same person."
    )

    # ── Sidebar ────────────────────────────────────────────────────────

    with st.sidebar:
        st.header("🔍 Search Settings")

        uploaded_selfies = st.file_uploader(
            "Upload Selfie Images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload clear selfie photos of the person to search for.",
        )

        # Use a counter in session_state to generate a fresh widget key
        # so that clicking "Clear" resets the file uploader.
        if "dataset_uploader_key" not in st.session_state:
            st.session_state["dataset_uploader_key"] = 0

        uploaded_dataset = st.file_uploader(
            "Upload Dataset Folder",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files="directory",
            key=f"dataset_uploader_{st.session_state['dataset_uploader_key']}",
            help=(
                "Click **Browse files** and select your photo folder. "
                "All images (including subfolders) will be uploaded. "
                "Supported formats: JPG, JPEG, PNG."
            ),
        )

        if uploaded_dataset:
            st.caption(f"📁 {len(uploaded_dataset)} photo(s) uploaded from folder")
            if st.button("🗑️ Clear Dataset", use_container_width=True):
                st.session_state["dataset_uploader_key"] += 1
                st.session_state.pop("search_result", None)
                st.session_state.pop("result_images", None)
                st.rerun()

        threshold = st.slider(
            "Similarity Threshold",
            min_value=SLIDER_MIN,
            max_value=SLIDER_MAX,
            value=DEFAULT_THRESHOLD,
            step=SLIDER_STEP,
            help="Lower values return more results but may include false matches.",
        )

        search_clicked = st.button(
            "🔍 Search", type="primary", use_container_width=True
        )

    # ── Query face preview ─────────────────────────────────────────────

    if uploaded_selfies:
        st.subheader("📸 Query Faces")
        preview_cols = st.columns(min(len(uploaded_selfies), 5))
        for idx, selfie_file in enumerate(uploaded_selfies):
            with preview_cols[idx % len(preview_cols)]:
                pil_img = Image.open(selfie_file)
                st.image(pil_img, caption=selfie_file.name, use_container_width=True)

    # ── Search execution ───────────────────────────────────────────────

    if search_clicked:
        # Clear stale results from a previous run
        st.session_state.pop("search_result", None)
        st.session_state.pop("result_images", None)

        # --- Input validation ---
        if not uploaded_selfies:
            st.error("❌ Please upload at least one selfie image.")
            st.stop()

        if not uploaded_dataset:
            st.error(
                "❌ Please upload a dataset folder. Use the **Upload Dataset "
                "Folder** widget in the sidebar to select a photo folder."
            )
            st.stop()

        # --- Save uploads to temp directories ---
        selfie_tmp: Path | None = None
        dataset_tmp: Path | None = None

        try:
            selfie_tmp = Path(tempfile.mkdtemp(prefix="fps_selfies_"))
            dataset_tmp = Path(tempfile.mkdtemp(prefix="fps_dataset_"))

            selfie_paths = _save_uploads_to_dir(uploaded_selfies, selfie_tmp)
            dataset_paths = _save_uploads_to_dir(
                uploaded_dataset, dataset_tmp, preserve_structure=True
            )

            if not dataset_paths:
                st.warning(
                    "⚠️ The uploaded folder contains no valid images "
                    "(JPG, JPEG, PNG)."
                )
                st.stop()

            # --- Load model ---
            try:
                model = _get_model()
            except Exception as exc:
                st.error(f"❌ Failed to load face recognition model: {exc}")
                st.stop()

            # --- Run pipeline with progress bar ---
            progress_bar = st.progress(0, text="Preparing search…")

            def _on_progress(current: int, total: int) -> None:
                progress_bar.progress(
                    current / total,
                    text=f"Detecting faces… {current}/{total} images",
                )

            try:
                result = run_search_pipeline(
                    model=model,
                    selfie_paths=selfie_paths,
                    dataset_dir=dataset_tmp,
                    threshold=threshold,
                    on_progress=_on_progress,
                )
            except ValueError as exc:
                progress_bar.empty()
                st.warning(f"⚠️ {exc}")
                st.stop()
            except Exception as exc:
                progress_bar.empty()
                st.error(f"❌ Search failed: {exc}")
                st.stop()

            progress_bar.progress(1.0, text="✅ Search complete!")

            # Pre-render result images before temp cleanup so they
            # survive in session_state after the temp dirs are deleted.
            cached_images: list[Image.Image | None] = []
            for match in result.results:
                cached_images.append(
                    _draw_bbox(match.photo_path, match.best_bbox)
                )

            # Persist for display after widget-triggered reruns
            st.session_state["search_result"] = result
            st.session_state["result_images"] = cached_images

            # Also export results.json as the spec requires
            export_results(result.results, result.stats)

        finally:
            # Always clean up temp directories
            _cleanup_temp_dir(selfie_tmp)
            _cleanup_temp_dir(dataset_tmp)

    # ── Display results ────────────────────────────────────────────────

    if "search_result" not in st.session_state:
        return

    result = st.session_state["search_result"]
    cached_images: list[Image.Image | None] = st.session_state.get(
        "result_images", []
    )

    st.divider()
    st.subheader(f"🎯 Results — {result.stats.matched_photos} match(es)")

    if not result.results:
        st.info("No matching photos found. Try lowering the similarity threshold.")
    else:
        for row_start in range(0, len(result.results), 3):
            row_items = result.results[row_start : row_start + 3]
            row_imgs = cached_images[row_start : row_start + 3]
            cols = st.columns(3)
            for col, match, img in zip(cols, row_items, row_imgs):
                with col:
                    if img is not None:
                        st.image(img, use_container_width=True)
                    else:
                        st.warning(
                            f"Could not load image: {Path(match.photo_path).name}"
                        )

                    file_name = Path(match.photo_path).name
                    st.markdown(
                        f"**Rank #{match.rank}** · Score: `{match.best_score:.4f}`\n\n"
                        f"📁 `{file_name}`"
                    )

    # ── Statistics ─────────────────────────────────────────────────────

    st.divider()
    st.subheader("📊 Statistics")
    s = result.stats
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Photos Scanned", s.total_photos_scanned)
    c2.metric("With Faces", s.photos_with_faces)
    c3.metric("Matched", s.matched_photos)
    c4.metric("Failed", s.failed_images)
    c5.metric("Time", f"{s.processing_time:.1f}s")


if __name__ == "__main__":
    main()
