# utils/load_papers_to_db.py

import os
import sqlite3
import bibtexparser
from typing import Dict, Any
import logging

# Global variables
DB_DIR = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\source_papers"
DB_NAME = "iot_ml_review.db"
PAPERS_DIR = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\source_papers\raw_files"
BIB_FILE = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\My Library.bib"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database(db_path: str):
    """Initialize the SQLite database with necessary tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY,
        bibtex_key TEXT UNIQUE,
        title TEXT,
        authors TEXT,
        year INTEGER,
        doi TEXT,
        full_text TEXT,
        file_path TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Initialized database at {db_path}")

def load_bibtex(bib_file: str) -> Dict[str, Any]:
    """Load BibTeX data from a file."""
    with open(bib_file, 'r', encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    return {entry['ID']: entry for entry in bib_database.entries}

def find_full_text_file(papers_dir: str, bibtex_key: str) -> str:
    """Find the full text file corresponding to a BibTeX key."""
    for filename in os.listdir(papers_dir):
        if bibtex_key in filename:
            return os.path.join(papers_dir, filename)
    return ""

def load_papers_to_db(db_path: str, papers_dir: str, bib_file: str):
    """Load papers and their metadata into the SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    bibtex_data = load_bibtex(bib_file)
    
    for bibtex_key, entry in bibtex_data.items():
        full_text_path = find_full_text_file(papers_dir, bibtex_key)
        if not full_text_path:
            logger.warning(f"No full text file found for {bibtex_key}")
            continue
        
        with open(full_text_path, 'r', encoding='utf-8') as file:
            full_text = file.read()
        
        cursor.execute('''
        INSERT OR REPLACE INTO papers 
        (bibtex_key, title, authors, year, doi, full_text, file_path) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bibtex_key,
            entry.get('title', ''),
            ' and '.join(entry.get('author', '').split(' and ')),
            int(entry.get('year', 0)),
            entry.get('doi', ''),
            full_text,
            full_text_path
        ))
    
    conn.commit()
    conn.close()
    logger.info(f"Loaded {len(bibtex_data)} papers into the database")

def main():
    # Ensure the database directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Construct the full database path
    db_path = os.path.join(DB_DIR, DB_NAME)
    
    init_database(db_path)
    load_papers_to_db(db_path, PAPERS_DIR, BIB_FILE)

if __name__ == "__main__":
    main()