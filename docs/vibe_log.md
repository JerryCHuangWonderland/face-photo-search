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

This optimization is documented for future implementation but not required for the MVP demo.

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
