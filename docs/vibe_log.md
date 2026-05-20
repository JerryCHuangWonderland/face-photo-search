# Vibe Coding Log

This document records the development process of the **Face Photo Search System** and documents how AI tools were used during the development lifecycle.

The goal of this log is to demonstrate:

- Prompt engineering strategies
- AI collaboration workflow
- Iterative development
- Problem solving and adjustments

---

# Project Information

Project Name: Face Photo Search System

Goal:
Build a system that can search a large collection of photos to find images containing a specific person based on selfie input.

Core Technologies:

- Python
- InsightFace (buffalo_l)
- Streamlit
- Cosine Similarity

AI Tools Used:

- Claude / ChatGPT / Copilot

---

# Development Timeline

## Iteration 1 — Spec Design

Goal:
Design system specification (spec.md).

Outcome:
Created initial specification including architecture, workflow, and development phases.

Key Decisions:

- Use InsightFace buffalo_l
- Use cosine similarity
- Use Streamlit for UI

---

## Iteration 2 — Spec Improvement

Goal:
Improve spec based on AI review.

Outcome:
Added:

- API interface definitions
- Default threshold configuration
- InsightFace initialization instructions
- Requirements version locking

---

## Iteration 3 — Core Pipeline Implementation

Goal:
Implement Phase 1 core modules.

Outcome:
Implemented the main modules described in the specification:

- face_service.py
- file_scanner.py
- query_builder.py
- matcher.py
- result_aggregator.py
- reporter.py
- main.py

The CLI pipeline was able to run end-to-end and produce `results.json`.

---

## Iteration 4 — Phase 1 Validation and Review

Date:
2026-03-09

Goal:
Validate the Phase 1 core pipeline implementation and verify basic face matching functionality.

Test Setup:

Selfie input:

- 1 selfie image

Dataset:

- 8 group photos

Ground truth:

- The target person appears in 5 photos

Test Results:

Threshold = 0.45  
Detected matches: 4 / 5

Threshold = 0.40  
Detected matches: 5 / 5

Observation:

The pipeline executed successfully:

- InsightFace model loaded correctly
- Faces were detected
- Embeddings were generated
- Cosine similarity matching worked
- results.json was generated

The missed match at threshold 0.45 appeared to be a borderline similarity case rather than a logic error.

AI Review:

Claude reviewed the implementation and confirmed:

- matcher.py logic is correct
- query_builder.py face selection logic is acceptable
- cosine similarity implementation is correct
- pipeline architecture matches the specification

Decision:

- Keep the default threshold at 0.45
- Allow threshold adjustment via UI

---

## Iteration 5 — Streamlit UI Implementation

Goal:
Build a web interface for interactive search.

Features implemented:

- Multiple selfie upload
- Dataset upload
- Threshold slider
- Search button
- Results grid display
- Bounding box drawing
- Similarity score display
- Statistics panel

The UI reused the existing pipeline from `app/main.py` to avoid duplicating business logic.

---

## Iteration 6 — UI Improvements and Dataset Folder Upload

Goal:
Improve usability and prepare the system for demo scenarios.

Changes:

- Replaced manual dataset path input with **dataset folder upload**
- Implemented Streamlit directory upload using  
  `st.file_uploader(..., accept_multiple_files="directory")`
- Preserved subfolder structure when saving uploaded files
- Added safe cleanup of temporary directories using `try/finally`
- Cached rendered result images in `session_state` so the UI can display results after temp files are deleted
- Added validation warnings when no valid images are found in the uploaded dataset

Outcome:

The UI now allows users to:

1. Upload selfie images
2. Upload an entire dataset folder from the browser
3. Adjust similarity threshold
4. Run the search interactively
5. View matched photos with bounding boxes and similarity scores

This version is considered the **MVP demo-ready implementation**.

---

## Iteration 7 — Embedding Cache and Search Optimization Design

Goal:
Design a strategy to improve search performance for larger datasets.

Problem:

The current pipeline recomputes face embeddings for every photo during each search run.  
For large datasets (hundreds or thousands of images), this increases processing time.

Design Idea:

Introduce an **embedding cache / index layer**.

Proposed workflow:

Dataset preparation phase:

1. Scan dataset images
2. Detect faces
3. Extract embeddings
4. Save embeddings to an index file (e.g. JSON / NumPy / FAISS)

Search phase:

1. Compute embedding for selfie query
2. Load precomputed dataset embeddings
3. Perform cosine similarity search against stored vectors
4. Return matched photos

Expected Benefits:

- Significant speed improvement for repeated searches
- Avoid repeated face detection on unchanged datasets
- Enable scaling to thousands of photos

Future Implementation Options:

