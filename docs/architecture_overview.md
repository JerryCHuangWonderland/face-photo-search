# Architecture Overview --- Face Photo Search System

This document provides a **visual explanation of the system
architecture** for the Face Photo Search System.

The goal is to help reviewers quickly understand how the system works
end‑to‑end.

------------------------------------------------------------------------

# 1. High-Level System Flow

``` mermaid
flowchart LR

A[User Upload Selfie] --> B[Streamlit UI]
B --> C[Query Builder]

D[Upload Dataset Folder] --> B

C --> E[Face Service]
E --> F[Embedding Extraction]

F --> G[Matcher]
G --> H[Result Aggregator]

H --> I[Statistics]
H --> J[Results JSON]
H --> K[UI Display]
```

Explanation:

-   Users upload **selfies** and a **dataset folder**
-   The system extracts **face embeddings**
-   Cosine similarity is used to find matches
-   Results are aggregated and displayed in the UI

------------------------------------------------------------------------

# 2. Processing Pipeline

``` mermaid
flowchart TD

A[Selfie Images] --> B[Face Detection]
B --> C[Select Main Face]
C --> D[Generate Query Embedding]

E[Dataset Photos] --> F[Scan Images]
F --> G[Detect Faces]
G --> H[Generate Face Embeddings]

D --> I[Similarity Matching]
H --> I

I --> J[Threshold Filtering]
J --> K[Matched Photos]

K --> L[Result Aggregation]
L --> M[Results + Statistics]
```

Pipeline steps:

1.  Detect faces from selfie images
2.  Generate query embeddings
3.  Scan dataset images
4.  Extract embeddings for all detected faces
5.  Compare embeddings using cosine similarity
6.  Filter matches using similarity threshold
7.  Aggregate results and compute statistics

------------------------------------------------------------------------

# 3. Code Architecture

``` mermaid
flowchart LR

UI[app/ui.py] --> PIPELINE[app/main.py]

PIPELINE --> FACE[core/face_service.py]
PIPELINE --> SCANNER[core/file_scanner.py]
PIPELINE --> QUERY[core/query_builder.py]
PIPELINE --> MATCHER[core/matcher.py]
PIPELINE --> AGG[core/result_aggregator.py]
PIPELINE --> REPORT[core/reporter.py]
```

Module responsibilities:

  Module                   Responsibility
  ------------------------ ---------------------------------------
  `ui.py`                  Streamlit interface
  `main.py`                Pipeline orchestration
  `face_service.py`        Face detection + embedding extraction
  `file_scanner.py`        Dataset image discovery
  `query_builder.py`       Build query embeddings from selfies
  `matcher.py`             Cosine similarity matching
  `result_aggregator.py`   Merge duplicate matches
  `reporter.py`            Export results and statistics

------------------------------------------------------------------------

# 4. Face Recognition Model

The system uses:

**InsightFace -- buffalo_l model**

Capabilities:

-   Face detection
-   Face alignment
-   512‑dimension embeddings

Embedding example:

    [0.034, -0.118, 0.562, ..., -0.217]

Similarity calculation:

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

Higher values indicate more similar faces.

------------------------------------------------------------------------

# 5. Streamlit UI Architecture

``` mermaid
flowchart TD

A[Sidebar Inputs] --> B[Selfie Upload]
A --> C[Dataset Folder Upload]
A --> D[Threshold Slider]

B --> E[Run Search]
C --> E
D --> E

E --> F[Search Pipeline]

F --> G[Match Results]
F --> H[Statistics]

G --> I[Result Grid]
H --> J[Metrics Panel]
```

UI features:

-   Multiple selfie upload
-   Dataset folder upload
-   Threshold adjustment slider
-   Grid layout result display
-   Bounding box visualization
-   Statistics summary

------------------------------------------------------------------------

# 6. Performance Considerations

Current approach:

-   Face embeddings are generated during each search

Future optimization:

``` mermaid
flowchart LR

Dataset --> EmbeddingExtraction
EmbeddingExtraction --> EmbeddingIndex

Query --> QueryEmbedding
QueryEmbedding --> VectorSearch

EmbeddingIndex --> VectorSearch
VectorSearch --> Results
```

Possible improvements:

-   Embedding cache
-   FAISS vector index
-   GPU acceleration

These optimizations would allow the system to scale to **thousands of
images**.

------------------------------------------------------------------------

# 7. End-to-End Summary

``` mermaid
flowchart LR

User --> UploadSelfie
User --> UploadDataset

UploadSelfie --> QueryEmbedding
UploadDataset --> DatasetEmbeddings

QueryEmbedding --> SimilaritySearch
DatasetEmbeddings --> SimilaritySearch

SimilaritySearch --> MatchedPhotos
MatchedPhotos --> StreamlitUI
```

Final output:

-   Matched photos
-   Similarity scores
-   Bounding box visualization
-   Search statistics

------------------------------------------------------------------------

# Key Design Goals

The system architecture prioritizes:

-   **Modularity** (separate core modules)
-   **Reusability** (shared pipeline for CLI and UI)
-   **Explainability** (clear search steps)
-   **Extensibility** (future vector index support)
