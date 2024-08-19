# main.py

import os
import logging
from paper_prepper.prepare_references import prepare_references
from paper_prepper.scrape_papers import scrape_papers
from paper_prepper.process_failed_scrapes import process_failed_scrapes
from paper_prepper.analyze_papers import analyze_papers

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Automated Paper Sourcing")

    # Get user input for the data directory to process
    data_dir = input("Enter the name of the data directory to process: ")
    full_data_dir = os.path.join('data', data_dir)

    if not os.path.exists(full_data_dir):
        logger.error(f"Data directory {full_data_dir} does not exist.")
        return

    # Step 1: Prepare references
    input_file = os.path.join(full_data_dir, 'My Library.bib')
    output_file = os.path.join(full_data_dir, 'references.json')
    prepare_references(input_file, output_file)

    # Step 2: Scrape papers
    scrape_papers(output_file, full_data_dir)

    # Step 3: Process failed scrapes
    process_failed_scrapes(full_data_dir)

    # Step 4: Analyze papers
    analyze_papers(full_data_dir)

    logger.info("Automated Paper Sourcing completed successfully")

if __name__ == "__main__":
    main()