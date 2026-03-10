# Face Photo Search System

## 1. Project Overview

### 1.1 Objective

This project implements a system that can search for photos containing a
specific person from a large collection of images using facial
recognition.

Users provide one or more selfie images as query inputs. The system
extracts facial embeddings from these selfies and compares them against
faces detected in a photo dataset.

The system returns photos that likely contain the same person.

### 1.2 Key Capabilities

The system should be able to: - Accept one or multiple selfie images -
Scan a folder containing many photos - Detect faces in all images -
Extract facial embeddings - Perform similarity search - Identify photos
containing the target person - Display matched faces and similarity
scores

### 1.3 Target Use Case

Typical scenario:

A user has hundreds or thousands of event photos and wants to quickly
find photos that contain a specific person.

---

# 2. Input Definition

## 2.1 Query Input (Selfies)

Supported formats:

- jpg
- jpeg
- png

Rules:

- Each selfie should contain at least one clear face
- If multiple faces are detected:
  - Select the largest face closest to the center
- If no face is detected:
  - Return an error and skip the image

---

## 2.2 Search Dataset

The search dataset is a folder containing photos.

Rules:

- Scan folder recursively
- Supported formats: jpg, jpeg, png
- Invalid or unreadable files are skipped
- Photos without detectable faces are ignored

---

## 2.3 Dataset Size Assumption

MVP target dataset size:

100 -- 3000 photos

Typical sources:

- event photos
- group photos
- personal photo collections

---

# 3. Output Definition

## 3.1 Search Results

Each result contains:

- photo_path
- preview_image
- matched_face_bbox
- similarity_score
- rank

Results are sorted by descending similarity score.

---

## 3.2 No Result Case

If no photo meets the similarity threshold:

    No matching photos found

---

## 3.3 JSON Output

Results are saved to:

    outputs/results.json

Example:

```json
{
  "photo_path": "photos/event/a.jpg",
  "best_bbox": [120, 80, 200, 160],
  "best_score": 0.61,
  "matched_query_index": 0,
  "rank": 1
}
```

---

## 3.4 Statistics

System displays:

- total_photos_scanned
- photos_with_faces
- matched_photos
- failed_images
- processing_time

---

# 4. Query Strategy

Supports **single or multiple selfies**.

### Matching Strategy

1.  Extract embeddings from each selfie
2.  Detect faces in dataset photos
3.  Compare embeddings using cosine similarity
4.  Record matches above threshold

### Aggregation Rule

If multiple matches occur for the same photo:

- Photo appears once
- Final score = highest similarity
- Use the bounding box corresponding to that score

---

# 5. System Workflow

## User Workflow

1.  Launch application
2.  Upload selfie images
3.  Select dataset folder
4.  Adjust similarity threshold
5.  Click **Search**
6.  View matched results

---

## System Processing Flow

    Selfies
     ↓
    Face Detection
     ↓
    Embedding Extraction
     ↓
    Scan Dataset Photos
     ↓
    Detect Faces
     ↓
    Extract Embeddings
     ↓
    Cosine Similarity
     ↓
    Match Results
     ↓
    Aggregate Results
     ↓
    Display UI

---

# 6. Technology Stack

## Programming Language

Python 3.10+

---

## Core Libraries

- insightface
- opencv-python
- numpy
- pillow
- streamlit
- tqdm

---

## Face Recognition Model

The system uses **InsightFace**.

Model:

    buffalo_l

Each face produces a **512‑dimension embedding vector**.

---

## Similarity Metric

Cosine similarity.

Future optimization may include:

- FAISS vector search

---

## Hardware

MVP runs on:

CPU (GPU optional)

---

# 7. System Architecture

Modules:

### config

Stores configuration values.

### file_scanner

Scans dataset folders and collects valid image paths.

### face_service

Initializes InsightFace, detects faces, extracts embeddings.

### query_builder

Processes selfies and generates query embeddings.

### matcher

Computes similarity between query and candidate embeddings.

### result_aggregator

Merges duplicate photo results and selects highest similarity.

### reporter

Exports JSON output and statistics.

### ui

Streamlit user interface.

### main

Orchestrates the pipeline.

---

# 8. Project Structure

    face-photo-search/
    │
    ├─ app/
    │  ├─ main.py
    │  └─ ui.py
    │
    ├─ core/
    │  ├─ config.py
    │  ├─ file_scanner.py
    │  ├─ face_service.py
    │  ├─ query_builder.py
    │  ├─ matcher.py
    │  ├─ result_aggregator.py
    │  └─ reporter.py
    │
    ├─ data/
    │  ├─ demo_selfies/
    │  └─ demo_photos/
    │
    ├─ outputs/
    │  └─ results.json
    │
    ├─ requirements.txt
    │
    └─ spec.md

---

# 9. Development Milestones

### Phase 1 --- Core Pipeline

Implement:

- face detection
- embedding extraction
- similarity computation

### Phase 2 --- Result Aggregation

- ranking
- JSON output
- statistics

### Phase 3 --- Streamlit UI

- selfie upload
- threshold slider
- result display

### Phase 4 --- Demo Improvements

- bounding box drawing
- UI improvements

---

# 10. Known Limitations

- Small faces in group photos may not be detected
- Pose variation affects similarity
- Similar-looking people may cause false positives
- Threshold tuning may be necessary
- CPU processing limits large datasets

---

# 11. Demo Plan

Demo dataset:

- 3--5 selfies
- 100--300 photos

Demo steps:

1.  Upload selfie
2.  Select dataset folder
3.  Adjust threshold
4.  Run search
5.  Show matched results

---

# Appendix A --- API Interfaces

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class CandidateFace:
    photo_path: str
    bbox: list[int]
    embedding: np.ndarray

@dataclass
class MatchResult:
    photo_path: str
    best_bbox: list[int]
    best_score: float
    matched_query_index: int
    rank: int
```

Example function signatures:

```python
def load_model(model_name: str = "buffalo_l"):
    ...

def detect_faces(image):
    ...

def extract_embedding(face):
    ...

def compute_similarity(query_embedding, candidate_embedding):
    ...

def find_matches(query_embeddings, candidate_faces, threshold):
    ...
```

---

# Appendix B --- Default Configuration

For the current demo dataset, 0.40 produced better recall than 0.45.
Recommended default threshold:

    0.45

UI Slider Range:

    0.2 – 0.8
    step = 0.05

This range matches common cosine similarity ranges for InsightFace
embeddings.

---

# Appendix C --- InsightFace Initialization

Recommended initialization:

```python
import insightface

app = insightface.app.FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)
```

---

# Appendix D --- Requirements

Example requirements.txt:

    insightface>=0.7.3
    opencv-python>=4.8.0
    numpy>=1.24.0
    pillow>=10.0.0
    streamlit>=1.28.0
    tqdm>=4.65.0
    onnxruntime>=1.16.0

Note:

InsightFace requires **onnxruntime**.

---

# Appendix E --- UI Layout

Recommended Streamlit layout:

Sidebar

- Upload selfies (multiple files)
- Dataset folder path
- Threshold slider
- Search button

Main Area

- Query faces preview
- Progress bar
- Results grid (3 images per row)
- Similarity score
- Rank
- Statistics summary

---

# Future Improvements

Possible extensions:

- FAISS vector index
- Pre-built embedding cache
- Annotated image export
- Larger dataset support
