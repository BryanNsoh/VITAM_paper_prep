import os
import json
import asyncio
import logging
import sys
import aiohttp
from pathlib import Path
from typing import List, Dict, Tuple
from utils.slow_scraper import UnifiedWebScraper  # Adjust the import path if necessary

# ============================
# Configuration Section
# ============================

# List of source folders to process
SOURCE_FOLDERS = [
    r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Documents\Projects\ACADEMIC LITERATURE UTILITIES\Automated Paper Sourcing\data\Al-Mutawtah et al. 2023",
    r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Documents\Projects\ACADEMIC LITERATURE UTILITIES\Automated Paper Sourcing\data\Fair et al. 2020",
    r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Documents\Projects\ACADEMIC LITERATURE UTILITIES\Automated Paper Sourcing\data\Jacobson et al. 2019",
    r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Documents\Projects\ACADEMIC LITERATURE UTILITIES\Automated Paper Sourcing\data\Hodgkinson et al. 2014"
    # Add more folders as needed
]

# Expected reference JSON filename in each folder
REFERENCE_JSON_FILENAME = "references.json"

# Minimum word count threshold for a valid paper
MIN_WORDS = 700

# Maximum number of retries for scraping each URL
MAX_RETRIES = 3

# Initial timeout in seconds for page loading and interactions
INITIAL_TIMEOUT = 60

# ============================
# Logging Configuration
# ============================

def setup_logging(log_file: str = "unified_scraper.log") -> None:
    """
    Sets up unified logging to both console and a log file.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )

# ============================
# Utility Functions
# ============================

def validate_reference_json(file_path: str) -> bool:
    """
    Validates the format of the reference JSON file.
    Expected format: a dictionary where each key maps to a dict containing 'title' and 'links' list.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(value, dict):
                    return False
                if 'links' not in value or not isinstance(value['links'], list):
                    return False
                for link in value['links']:
                    if not isinstance(link, str):
                        return False
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Failed to validate JSON file {file_path}: {str(e)}")
        return False

def collect_papers_from_json(file_path: str) -> Dict[str, List[str]]:
    """
    Extracts a dictionary mapping paper keys to their list of URLs from the reference JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        papers = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if 'links' in value and isinstance(value['links'], list):
                    papers[key] = value['links']
        return papers
    except Exception as e:
        logging.error(f"Failed to extract papers from JSON file {file_path}: {str(e)}")
        return {}

# ============================
# Main Scraping Function
# ============================

async def scrape_papers():
    """
    Main function to orchestrate the scraping of papers from multiple source folders.
    """
    setup_logging()
    logger = logging.getLogger("scrape_papers")

    # Initialize UnifiedWebScraper
    async with aiohttp.ClientSession() as session:
        scraper = UnifiedWebScraper(
            session=session,
            max_concurrent_tasks=1,  # Process one URL at a time
            initial_timeout=INITIAL_TIMEOUT
        )
        try:
            await scraper.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {str(e)}")
            return

        # Iterate through each source folder
        for folder in SOURCE_FOLDERS:
            folder_path = Path(folder)
            logger.info(f"Processing folder: {folder_path}")

            if not folder_path.exists() or not folder_path.is_dir():
                logger.error(f"Folder does not exist or is not a directory: {folder_path}")
                continue

            # Path to the reference JSON file
            reference_json_path = folder_path / REFERENCE_JSON_FILENAME

            if not reference_json_path.exists():
                logger.error(f"Reference JSON file not found: {reference_json_path}")
                continue

            # Validate the reference JSON file
            if not validate_reference_json(str(reference_json_path)):
                logger.error(f"Invalid format in reference JSON file: {reference_json_path}")
                continue

            # Extract papers and their links from the JSON file
            papers = collect_papers_from_json(str(reference_json_path))
            logger.info(f"Found {len(papers)} papers in {reference_json_path}")

            # Print a sample of the references.json to ensure it's being read correctly
            sample_papers = dict(list(papers.items())[:2])  # Get first 2 entries as a sample
            logger.info(f"Sample of references.json: {json.dumps(sample_papers, indent=2)}")

            # Define the output folder as the source folder itself
            source_output_folder = folder_path
            logger.info(f"PDFs will be saved directly to: {source_output_folder}")

            # Process each paper
            for paper_key, links in papers.items():
                logger.info(f"Processing paper: {paper_key}")
                best_word_count = -1
                best_pdf_path = ""

                for link in links:
                    logger.info(f"Scraping link: {link}")
                    content, pdf_path = await scraper.scrape(link, min_words=MIN_WORDS, max_retries=MAX_RETRIES)

                    if content and pdf_path:
                        word_count = len(content.split())
                        logger.info(f"Word count for URL {link}: {word_count}")

                        if word_count > best_word_count:
                            best_word_count = word_count
                            best_pdf_path = pdf_path

                if best_pdf_path:
                    # Define the final PDF path with the paper_key as the filename
                    final_pdf_path = source_output_folder / f"{paper_key}.pdf"
                    try:
                        os.rename(best_pdf_path, final_pdf_path)
                        logger.info(f"Saved best PDF for {paper_key} at {final_pdf_path}")
                        print(f"\nPaper: {paper_key}\nStatus: Success\nWord count: {best_word_count}\nSaved as: {final_pdf_path}\n" + "-" * 80)
                    except Exception as e:
                        logger.error(f"Failed to rename/move PDF for {paper_key}: {str(e)}")
                else:
                    logger.warning(f"No valid PDF found for paper: {paper_key}")
                    print(f"\nPaper: {paper_key}\nStatus: Failure (No valid PDF found)\n" + "-" * 80)

        # After processing all folders
        await scraper.close()
        logger.info("Completed scraping all sources.")

# ============================
# Entry Point
# ============================

if __name__ == "__main__":
    asyncio.run(scrape_papers())
