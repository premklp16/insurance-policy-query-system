import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

logger = logging.getLogger("app")

# Add current directory to path so imports work correctly
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from routes import router
from embedding_service import embedding_service
from utils import ensure_directories

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize necessary folders
    ensure_directories()
    # Eagerly load the model on startup so that the user's first query has zero latency
    logger.info("Loading Sentence Transformers model ('all-MiniLM-L6-v2') on startup...")
    try:
        embedding_service.load_model()
        logger.info("Model 'all-MiniLM-L6-v2' successfully loaded in memory.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to load Sentence Transformer model on startup: {str(e)}", exc_info=True)
    
    yield
    # Cleanup memory embeddings on shutdown
    embedding_service.clear_cache()
    logger.info("Caches cleared. Backend shutting down.")

app = FastAPI(
    title="Insurance Policy Query API",
    description="Semantic document retrieval API using Sentence Transformers, Scikit-learn (Cosine Similarity), and FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
# Allow requests from Vite default dev server (typically http://localhost:5173 or http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for seamless local developer setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routes router
app.include_router(router)
