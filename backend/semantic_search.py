import re
import logging
import numpy as np
from typing import Dict, Any, List
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import HTTPException, status
from embedding_service import embedding_service
from utils import DEBUG

logger = logging.getLogger("semantic_search")

STOP_WORDS = {"the", "is", "does", "this", "policy", "cover", "under", "for", "with", "a", "an", "and", "or", "of", "to", "in", "on", "at", "by", "from", "are", "about", "what", "how", "any"}

def search_policy(query_text: str) -> Dict[str, Any]:
    """
    Executes the semantic search pipeline:
    1. Generates embedding for the query.
    2. Compares with all stored chunk embeddings.
    3. Retrieves the Top-3 most similar chunks.
    4. Splits the best matching chunk (Top-1) into sentences, matches the query against each sentence,
       and returns the best sentence (highlighted_sentence) along with surrounding context.
    """
    # Verify embeddings are present in memory
    if not embedding_service.is_document_uploaded():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No policy document has been uploaded yet. Please upload a PDF before querying."
        )

    # 1. Generate query embedding
    try:
        query_embedding = embedding_service.embed_text(query_text)
    except Exception as e:
        logger.exception("Failed to generate query embedding.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the search query. Please try again."
        )

    # 2. Compare with all stored chunk embeddings
    chunks = embedding_service.chunks_cache
    
    # Structure inputs for cosine_similarity
    query_vector = np.array(query_embedding).reshape(1, -1)
    chunk_vectors = np.array([chunk["embedding"] for chunk in chunks])

    # Compute similarity matrix (shape: 1 x N)
    similarity_matrix = cosine_similarity(query_vector, chunk_vectors)
    scores = similarity_matrix[0]

    # Pair scores with their corresponding index
    scored_indices = []
    for idx, score in enumerate(scores):
        similarity_percentage = max(0.0, float(score) * 100.0)
        scored_indices.append((similarity_percentage, idx))

    # 1. Extract query keywords
    query_clean = re.sub(r'[^\w\s-]', ' ', query_text.lower())
    words = query_clean.split()
    
    keywords = []
    for w in words:
        w_clean = w.strip("-")
        if w_clean not in STOP_WORDS and len(w_clean) > 1:
            keywords.append(w_clean)
            
    logger.debug(f"Query: '{query_text}' | Keywords Extracted: {keywords}")

    # 3. Retrieve the Top-5 most similar chunks (descending score)
    scored_indices.sort(key=lambda x: x[0], reverse=True)
    top_5_raw = scored_indices[:5]

    # Perform heading-aware and keyword-overlap reranking on these Top-5 chunks
    reranked_chunks = []
    for rank, (chunk_score, idx) in enumerate(top_5_raw):
        chunk = chunks[idx]
        
        # Heading similarity
        heading_emb = chunk.get("heading_embedding")
        if heading_emb:
            heading_vector = np.array(heading_emb).reshape(1, -1)
            h_similarity_matrix = cosine_similarity(query_vector, heading_vector)
            h_score = max(0.0, float(h_similarity_matrix[0][0]) * 100.0)
        else:
            h_score = 0.0
            
        # Keyword overlap score
        if not keywords:
            kw_score = 0.0
        else:
            matched_count = 0.0
            heading_lower = chunk.get("heading", "").lower()
            text_lower = chunk["text"].lower()
            for kw in keywords:
                if kw in heading_lower:
                    matched_count += 1.0
                elif kw in text_lower:
                    matched_count += 0.5
            kw_score = min(100.0, (matched_count / len(keywords)) * 100.0)
            
        # Compute final combined score: 0.6 semantic + 0.2 heading + 0.2 keyword
        final_score = 0.6 * chunk_score + 0.2 * h_score + 0.2 * kw_score
        reranked_chunks.append({
            "idx": idx,
            "chunk_score": chunk_score,
            "heading_score": h_score,
            "kw_score": kw_score,
            "final_score": final_score,
            "chunk": chunk
        })

    # Sort the Top-5 chunks by final_score descending
    reranked_chunks.sort(key=lambda x: x["final_score"], reverse=True)

    # Log diagnostic Top-5 reranked information internally
    logger.debug("--- Semantic Search Diagnostics & Combined Reranking (Top-5 Chunks) ---")
    for rank, item in enumerate(reranked_chunks):
        chunk = item["chunk"]
        heading = chunk.get("heading", "General Policy text")
        logger.debug(f"Rank {rank + 1}: Page {chunk['page']} | Heading: '{heading}'")
        logger.debug(f"  Chunk Sim: {item['chunk_score']:.2f}% | Heading Sim: {item['heading_score']:.2f}% | Keyword Overlap: {item['kw_score']:.2f}% | Final Score: {item['final_score']:.2f}%")
        snippet = chunk['text'][:100].replace("\n", " ")
        logger.debug(f"  Snippet: {snippet}...")
    logger.debug("----------------------------------------------------------------------")

    # 4. Select the chunk with the highest final score
    best_item = reranked_chunks[0]
    best_chunk = best_item["chunk"]
    best_score = best_item["final_score"]
    chunk_text = best_chunk["text"]

    # 5. Sentence-level retrieval: split chunk into sentences and find the best match
    try:
        # Split on period, question mark, or exclamation mark followed by whitespace
        sentences = re.split(r'(?<=[.!?])\s+', chunk_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences and embedding_service.is_model_loaded():
            # Generate embeddings for individual sentences (with normalization)
            sentence_embeddings = embedding_service.model.encode(
                sentences,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            sentence_vectors = np.array(sentence_embeddings)
            
            # Compute cosine similarities for each sentence
            s_sim_matrix = cosine_similarity(query_vector, sentence_vectors)
            s_scores = s_sim_matrix[0]
            
            best_s_idx = int(np.argmax(s_scores))
            highlighted_sentence = sentences[best_s_idx]
            
            # Extract surrounding context: 1 sentence before and 1 sentence after
            start_s_idx = max(0, best_s_idx - 1)
            end_s_idx = min(len(sentences) - 1, best_s_idx + 1)
            context_sentences = sentences[start_s_idx:end_s_idx + 1]
            answer_text = " ".join(context_sentences)
        else:
            answer_text = chunk_text
            highlighted_sentence = None
    except Exception as e:
        # Fallback to the full chunk text on any unexpected processing errors
        logger.warning("Sentence-level retrieval failed, falling back to full chunk text.", exc_info=True)
        answer_text = chunk_text
        highlighted_sentence = None

    return {
        "status": "success",
        "answer": answer_text,
        "highlighted_sentence": highlighted_sentence,
        "page": best_chunk["page"],
        "similarity": round(best_score, 2),
        "message": None,
        "heading": best_chunk.get("heading")
    }
