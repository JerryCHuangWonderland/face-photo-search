"""Cosine similarity matching between query and candidate face embeddings."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.config import DEFAULT_THRESHOLD


@dataclass
class CandidateFace:
    """A face detected in a dataset photo."""

    photo_path: str
    bbox: list[int]
    embedding: np.ndarray


@dataclass
class MatchResult:
    """A dataset photo that matched a query embedding."""

    photo_path: str
    best_bbox: list[int]
    best_score: float
    matched_query_index: int
    rank: int  # assigned after sorting


def compute_similarity(
    query_embedding: np.ndarray,
    candidate_embedding: np.ndarray,
) -> float:
    """Compute cosine similarity between two embedding vectors.

    Args:
        query_embedding: 512-d query vector.
        candidate_embedding: 512-d candidate vector.

    Returns:
        Cosine similarity in the range [-1, 1].
    """
    norm_q = np.linalg.norm(query_embedding)
    norm_c = np.linalg.norm(candidate_embedding)
    if norm_q == 0 or norm_c == 0:
        return 0.0
    return float(np.dot(query_embedding, candidate_embedding) / (norm_q * norm_c))


def find_matches(
    query_embeddings: list[np.ndarray],
    candidate_faces: list[CandidateFace],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[MatchResult]:
    """Compare every candidate face against all query embeddings.

    Each candidate is compared to every query; only the best scoring
    query is kept for that candidate.  Results below *threshold* are
    discarded.

    Args:
        query_embeddings: List of query embedding vectors.
        candidate_faces: Faces detected across the dataset.
        threshold: Minimum cosine similarity to consider a match.

    Returns:
        Unsorted list of ``MatchResult`` objects (rank is set to 0).
    """
    matches: list[MatchResult] = []

    for candidate in candidate_faces:
        best_score: float = -1.0
        best_query_idx: int = -1

        for q_idx, q_emb in enumerate(query_embeddings):
            score = compute_similarity(q_emb, candidate.embedding)
            if score > best_score:
                best_score = score
                best_query_idx = q_idx

        if best_score >= threshold:
            matches.append(
                MatchResult(
                    photo_path=candidate.photo_path,
                    best_bbox=candidate.bbox,
                    best_score=round(best_score, 4),
                    matched_query_index=best_query_idx,
                    rank=0,
                )
            )

    return matches
