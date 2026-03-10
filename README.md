
# Face Photo Search System

AI-powered facial search tool that scans a photo collection and finds images containing a specific person using selfie input.

This project demonstrates **AI‑assisted development (Vibe Coding)** where system design, implementation, testing, and documentation were iteratively developed with AI collaboration.

---

# Demo

### Search Interface

![UI Overview](docs/screenshots/ui_overview.png)

Users upload selfie images and a dataset folder, then adjust the similarity threshold.

---

### Searching

![Searching](docs/screenshots/search_running.png)

The system scans the dataset, detects faces, and compares embeddings.

---

### Results

![Results](docs/screenshots/results.png)

Matched photos are displayed with:

- bounding box
- similarity score
- ranking
- statistics

Example search result for a dataset of ~200 photos.

---

# Features

- Multiple selfie inputs
- Dataset folder upload
- Automatic face detection
- Face embedding extraction
- Cosine similarity search
- Adjustable similarity threshold
- Bounding box visualization
- Search statistics
- JSON result export
- Streamlit web UI

---

# System Architecture

```mermaid
flowchart LR
User --> UI
UI --> Pipeline
Pipeline --> FaceService
Pipeline --> FileScanner
Pipeline --> QueryBuilder
Pipeline --> Matcher
Pipeline --> Aggregator
Aggregator --> Results
```

Module responsibilities:

| Module | Responsibility |
|------|------|
| `app/ui.py` | Streamlit interface |
| `app/main.py` | Pipeline orchestration |
| `core/face_service.py` | Face detection + embedding extraction |
| `core/file_scanner.py` | Dataset image discovery |
| `core/query_builder.py` | Build query embeddings |
| `core/matcher.py` | Cosine similarity matching |
| `core/result_aggregator.py` | Merge duplicate matches |
| `core/reporter.py` | Export statistics and JSON output |

---

# Processing Pipeline

```mermaid
flowchart TD

SelfieImages --> DetectFaces
DetectFaces --> QueryEmbedding

DatasetImages --> ScanDataset
ScanDataset --> DetectDatasetFaces
DetectDatasetFaces --> DatasetEmbeddings

QueryEmbedding --> SimilaritySearch
DatasetEmbeddings --> SimilaritySearch

SimilaritySearch --> ThresholdFilter
ThresholdFilter --> MatchedPhotos

MatchedPhotos --> Aggregation
Aggregation --> Results
```

---

# Technology Stack

Language
- Python 3.12

Computer Vision
- InsightFace (buffalo_l model)

Libraries
- OpenCV
- NumPy
- Streamlit

Similarity Metric
- Cosine Similarity

---

# Installation

## 1. Install Python

Install **Python 3.12**.

Verify:

```
py -3.12 --version
```

---

## 2. Clone Repository

```
git clone <repository-url>
cd face-photo-search
```

---

## 3. Create Virtual Environment

```
py -3.12 -m venv .venv
```

Activate (Windows):

```
.venv\Scripts\activate
```

---

## 4. Install Dependencies

```
pip install -r requirements.txt
```

InsightFace will automatically download the required model during first execution.

---

# Running the Application

Start the web interface:

```
streamlit run app/ui.py
```

Then open the local URL shown in the terminal.

---

# Usage Guide

## Step 1 — Upload Selfies

Upload one or more selfie images containing the person you want to search for.

Tips:

- Use clear frontal faces
- Multiple selfies improve matching reliability

---

## Step 2 — Upload Dataset Folder

Upload the folder containing the photos you want to search.

Supported formats:

- JPG
- JPEG
- PNG

Subfolders are supported.

---

## Step 3 — Adjust Similarity Threshold

Default value:

```
0.45
```

Lower threshold
- higher recall
- more matches

Higher threshold
- higher precision
- fewer matches

---

## Step 4 — Run Search

Click **Search**.

The system will:

1. Detect faces
2. Extract embeddings
3. Compare embeddings
4. Filter matches
5. Display results

---

# Output

Results include:

- matched images
- bounding box highlighting the detected face
- similarity score
- search statistics

The system also exports:

```
outputs/results.json
```

Example statistics:

- total photos scanned
- photos containing faces
- matched photos
- processing time

---

# Repository Structure

```
face-photo-search
│
├─ README.md
│
├─ docs
│  ├─ screenshots
│  │   ├─ ui_overview.png
│  │   ├─ search_running.png
│  │   └─ results.png
│  │
│  ├─ spec.md
│  ├─ vibe_log.md
│  └─ architecture_overview.md
│
├─ app
├─ core
└─ requirements.txt
```

---

# Development Documentation

Detailed design and development process are documented in:

```
docs/spec.md
docs/vibe_log.md
docs/architecture_overview.md
```

These include:

- system design
- AI collaboration workflow
- prompt engineering iterations
- implementation decisions

---

# Performance Notes

Current approach:

- embeddings are computed during each search

Potential future optimizations:

- embedding cache
- FAISS vector index
- GPU acceleration

These improvements would allow the system to scale to thousands of images.

---

# License

This project is intended for educational and demonstration purposes.
