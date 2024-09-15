# citation_transformer.py

import json
import os
import re

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_text(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def replace_citations(text, replacements):
    for replacement in replacements:
        text = text.replace(replacement['original'], replacement['replacement'])
    return text

def reorder_bibtex(bibtex_content, citation_order):
    entries = re.split(r'(@\w+\{[^@]+\})', bibtex_content)[1:]  # Split entries, keeping delimiters
    entry_dict = {entry.split('{')[1].split(',')[0].strip(): entry for entry in entries[::2]}
    
    ordered_entries = []
    for key in citation_order:
        if key in entry_dict:
            ordered_entries.append(entry_dict[key])
    
    return '\n\n'.join(ordered_entries)

def process_document(text_file, json_file, bib_file, output_dir):
    # Load input files
    text_content = load_text(text_file)
    replacements = load_json(json_file)
    bibtex_content = load_text(bib_file)

    # Perform replacements
    modified_text = replace_citations(text_content, replacements)

    # Save modified text
    output_text_file = os.path.join(output_dir, 'IoT_ML_ReviewPaper_NumericCitations.txt')
    save_text(modified_text, output_text_file)

    # Extract citation order
    citation_order = [rep['bibtex_keys'][0] for rep in replacements]

    # Reorder BibTeX entries
    ordered_bibtex = reorder_bibtex(bibtex_content, citation_order)

    # Save reordered BibTeX
    output_bib_file = os.path.join(output_dir, 'IoT_ML_ReviewPaper_OrderedReferences.bib')
    save_text(ordered_bibtex, output_bib_file)

    print(f"Modified text saved to: {output_text_file}")
    print(f"Ordered BibTeX file saved to: {output_bib_file}")

if __name__ == "__main__":
    base_dir = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Draft14 Citation MDPI Edits"
    text_file = os.path.join(base_dir, "2025_Nsoh et al._IoT-ML_ReviewPaper_Final_v2_HNN.txt")
    json_file = os.path.join(base_dir, "citation_replacements.json")
    bib_file = os.path.join(base_dir, "My Library.bib")
    output_dir = base_dir
    
    process_document(text_file, json_file, bib_file, output_dir)