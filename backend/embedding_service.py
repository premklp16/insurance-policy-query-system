from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional

class EmbeddingService:
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.chunks_cache: List[Dict[str, Any]] = []
        self.uploaded_filename: Optional[str] = None

    def load_model(self) -> None:
        """
        Loads the Sentence Transformer model 'all-MiniLM-L6-v2' once at startup 
        and keeps it in memory.
        """
        if self.model is None:
            # sentence-transformers loads all-MiniLM-L6-v2 locally or pulls it if not cached.
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def is_model_loaded(self) -> bool:
        """Returns True if the sentence transformer model is loaded."""
        return self.model is not None

    def is_document_uploaded(self) -> bool:
        """Returns True if a document's chunks have been processed and cached in memory."""
        return len(self.chunks_cache) > 0 and self.uploaded_filename is not None

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single text query and returns it as a list of floats."""
        self.load_model()
        if self.model is None:
            raise RuntimeError("Sentence Transformer model failed to load.")
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding.tolist()

    def embed_chunks_and_cache(self, chunks: List[Dict[str, Any]], filename: str) -> None:
        """
        Generates embeddings for all extracted text chunks and their headings,
        and stores them with their metadata in-memory.
        """
        self.load_model()
        if self.model is None:
            raise RuntimeError("Sentence Transformer model failed to load.")

        texts = [chunk["text"] for chunk in chunks]
        headings = [chunk.get("heading", "General Policy text") for chunk in chunks]
        
        # Batch encode all chunks for performance
        chunk_embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Batch encode all headings for performance
        heading_embeddings = self.model.encode(
            headings,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Format and write into in-memory list
        self.chunks_cache = []
        for chunk, c_emb, h_emb in zip(chunks, chunk_embeddings, heading_embeddings):
            self.chunks_cache.append({
                "heading": chunk.get("heading", "General Policy text"),
                "text": chunk["text"],
                "page": chunk["page"],
                "embedding": c_emb.tolist(),
                "heading_embedding": h_emb.tolist()
            })
        self.uploaded_filename = filename

    def clear_cache(self) -> None:
        """Wipes the currently cached file information and in-memory embeddings."""
        self.chunks_cache = []
        self.uploaded_filename = None

# Instantiate a singleton to share the state in memory across endpoints
embedding_service = EmbeddingService()