- NumPy embedding matrix
- FAISS vector index
- Persistent cache file in `outputs/embeddings_index`

Status:

Implemented in Iteration 8.

---

## Iteration 8 — Dataset Preprocessing and Indexed Search Implementation

Goal:
Implement the dataset preprocessing and indexed search workflow
that was previously proposed in Iteration 7.

Problem:
The original pipeline recomputed face detection and embeddings
for the entire dataset during every search run.

In testing:

- Dataset size: 348 photos
- Total search time: ~1607 seconds

Most processing time was spent on:

- loading images
- face detection
- embedding extraction

This made repeated searches slow and impractical.

Implementation:

A two-stage workflow was introduced:

1. **Prepare Dataset**
2. **Search**

Dataset Preparation:

- scan dataset images
- detect faces
- extract embeddings
- build a reusable dataset index
- cache candidate face embeddings in memory

Search Stage:

- process selfie images
- generate query embeddings
- compare against cached dataset embeddings
- aggregate results

UI Improvements:

- Added **Prepare Dataset** button
- Added **Cancel** option during dataset preparation
- Disabled Search until dataset is prepared
- Disabled UI controls during preparation/search
- Added dataset-ready indicator in sidebar

Technical Changes:

- Introduced `PreparedDataset` structure
- Implemented `prepare_dataset()` preprocessing pipeline
- Added `run_search_from_index()` search function
- Cached dataset images for result rendering
- Invalidated dataset cache when dataset changes

Result:

Dataset preprocessing now runs **only once per dataset upload**.

Subsequent searches reuse the cached embeddings and complete
significantly faster.

This architecture improves usability for repeated searches and
enables scaling to larger datasets.

### Performance Comparison

A performance comparison was conducted before and after introducing
dataset preprocessing and indexed search.

Initial implementation (no dataset index):

- Dataset size: 348 photos
- Total processing time: **1607 seconds**
- Each search recomputed:
  - image loading
  - face detection
  - embedding extraction

Indexed implementation (Prepare Dataset + Search):

- Dataset preprocessing runs **once per dataset upload**
- Subsequent searches reuse the cached embeddings

Expected behavior after indexing:

Prepare Dataset (one-time):

- scan dataset
- detect faces
- extract embeddings
- build dataset index

Search:

- process selfie images
- compare query embeddings with cached dataset embeddings

This change shifts the complexity from:

O(N × detection + embedding) per search

to:

O(N × detection + embedding) once

- O(Q × similarity search)

Where:

- N = dataset size
- Q = number of user searches

This significantly improves responsiveness when performing
multiple searches on the same dataset.

---

## Iteration 9 — Persistent Saved Datasets and One-Click Launch

Goal:
Make prepared dataset indexes reusable across reruns and sessions,
and reduce launch friction for local demos.

Problem:
The two-stage workflow introduced in Iteration 8 only kept the
prepared dataset in Streamlit session state.

This meant:

- the prepared index was lost after rerun / restart
- users had to re-upload and re-prepare the same dataset
- there was no way to switch between previously prepared datasets
- launching the UI still required manually activating the virtual environment

Implementation:

- Added persisted dataset storage under `data/dataset/<dataset_name>`
- Stored dataset metadata, preparation time, and embedding matrix on disk
- Copied uploaded dataset photos into the saved dataset folder so result images can be rendered later
- Added saved dataset summaries for sidebar selection
- Replaced the old Prepare action with:
  1. enter dataset name
  2. prepare dataset
  3. save reusable index
- Added a Saved Dataset dropdown next to the Prepare controls
- Loaded saved datasets back into `PreparedDataset` for indexed search reuse
- Switched result rendering to load saved images from disk on demand when they are not already cached in memory
- Added `run_app.bat` to launch Streamlit directly with the project's `.venv`

Result:

Prepared datasets can now be reused without rebuilding the index each time.

Users can:

- select an existing dataset from the sidebar
- create a new named dataset index
- keep using saved dataset preparation times as part of the UI feedback
- launch the demo without manually activating the environment

---

# Issues and Lessons Learned

## Face Detection Limitations

Small faces in group photos may not be detected reliably.

Mitigation:
Allow multiple selfie inputs to improve matching robustness.

---

## Threshold Sensitivity

Similarity threshold significantly affects recall vs precision.

Solution:
Provide an adjustable threshold slider in the UI.

---

# Future Improvements

Potential extensions:

- FAISS vector search
- Pre-computed embedding index
- GPU acceleration
- Annotated image export
- Large dataset indexing

---

# Demo Preparation Checklist

Before demo day:

- Prepare selfie examples
- Prepare dataset photos
- Verify model loading
- Verify UI workflow
- Verify JSON output
