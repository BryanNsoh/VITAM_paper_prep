# paper_prepper/utils/file_utils.py

import chardet
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def detect_encoding(file_path: str, fallback_encodings: List[str] = ['utf-8', 'iso-8859-1', 'windows-1252']) -> str:
    """
    Detect the encoding of a file using chardet, with fallback options.
    
    Args:
    file_path (str): Path to the file
    fallback_encodings (List[str]): List of encodings to try if chardet fails

    Returns:
    str: Detected encoding
    """
    # First, try to detect the encoding using chardet
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    detected = chardet.detect(raw_data)
    if detected['encoding'] and detected['confidence'] > 0.7:
        logger.info(f"Detected encoding for {file_path}: {detected['encoding']} (confidence: {detected['confidence']})")
        return detected['encoding']

    # If chardet fails or has low confidence, try fallback encodings
    for encoding in fallback_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                file.read()
            logger.info(f"Successfully read {file_path} with fallback encoding: {encoding}")
            return encoding
        except UnicodeDecodeError:
            continue

    # If all attempts fail, raise an exception
    raise ValueError(f"Unable to determine encoding for {file_path}")

def read_file(file_path: str) -> str:
    """
    Read a file using the detected encoding.

    Args:
    file_path (str): Path to the file

    Returns:
    str: Contents of the file
    """
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()

def write_file(file_path: str, content: str, encoding: Optional[str] = None) -> None:
    """
    Write content to a file using the specified or detected encoding.

    Args:
    file_path (str): Path to the file
    content (str): Content to write
    encoding (Optional[str]): Encoding to use, if None, UTF-8 will be used
    """
    encoding = encoding or 'utf-8'
    with open(file_path, 'w', encoding=encoding) as file:
        file.write(content)
    logger.info(f"Successfully wrote to {file_path} using encoding: {encoding}")