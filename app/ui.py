"""Streamlit UI for the Face Photo Search System.

Run from the project root with::

    py -3.12 -m streamlit run app/ui.py

Workflow:
    1. Select a saved dataset or upload a new dataset folder.
    2. Enter a dataset name and click **Prepare** to save a reusable index.
    3. Upload selfie(s) → adjust threshold → click **Search**.
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

from core.config import (
    DATASET_STORAGE_DIR,
    DEFAULT_THRESHOLD,
    SLIDER_MAX,
    SLIDER_MIN,
    SLIDER_STEP,
)
from core.dataset_index import (
    DatasetPhotoInfo,
    DatasetSummary,
    PreparedDataset,
    delete_saved_dataset,
    list_dataset_photos,
    list_saved_datasets,
    load_prepared_dataset,
    prepare_dataset,
    rename_saved_dataset,
    save_prepared_dataset,
    validate_dataset_name,
)
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


def _clear_search_state() -> None:
    """Clear the current search output while preserving the active dataset."""
    for key in ("search_result", "result_images"):
        st.session_state.pop(key, None)


def _invalidate_dataset() -> None:
    """Remove all dataset-related state so the UI resets cleanly."""
    for key in ("prepared_dataset", "loaded_dataset_name"):
        st.session_state.pop(key, None)
    _clear_search_state()


def _queue_notice(level: str, message: str) -> None:
    """Store a sidebar notice to show after a rerun."""
    st.session_state["dataset_notice"] = {
        "level": level,
        "message": message,
    }


def _queue_dataset_selection(dataset_name: str) -> None:
    """Defer dataset selector updates until the next rerun."""
    st.session_state["pending_selected_dataset_name"] = dataset_name


def _queue_new_dataset_name(value: str) -> None:
    """Defer new dataset name input updates until the next rerun."""
    st.session_state["pending_new_dataset_name"] = value


def _sync_dataset_manager_state(dataset_name: str) -> None:
    """Keep dataset manager widget state aligned with the active dataset."""
    current_target = st.session_state.get("dataset_manager_target", "")
    if dataset_name and current_target != dataset_name:
        st.session_state["dataset_manager_target"] = dataset_name
        st.session_state["rename_dataset_name"] = dataset_name
        st.session_state["dataset_photo_filter"] = ""
    elif not dataset_name:
        st.session_state.pop("dataset_manager_target", None)


def _format_saved_dataset(
    dataset_name: str,
    summary_map: dict[str, DatasetSummary],
) -> str:
    """Render a human-friendly label for the saved dataset selector."""
    if not dataset_name:
        return "Select saved dataset"

    summary = summary_map[dataset_name]
    return (
        f"{summary.name} · {summary.total_photos} photos · "
        f"{summary.candidate_faces} faces · {summary.preparation_time:.1f}s"
    )


def _render_match_image(
    prepared: PreparedDataset,
    photo_path: str,
    bbox: list[int],
) -> Image.Image | None:
    """Render a result image from cache or by loading the stored dataset photo."""
    src_img = _load_dataset_image(prepared, photo_path)
    if src_img is None:
        return None

    return _draw_bbox_from_cache(src_img, bbox)


def _load_dataset_image(
    prepared: PreparedDataset,
    photo_path: str,
) -> Image.Image | None:
    """Load a stored dataset image into the in-memory cache on demand."""
    src_img = prepared.image_cache.get(photo_path)
    if src_img is None:
        photo = Path(photo_path)
        if not photo.exists():
            return None
        with Image.open(photo) as pil_img:
            src_img = pil_img.convert("RGB")
        prepared.image_cache[photo_path] = src_img

    return src_img


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
        "Reuse saved dataset indexes or create a new one from an uploaded "
        "folder, then search repeatedly with different selfies or thresholds."
    )

    saved_datasets = list_saved_datasets()
    summary_map = {summary.name: summary for summary in saved_datasets}

    pending_selected_dataset_name = st.session_state.pop(
        "pending_selected_dataset_name", None
    )
    if pending_selected_dataset_name is not None:
        st.session_state["selected_dataset_name"] = pending_selected_dataset_name

    pending_new_dataset_name = st.session_state.pop(
        "pending_new_dataset_name", None
    )
    if pending_new_dataset_name is not None:
        st.session_state["new_dataset_name"] = pending_new_dataset_name

    if "selected_dataset_name" not in st.session_state:
        st.session_state["selected_dataset_name"] = ""
    if st.session_state["selected_dataset_name"] not in {"", *summary_map}:
        st.session_state["selected_dataset_name"] = ""

    is_preparing: bool = st.session_state.get("is_preparing", False)
    if not is_preparing:
        selected_dataset_name = st.session_state.get("selected_dataset_name", "")
        loaded_dataset_name = st.session_state.get("loaded_dataset_name", "")

        if selected_dataset_name and selected_dataset_name != loaded_dataset_name:
            try:
                st.session_state["prepared_dataset"] = load_prepared_dataset(
                    selected_dataset_name
                )
                st.session_state["loaded_dataset_name"] = selected_dataset_name
                _clear_search_state()
            except Exception as exc:
                st.session_state["selected_dataset_name"] = ""
                _invalidate_dataset()
                _queue_notice(
                    "error",
                    f"Failed to load dataset '{selected_dataset_name}': {exc}",
                )
        elif not selected_dataset_name and loaded_dataset_name:
            _invalidate_dataset()

    _sync_dataset_manager_state(st.session_state.get("selected_dataset_name", ""))

    dataset_ready: bool = "prepared_dataset" in st.session_state
    rename_clicked = False
    delete_clicked = False
    active_dataset_name = st.session_state.get("selected_dataset_name", "")
    active_summary = summary_map.get(active_dataset_name)

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

        dataset_name_input = st.text_input(
            "New Dataset Name",
            key="new_dataset_name",
            help=(
                "Used as the reusable dataset index folder name under "
                f"{DATASET_STORAGE_DIR}."
            ),
            placeholder="e.g. company_party_2026",
            disabled=is_preparing,
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            prepare_clicked = st.button(
                "⚙️ Prepare",
                use_container_width=True,
                disabled=(
                    is_preparing
                    or not uploaded_dataset
                    or not dataset_name_input.strip()
                ),
                help=(
                    "Create a reusable dataset index from the uploaded folder "
                    "and save it for future searches."
                ),
            )
        with btn_col2:
            if is_preparing:
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

        st.selectbox(
            "Saved Dataset",
            options=[""] + [summary.name for summary in saved_datasets],
            key="selected_dataset_name",
            format_func=lambda name: _format_saved_dataset(name, summary_map),
            disabled=is_preparing,
        )

        st.caption(f"💾 Saved dataset indexes are stored in {DATASET_STORAGE_DIR}")

        active_dataset_name = st.session_state.get("selected_dataset_name", "")
        active_summary = summary_map.get(active_dataset_name)

        if dataset_name_input.strip() and dataset_name_input.strip() in summary_map:
            st.caption("⚠️ This dataset name already exists. Choose a different name.")

        if dataset_ready:
            prep: PreparedDataset = st.session_state["prepared_dataset"]
            st.success(
                f"✅ Dataset ready — {prep.dataset_name or 'Current dataset'} · "
                f"{prep.total_photos} photos, {len(prep.candidate_faces)} faces "
                f"({prep.preparation_time:.1f}s)",
                icon="✅",
            )
            if prep.dataset_name in summary_map:
                st.caption(f"Created: {summary_map[prep.dataset_name].created_at}")

        if active_summary is not None:
            with st.expander("🗂️ Manage Saved Dataset", expanded=False):
                st.caption(
                    f"Selected: {active_summary.name} · {active_summary.total_photos} photos"
                )
                st.text_input(
                    "Rename Selected Dataset",
                    key="rename_dataset_name",
                    disabled=is_preparing,
                )
                delete_confirmed = st.checkbox(
                    "I understand this will permanently delete the saved dataset files.",
                    key=f"confirm_delete_{active_dataset_name}",
                    disabled=is_preparing,
                )
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    rename_clicked = st.button(
                        "✏️ Rename",
                        key="rename_dataset_btn",
                        use_container_width=True,
                        disabled=is_preparing
                        or not st.session_state.get("rename_dataset_name", "").strip(),
                    )
                with action_col2:
                    delete_clicked = st.button(
                        "🗑️ Delete",
                        key="delete_dataset_btn",
                        use_container_width=True,
                        disabled=is_preparing or not delete_confirmed,
                    )

        notice = st.session_state.pop("dataset_notice", None)
        if notice is not None:
            getattr(st, notice["level"])(notice["message"])

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

        if not dataset_ready and not is_preparing:
            st.info(
                "👆 Select a saved dataset, or upload a folder, enter a name, "
                "and click **Prepare**."
            )

    # ── Handle Prepare request (phase 1: set flag → rerun) ─────────────

    if prepare_clicked:
        try:
            pending_dataset_name = validate_dataset_name(dataset_name_input)
        except ValueError as exc:
            st.error(f"❌ {exc}")
        else:
            if pending_dataset_name in summary_map:
                st.error(
                    f"❌ Dataset '{pending_dataset_name}' already exists. "
                    "Please choose another name."
                )
            else:
                st.session_state["is_preparing"] = True
                st.session_state["pending_dataset_name"] = pending_dataset_name
                st.rerun()

    # ── Handle Cancel ──────────────────────────────────────────────────

    if cancel_clicked:
        st.session_state.pop("is_preparing", None)
        st.session_state.pop("pending_dataset_name", None)
        st.rerun()

    # ── Handle Clear ───────────────────────────────────────────────────

    if clear_clicked:
        st.session_state["dataset_uploader_key"] += 1
        _queue_dataset_selection("")
        st.session_state.pop("pending_dataset_name", None)
        _invalidate_dataset()
        st.rerun()

    if rename_clicked and active_dataset_name:
        try:
            updated_name = validate_dataset_name(
                st.session_state.get("rename_dataset_name", "")
            )
            if updated_name == active_dataset_name:
                _queue_notice("info", "Dataset name is unchanged.")
            else:
                rename_saved_dataset(active_dataset_name, updated_name)
                _queue_dataset_selection(updated_name)
                _invalidate_dataset()
                _queue_notice(
                    "success",
                    f"Dataset '{active_dataset_name}' was renamed to '{updated_name}'.",
                )
        except ValueError as exc:
            _queue_notice("error", f"❌ {exc}")
        except FileExistsError as exc:
            _queue_notice("error", f"❌ {exc}")
        except FileNotFoundError as exc:
            _queue_notice("error", f"❌ {exc}")
        st.rerun()

    if delete_clicked and active_dataset_name:
        try:
            delete_saved_dataset(active_dataset_name)
            _queue_dataset_selection("")
            _invalidate_dataset()
            _queue_notice(
                "success",
                f"Dataset '{active_dataset_name}' was deleted.",
            )
        except FileNotFoundError as exc:
            _queue_notice("error", f"❌ {exc}")
        st.rerun()

    # ── Query face preview ─────────────────────────────────────────────

    if uploaded_selfies and not is_preparing:
        st.subheader("📸 Query Faces")
        preview_cols = st.columns(min(len(uploaded_selfies), 5))
        for idx, selfie_file in enumerate(uploaded_selfies):
            with preview_cols[idx % len(preview_cols)]:
                pil_img = Image.open(selfie_file)
                st.image(pil_img, caption=selfie_file.name, width="stretch")

    if dataset_ready and not is_preparing:
        prepared = st.session_state["prepared_dataset"]
        try:
            dataset_photos = list_dataset_photos(prepared.dataset_name)
        except FileNotFoundError:
            dataset_photos = []

        st.divider()
        with st.expander("🖼️ Dataset Photos", expanded=False):
            st.caption(
                "Browse the original photos stored with the selected dataset index."
            )
            photo_filter = st.text_input(
                "Filter Photos",
                key="dataset_photo_filter",
                placeholder="Search by file name or folder",
            ).strip()
            preview_limit = st.select_slider(
                "Preview Count",
                options=[12, 24, 48, 96],
                value=24,
                key="dataset_preview_limit",
            )

            filtered_photos = [
                photo
                for photo in dataset_photos
                if not photo_filter
                or photo_filter.lower() in photo.display_name.lower()
            ]

            st.caption(
                f"Showing {min(len(filtered_photos), preview_limit)} of {len(filtered_photos)} photo(s)"
            )

            if not filtered_photos:
                st.info("No photos match the current filter.")
            else:
                preview_photos = filtered_photos[:preview_limit]
                preview_cols = st.columns(4)
                for idx, photo in enumerate(preview_photos):
                    with preview_cols[idx % len(preview_cols)]:
                        image = _load_dataset_image(prepared, photo.path)
                        if image is not None:
                            st.image(image, width="stretch")
                        else:
                            st.warning("Could not load this photo.")
                        st.caption(photo.display_name)

    # ── Prepare Dataset execution (phase 2: run after rerun) ───────────

    if is_preparing:
        pending_dataset_name = st.session_state.get("pending_dataset_name", "")
        if not pending_dataset_name:
            _queue_notice("warning", "No dataset name was provided. Please try again.")
            st.session_state.pop("is_preparing", None)
            st.rerun()

        if not uploaded_dataset:
            _queue_notice("warning", "No dataset files are available. Please re-upload.")
            st.session_state.pop("is_preparing", None)
            st.session_state.pop("pending_dataset_name", None)
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

            save_prepared_dataset(
                prepared=prepared,
                dataset_name=pending_dataset_name,
                source_dir=dataset_tmp,
            )

            progress.progress(1.0, text="✅ Dataset prepared and saved!")
            _queue_dataset_selection(pending_dataset_name)
            _queue_new_dataset_name("")
            _invalidate_dataset()
            _clear_search_state()
            _queue_notice(
                "success",
                f"Dataset '{pending_dataset_name}' was saved for reuse.",
            )

        except ValueError as ve:
            _queue_notice("warning", f"⚠️ {ve}")
        except FileExistsError as exc:
            _queue_notice("error", f"❌ {exc}")
        except Exception as exc:
            _queue_notice("error", f"❌ Dataset preparation failed: {exc}")
        finally:
            _cleanup_temp_dir(dataset_tmp)
            st.session_state.pop("is_preparing", None)
            st.session_state.pop("pending_dataset_name", None)
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
                cached_images.append(
                    _render_match_image(
                        prepared=prepared,
                        photo_path=match.photo_path,
                        bbox=match.best_bbox,
                    )
                )

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
                    file_name = original or Path(match.photo_path).name
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
