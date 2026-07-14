import os
import re
import logging
from typing import List, Dict, Any
from collections import Counter
from PyPDF2 import PdfReader
from fastapi import HTTPException, status

logger = logging.getLogger("pdf_processor")

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB in bytes

def validate_pdf_metadata(filename: str, file_size: int) -> None:
    """
    Validates PDF file metadata (extension, size).
    Raises HTTPException if validation fails.
    """
    # 1. Check file extension
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )

    # 2. Check file size limits
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes)."
        )
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"The uploaded PDF file exceeds the maximum allowed size of 20 MB."
        )

def clean_text(text: str) -> str:
    """Cleans unnecessary whitespace."""
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def repair_broken_words(text: str) -> str:
    """Repairs split words caused by PDF extraction line-wraps."""
    # 1. Handle single-letter splits (e.g. t reatment -> treatment, p olicy -> policy)
    def single_letter_repl(match):
        letter = match.group(1)
        rest = match.group(2)
        return letter + rest
        
    text = re.sub(r'\b([b-hj-np-z])\s+([a-z]+)\b', single_letter_repl, text, flags=re.IGNORECASE)
    
    # 2. Known split patterns mapping (common in PDF extractions)
    split_patterns = {
        r'\bhospi\s+tal\b': 'hospital',
        r'\bhospi\s+tals\b': 'hospitals',
        r'\bhospi\s+talization\b': 'hospitalization',
        r'\bhospi\s+talizations\b': 'hospitalizations',
        r'\bdiagnos\s+tic\b': 'diagnostic',
        r'\bdiagnos\s+tics\b': 'diagnostics',
        r'\btreat\s+ment\b': 'treatment',
        r'\btreat\s+ments\b': 'treatments',
        r'\bco\s+payment\b': 'co-payment',
        r'\bco\s+payments\b': 'co-payments',
        r'\bpre\s+existing\b': 'pre-existing',
        r'\bexclu\s+sion\b': 'exclusion',
        r'\bexclu\s+sions\b': 'exclusions',
        r'\bout\s+patient\b': 'outpatient',
        r'\bin\s+patient\b': 'inpatient',
        r'\bmedi\s+cal\b': 'medical',
        r'\binsur\s+ance\b': 'insurance',
        r'\bwait\s+ing\b': 'waiting',
        r'\bma\s+ternity\b': 'maternity',
        r'\bcatar\s+act\b': 'cataract',
        r'\bop\s+d\b': 'opd',
    }
    
    for pattern, replacement in split_patterns.items():
        def case_repl(match, repl=replacement):
            matched_str = match.group(0)
            if matched_str[0].isupper():
                return repl.capitalize()
            return repl
            
        text = re.compile(pattern, re.IGNORECASE).sub(case_repl, text)
        
    return text

PAGE_PATTERN = re.compile(
    r'^(page\s+\d+\s+of\s+\d+|page\s+\d+|[Pp]age\s*-?\s*\d+\s*-?)$', 
    re.IGNORECASE
)
UIN_PATTERN = re.compile(
    r'\b(UIN|IRDAI|CIN|Reg\s+No|Regd?\.\s*Office|Registered\s+Office|National\s+Insurance|Arogya\s+Sanjeevani)\b.*', 
    re.IGNORECASE
)
HEADING_REGEX = re.compile(
    r'^(\d+(\.\d+)+\.?\s+|Section\s+\d+|Clause\s+\d+|Chapter\s+\d+|Exclusion\s+\d+|Exclusions\b)',
    re.IGNORECASE
)

