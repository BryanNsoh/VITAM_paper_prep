# paper_prepper/create_manual_entry_files.py

import os
import json
from utils.file_utils import read_file, write_file

def create_manual_entry_files(data_dir, source_paper_name):
    source_paper_dir = os.path.join(data_dir, source_paper_name)
    failed_scrapes_json = os.path.join(source_paper_dir, "failed_scrapes.json")
    references_json = os.path.join(source_paper_dir, "references.json")
    
    if not os.path.exists(failed_scrapes_json):
        print(f"No failed_scrapes.json found in {source_paper_dir}")
        return
    
    if not os.path.exists(references_json):
        print(f"No references.json found in {source_paper_dir}")
        return
    
    failed_scrapes = json.loads(read_file(failed_scrapes_json))
    all_references = json.loads(read_file(references_json))
    
    manual_entry_dir = os.path.join(source_paper_dir, "manual_entry")
    os.makedirs(manual_entry_dir, exist_ok=True)
    
    for ref_name, ref_data in failed_scrapes.items():
        file_name = f"{ref_name}_manual.txt"
        file_path = os.path.join(manual_entry_dir, file_name)
        
        title = all_references.get(ref_name, {}).get('title', 'Title not available')
        
        content = f"Reference: {ref_name}\n"
        content += f"Title: {title}\n"
        content += "Original links:\n"
        for link in ref_data['links']:
            content += f"- {link}\n"
        content += "\nPlease enter the reference content below this line:\n"
        content += "=" * 50 + "\n"
        
        write_file(file_path, content)
        print(f"Created manual entry file: {file_path}")
    
    print(f"\nCreated {len(failed_scrapes)} files for manual entry in {manual_entry_dir}")
    print("Please manually add the reference content to these files.")

if __name__ == "__main__":
    data_dir = "data"  # Adjust this if your data directory is located elsewhere
    source_paper_name = input("Enter the name of the source paper directory: ")
    create_manual_entry_files(data_dir, source_paper_name)