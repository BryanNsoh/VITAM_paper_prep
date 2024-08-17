# paper_prepper/bibtex_to_json.py

import os
import json
import bibtexparser
from typing import Dict, Any
from utils.file_utils import read_file, write_file

# Global variables
INPUT_BIB = os.path.join('data', 'iot_ml_review', 'My Library.bib')
OUTPUT_DIR = os.path.join('data', 'iot_ml_review')

def clean_text(text: str) -> str:
    return text.strip().replace('{', '').replace('}', '')

def extract_links(entry: Dict[str, Any]) -> list:
    links = []
    if 'doi' in entry:
        links.append(f"https://doi.org/{entry['doi']}")
    if 'url' in entry:
        links.append(entry['url'])
    return links

def bibtex_to_json(bibtex_str: str) -> Dict[str, Any]:
    parser = bibtexparser.bparser.BibTexParser(ignore_nonstandard_types=False)
    bib_database = bibtexparser.loads(bibtex_str, parser)
    
    result = {}
    for entry in bib_database.entries:
        key = entry['ID']
        result[key] = {
            "title": clean_text(entry.get('title', '')),
            "links": extract_links(entry),
            "bibtex_data": entry  # Preserve all BibTeX data
        }
    
    return result

def process_bibtex_file():
    try:
        bibtex_content = read_file(INPUT_BIB)
        json_data = bibtex_to_json(bibtex_content)
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(OUTPUT_DIR, 'references.json')
        
        json_content = json.dumps(json_data, indent=2, ensure_ascii=False)
        write_file(output_file, json_content)
        
        print(f"Successfully converted BibTeX to JSON. Output saved to {output_file}")
    except FileNotFoundError:
        print(f"Error: Input file {INPUT_BIB} not found.")
    except json.JSONDecodeError:
        print("Error: Failed to encode data to JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    process_bibtex_file()