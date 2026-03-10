"""Streamlit UI for the Face Photo Search System.

Run from the project root with::

    py -3.12 -m streamlit run app/ui.py

Workflow:
    1. Upload dataset folder → click **Prepare Dataset** (one-time).
    2. Upload selfie(s) → adjust threshold → click **Search** (fast, repeatable).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.config import DEFAULT_THRESHOLD, SLIDER_MIN, SLIDER_MAX, SLIDER_STEP
from core.dataset_index import PreparedDataset, prepare_dataset
from core.face_service import load_model
from core.reporter import export_results
from app.main import run_search_from_index


# ── Model caching ──────────────────────────────────────────────────────


@st.cache_resource(show_spinner="Loading face recognition model…")
def _get_model():
    """Load the InsightFace model once and cache across reruns."""
    return load_model()


# ── Helpers ────────────────────────────────────────────────────────────


def _save_uploads_to_dir(
    uploaded_files: list, dest_dir: Path
) -> tuple[list[Path], dict[str, str]]:
    """Persist Streamlit ``UploadedFile`` objects into *dest_dir*.

    All files are saved with safe ASCII names (``img_0000.jpg``, …) to
    avoid ``cv2.imread`` failures with non-ASCII characters on Windows.
    A mapping from each saved path back to the original upload name is
    returned for display purposes.
    """
    paths: list[Path] = []
    name_map: dict[str, str] = {}
    counter = 0
    for uf in uploaded_files:
        suffix = Path(uf.name).suffix
        safe_name = f"img_{counter:04d}{suffix}"
        counter += 1
        dest = dest_dir / safe_name
        dest.write_bytes(uf.getvalue())
        paths.append(dest)
        name_map[str(dest)] = uf.name
    return paths, name_map


def _draw_bbox_from_cache(
    pil_image: Image.Image, bbox: list[int]
) -> Image.Image:
    """Draw a bounding box on an already-loaded PIL image.

    Returns a *copy* so the cached original is not mutated.
    """
    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
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


def _invalidate_dataset() -> None:
    """Remove all dataset-related state so the UI resets cleanly."""
    for key in (
        "prepared_dataset",
        "search_result",
        "result_images",
    ):
        st.session_state.pop(key, None)


# ── Page layout ────────────────────────────────────────────────────────


def main() -> None:
    """Render the Streamlit application."""

    st.set_page_config(
        page_title="Face Photo Search",
        page_icon="📷",
        layout="wide",
    )

    # CSS: hide individual file names in the dataset uploader only
    st.markdown(
        """
        <style>
        .st-key-dataset_upload_section [data-testid="stFileUploaderFileList"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📷 Face Photo Search")
    st.caption(
        "Upload a dataset folder and prepare it once, then search "
        "repeatedly with different selfies or thresholds."
    )

    # State flags
    dataset_ready: bool = "prepared_dataset" in st.session_state
    is_preparing: bool = st.session_state.get("is_preparing", False)

    # ── Sidebar ────────────────────────────────────────────────────────

    with st.sidebar:
        st.header("🔍 Search Settings")

        # ── 1. Selfie upload ──────────────────────────────────────────
        uploaded_selfies = st.file_uploader(
            "Upload Selfie Images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload clear selfie photos of the person to search for.",
            disabled=is_preparing,
        )

        st.divider()

        # ── 2. Dataset upload + Prepare / Cancel ──────────────────────
        if "dataset_uploader_key" not in st.session_state:
            st.session_state["dataset_uploader_key"] = 0

        with st.container(key="dataset_upload_section"):
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
                disabled=is_preparing,
            )

        if uploaded_dataset:
            st.caption(f"📁 {len(uploaded_dataset)} photo(s) uploaded")
        elif is_preparing:
            st.caption("⏳ Preparing dataset…")

        # Prepare / Cancel buttons side-by-side
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            prepare_clicked = st.button(
                "⚙️ Prepare",
                use_container_width=True,
                disabled=is_preparing or not uploaded_dataset or dataset_ready,
                help=(
                    "Preprocess the dataset (detect faces & extract embeddings). "
                    "Required once before searching."
                ),
            )
        with btn_col2:
            if is_preparing:
                # Cancel is NEVER disabled — guarantees the user can always escape
                cancel_clicked = st.button(
                    "❌ Cancel",
                    key="cancel_prepare_btn",
                    use_container_width=True,
                    type="primary",
                )
                clear_clicked = False
            else:
                cancel_clicked = False
                clear_clicked = st.button(
                    "🗑️ Clear",
                    key="clear_dataset_btn",
                    use_container_width=True,
                    disabled=not uploaded_dataset and not dataset_ready,
                )

        if dataset_ready:
            prep: PreparedDataset = st.session_state["prepared_dataset"]
            st.success(
                f"✅ Dataset ready — {prep.total_photos} photos, "
                f"{len(prep.candidate_faces)} faces "
                f"({prep.preparation_time:.1f}s)",
                icon="✅",
            )

        st.divider()

        # ── 3. Threshold + Search ─────────────────────────────────────
        threshold = st.slider(
            "Similarity Threshold",
            min_value=SLIDER_MIN,
            max_value=SLIDER_MAX,
            value=DEFAULT_THRESHOLD,
            step=SLIDER_STEP,
            help="Lower values return more results but may include false matches.",
            disabled=is_preparing,
        )

        search_clicked = st.button(
            "🔍 Search",
            type="primary",
            use_container_width=True,
            disabled=is_preparing or not dataset_ready,
        )

        if not dataset_ready and uploaded_dataset and not is_preparing:
            st.info("👆 Click **Prepare** to preprocess the dataset before searching.")

    # ── Handle Prepare request (phase 1: set flag → rerun) ─────────────

    if prepare_clicked:
        st.session_state["is_preparing"] = True
        _invalidate_dataset()
        st.rerun()

    # ── Handle Cancel ──────────────────────────────────────────────────

    if cancel_clicked:
        st.session_state.pop("is_preparing", None)
        st.rerun()

    # ── Handle Clear ───────────────────────────────────────────────────

    if clear_clicked:
        st.session_state["dataset_uploader_key"] += 1
        _invalidate_dataset()
        st.rerun()

    # ── Query face preview ─────────────────────────────────────────────

    if uploaded_selfies and not is_preparing:
        st.subheader("📸 Query Faces")
        preview_cols = st.columns(min(len(uploaded_selfies), 5))
        for idx, selfie_file in enumerate(uploaded_selfies):
            with preview_cols[idx % len(preview_cols)]:
                pil_img = Image.open(selfie_file)
                st.image(pil_img, caption=selfie_file.name, width="stretch")

    # ── Prepare Dataset execution (phase 2: run after rerun) ───────────

    if is_preparing and not dataset_ready:
        if not uploaded_dataset:
            st.warning("⚠️ No dataset files available. Please re-upload.")
            st.session_state.pop("is_preparing", None)
            st.rerun()

        dataset_tmp: Path | None = None
        try:
            model = _get_model()

            dataset_tmp = Path(tempfile.mkdtemp(prefix="fps_dataset_"))
            dataset_paths, name_map = _save_uploads_to_dir(
                uploaded_dataset, dataset_tmp
            )

            if not dataset_paths:
                raise ValueError("The uploaded folder contains no valid images.")

            progress = st.progress(0, text="Preparing dataset…")

            def _on_prep_progress(current: int, total: int) -> None:
                progress.progress(
                    current / total,
                    text=f"Detecting faces… {current}/{total} images",
                )

            prepared = prepare_dataset(
                model=model,
                dataset_dir=dataset_tmp,
                name_map=name_map,
                on_progress=_on_prep_progress,
            )

            progress.progress(1.0, text="✅ Dataset prepared!")
            st.session_state["prepared_dataset"] = prepared

        except ValueError as ve:
            st.warning(f"⚠️ {ve}")
        except Exception as exc:
            st.error(f"❌ Dataset preparation failed: {exc}")
        finally:
            _cleanup_temp_dir(dataset_tmp)
            st.session_state.pop("is_preparing", None)
            st.rerun()

    # ── Search execution ───────────────────────────────────────────────

    if search_clicked:
        st.session_state.pop("search_result", None)
        st.session_state.pop("result_images", None)

        if not uploaded_selfies:
            st.error("❌ Please upload at least one selfie image.")
            st.stop()

        prepared = st.session_state["prepared_dataset"]

        selfie_tmp: Path | None = None
        try:
            model = _get_model()

            selfie_tmp = Path(tempfile.mkdtemp(prefix="fps_selfies_"))
            selfie_paths, _ = _save_uploads_to_dir(uploaded_selfies, selfie_tmp)

            progress = st.progress(0, text="Searching…")

            result = run_search_from_index(
                model=model,
                selfie_paths=selfie_paths,
                prepared=prepared,
                threshold=threshold,
            )

            progress.progress(1.0, text="✅ Search complete!")

            # Render result images from the prepared image cache
            cached_images: list[Image.Image | None] = []
            for match in result.results:
                src_img = prepared.image_cache.get(match.photo_path)
                if src_img is not None:
                    cached_images.append(
                        _draw_bbox_from_cache(src_img, match.best_bbox)
                    )
                else:
                    cached_images.append(None)

            st.session_state["search_result"] = result
            st.session_state["result_images"] = cached_images

            export_results(result.results, result.stats)

        except ValueError as exc:
            st.warning(f"⚠️ {exc}")
        except Exception as exc:
            st.error(f"❌ Search failed: {exc}")
        finally:
            _cleanup_temp_dir(selfie_tmp)

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
        name_map = (
            st.session_state.get("prepared_dataset").name_map
            if "prepared_dataset" in st.session_state
            else {}
        )
        for row_start in range(0, len(result.results), 3):
            row_items = result.results[row_start : row_start + 3]
            row_imgs = cached_images[row_start : row_start + 3]
            cols = st.columns(3)
            for col, match, img in zip(cols, row_items, row_imgs):
                with col:
                    if img is not None:
                        st.image(img, width="stretch")
                    else:
                        st.warning(
                            f"Could not load image: {Path(match.photo_path).name}"
                        )

                    original = name_map.get(match.photo_path, "")
                    file_name = (
                        Path(original).name
                        if original
                        else Path(match.photo_path).name
                    )
                    st.markdown(
                        f"**Rank #{match.rank}** · Score: `{match.best_score:.4f}`\n\n"
                        f"📁 `{file_name}`"
                    )

    # ── Statistics ─────────────────────────────────────────────────────

    st.divider()
    st.subheader("📊 Statistics")
    s = result.stats
    prep_time: float = 0.0
    if "prepared_dataset" in st.session_state:
        prep_time = st.session_state["prepared_dataset"].preparation_time
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Photos Scanned", s.total_photos_scanned)
    c2.metric("With Faces", s.photos_with_faces)
    c3.metric("Matched", s.matched_photos)
    c4.metric("Failed", s.failed_images)
    c5.metric("Prepare", f"{prep_time:.1f}s")
    c6.metric("Search", f"{s.processing_time:.1f}s")


if __name__ == "__main__":
    main()