def process_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Reads the PDF, extracts text, handles validation checks, cleans page text
    by stripping repeated headers/footers, and groups them line-by-line into chunks.
    """
    # 3. Read and check for corruption
    try:
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
    except Exception as e:
        logger.exception(f"Corrupted or invalid PDF file path: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to parse the PDF document. Please verify the file is not corrupted or password-protected."
        )

    if num_pages == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The PDF file contains no pages."
        )

    # Extract text from pages line by line
    raw_pages_lines = []
    line_counts = Counter()

    for idx in range(num_pages):
        page_num = idx + 1
        try:
            page = reader.pages[idx]
            text = page.extract_text()
            if text:
                # Normalize newline characters
                text = text.replace("\r\n", "\n").replace("\r", "\n")
                # Split page into lines
                lines = [line.strip() for line in text.split("\n")]
                raw_pages_lines.append((page_num, lines))
                for line in lines:
                    if len(line) > 3:  # Only count lines longer than 3 chars
                        line_counts[line] += 1
        except Exception:
            # Fallback for page reading errors
            continue

    # Identify repeated header/footer lines (appearing on 3 or more pages)
    repeated_lines = {line for line, count in line_counts.items() if count >= 3}

    # Clean pages text using header/footer filter and word repair
    pages_text = []
    total_extracted_chars = 0

    for page_num, lines in raw_pages_lines:
        cleaned_lines = []
        for line in lines:
            # 1. Skip if it is a repeated header/footer line
            if line in repeated_lines:
                continue
            
            # 2. Skip if it matches page numbers or UIN patterns
            if PAGE_PATTERN.match(line) or UIN_PATTERN.search(line):
                continue
            
            # 3. Clean spacing
            line_clean = clean_text(line)
            
            # 4. Repair broken words
            line_clean = repair_broken_words(line_clean)
            
            if line_clean:
                cleaned_lines.append(line_clean)
                
        if cleaned_lines:
            page_text = "\n".join(cleaned_lines)
            pages_text.append((page_num, page_text))
            total_extracted_chars += len(page_text)

    # 4. Check if we extracted any text (prevent scanned PDFs with no text layers)
    if total_extracted_chars == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text was found in the PDF after cleaning. Scanned PDFs are not supported."
        )

    # Split page text into line-page mappings for chunking
    lines_mapped = []
    for page_num, text in pages_text:
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if line_str:
                lines_mapped.append((page_num, line_str))

    heading_indices = []
    for idx, (page_num, line_str) in enumerate(lines_mapped):
        if HEADING_REGEX.match(line_str) and len(line_str) < 120:
            heading_indices.append(idx)

    # 2. If headings are found (at least 2 headings), chunk by headings
    if len(heading_indices) >= 2:
        raw_sections = []
        for i in range(len(heading_indices)):
            start_idx = heading_indices[i]
            end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines_mapped)
            
            section_lines = lines_mapped[start_idx:end_idx]
            heading = section_lines[0][1]
            page = section_lines[0][0]
            
            text_lines = [item[1] for item in section_lines]
            section_text = "\n".join(text_lines)
            
            raw_sections.append({
                "heading": heading,
                "text": section_text,
                "page": page
            })

        # Process sections: split large sections (> 500 words) into sub-chunks with headings prepended
        chunks = []
        for sec in raw_sections:
            words = sec["text"].split()
            word_count = len(words)
            
            if word_count <= 500:
                chunks.append({
                    "heading": sec["heading"],
                    "text": sec["text"],
                    "page": sec["page"]
                })
            else:
                heading_text = sec["heading"]
                page = sec["page"]
                
                # Split into sub-chunks of ~400 words with some overlap
                for j in range(0, word_count, 400):
                    sub_words = words[j:j + 400]
                    sub_text = " ".join(sub_words)
                    
                    # Prepend section heading to sub-chunk
                    if not sub_text.startswith(heading_text):
                        sub_text = f"{heading_text} (continued):\n{sub_text}"
                        
                    chunks.append({
                        "heading": heading_text,
                        "text": sub_text,
                        "page": page
                    })
    else:
        # 3. Fallback to standard paragraph-based chunking
        paragraphs = []
        for page_num, text in pages_text:
            parts = [p.strip() for p in text.split("\n\n") if p.strip()]
            for part in parts:
                paragraphs.append((page_num, part))

        chunks = []
        current_chunk = []
        current_word_count = 0
        current_page = None

        for page_num, para in paragraphs:
            words = para.split()
            word_count = len(words)
            if word_count == 0:
                continue

            if word_count > 500:
                sub_paragraphs = []
                for i in range(0, word_count, 400):
                    sub_words = words[i:i + 400]
                    sub_paragraphs.append((page_num, " ".join(sub_words)))
            else:
                sub_paragraphs = [(page_num, para)]

            for p_num, p_text in sub_paragraphs:
                p_words = p_text.split()
                p_len = len(p_words)

                if not current_chunk:
                    current_chunk = [p_text]
                    current_word_count = p_len
                    current_page = p_num
                elif current_word_count + p_len <= 500:
                    current_chunk.append(p_text)
                    current_word_count += p_len
                else:
                    chunks.append({
                        "heading": "General Policy text",
                        "text": "\n\n".join(current_chunk),
                        "page": current_page
                    })
                    current_chunk = [p_text]
                    current_word_count = p_len
                    current_page = p_num

        if current_chunk:
            chunks.append({
                "heading": "General Policy text",
                "text": "\n\n".join(current_chunk),
                "page": current_page
            })

    return chunks
