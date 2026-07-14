import os
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from models import QueryRequest, QueryResponse, HealthResponse
from pdf_processor import validate_pdf_metadata, process_pdf
from embedding_service import embedding_service
from semantic_search import search_policy
from utils import UPLOAD_DIR, ensure_directories, DEBUG

router = APIRouter()
logger = logging.getLogger("routes")

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process an insurance policy PDF"
)
async def upload_pdf(file: UploadFile = File(...)):
    # 1. Read file contents and retrieve file size
    try:
        content = await file.read()
        file_size = len(content)
    except Exception as e:
        logger.exception("Failed to read file payload on upload.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file. Please verify the file is accessible and not empty."
        )

    # 2. Run PDF metadata validation checks
    validate_pdf_metadata(file.filename or "", file_size)

    # Make sure local uploads directory exists
    ensure_directories()

    # Save content to a temporary location for PyPDF2 processing
    temp_path = os.path.join(UPLOAD_DIR, file.filename or "temp_policy.pdf")
    try:
        with open(temp_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.exception(f"Failed to write upload content to temp file on server: {temp_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while caching the upload. Please try again."
        )

    # 3. Process, clean, and chunk the PDF text
    try:
        chunks = process_pdf(temp_path)
    except HTTPException as he:
        # Re-raise FastAPIs HTTPExceptions
        raise he
    except Exception as e:
        logger.exception("Error occurred during process_pdf extraction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while parsing the PDF text. Please ensure the document is not corrupted."
        )
    finally:
        # Always clear temporary file from server to keep it clean
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    # 4. Generate embeddings and store them in memory
    try:
        embedding_service.embed_chunks_and_cache(chunks, file.filename or "policy.pdf")
    except Exception as e:
        # Clear cache in case of partial failures
        embedding_service.clear_cache()
        logger.exception("Failed to generate and cache text embeddings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during semantic processing of the policy. Please try again."
        )

    logger.info(f"Successfully uploaded and processed policy: '{file.filename}' ({len(chunks)} chunks).")
    return {"message": "Policy document processed successfully and ready for searching."}

@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit a natural language question against the uploaded policy"
)
async def query_policy(payload: QueryRequest):
    # 1. Validation check: question must not be empty (handled by Pydantic QueryRequest)
    # 2. Validation check: query before upload
    if not embedding_service.is_document_uploaded():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document has been uploaded. Please upload a PDF before asking questions."
        )

    # 3. Run semantic search
    try:
        result = search_policy(payload.question)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception(f"Unexpected search execution failure for query: '{payload.question}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the search query. Please try again."
        )

@router.delete(
    "/reset",
    summary="Clear the current uploaded document and cached embeddings"
)
async def reset_system():
    # Clear the in-memory cache
    embedding_service.clear_cache()

    # Clear uploads folder contents just in case
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file during reset: {file_path}. Error: {str(e)}")

    logger.info("System and document cache have been reset.")
    return {"message": "System has been reset."}

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check and diagnostic info"
)
async def health_check():
    # Make sure we try to load the model on health query if not yet loaded
    # to provide accurate diagnostics
    try:
        embedding_service.load_model()
        model_loaded = embedding_service.is_model_loaded()
    except Exception:
        model_loaded = False

    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "document_uploaded": embedding_service.is_document_uploaded()
    }

@router.get(
    "/inspect_chunks",
    summary="Inspect how the active document is chunked (for debugging)",
    include_in_schema=False
)
async def inspect_chunks():
    if not DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debugging and inspection endpoints are disabled in production."
        )

    if not embedding_service.is_document_uploaded():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document has been uploaded yet. Please upload a PDF to inspect."
        )

    inspected = []
    logger.debug("=== Chunks Inspection Diagnostics ===")
    for idx, chunk in enumerate(embedding_service.chunks_cache):
        text = chunk["text"]
        words = text.split()
        word_count = len(words)
        
        info = {
            "chunk_id": idx + 1,
            "heading": chunk.get("heading", "General Policy text"),
            "page_number": chunk["page"],
            "word_count": word_count,
            "first_300_characters": text[:300]
        }
        inspected.append(info)
        
        logger.debug(f"Chunk ID: {info['chunk_id']} | Page: {info['page_number']} | Heading: '{info['heading']}' | Words: {info['word_count']}")
        logger.debug(f"  Snippet: {info['first_300_characters'][:150].replace('\n', ' ')}...")
    logger.debug("=====================================")

    return inspected
