import bibtexparser
import re
import os
from unidecode import unidecode

def clean_text(text):
    text = unidecode(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\{\}]', '', text)
    return text.strip()

def format_authors(authors, max_authors=7):
    author_list = [a.strip() for a in re.split(r'\s+and\s+', authors)]
    formatted_authors = []
    for author in author_list:
        names = author.split(',')
        if len(names) == 2:
            last_name = names[0].strip()
            first_names = names[1].strip()
            initials = ''.join(name[0].upper() + '.' for name in first_names.split() if name)
            formatted_authors.append(f"{last_name}, {initials}")
        else:
            formatted_authors.append(author)
    
    if len(formatted_authors) > max_authors:
        return ', '.join(formatted_authors[:6]) + ', et al.'
    elif len(formatted_authors) > 1:
        return ', '.join(formatted_authors[:-1]) + ', & ' + formatted_authors[-1]
    else:
        return formatted_authors[0]

def format_title(title):
    title = clean_text(title)
    return title[0].upper() + title[1:].lower()

def format_journal(journal):
    journal = clean_text(journal)
    return ' '.join(word.capitalize() for word in journal.split())

def format_pages(pages):
    return pages.replace('--', '-')

def format_doi(doi):
    return f"https://doi.org/{doi}" if doi else ''

def get_sort_key(entry):
    authors = entry.get('author', '')
    if not authors:
        return ('', entry.get('year', '9999'), entry.get('title', ''))
    first_author = authors.split(' and ')[0]
    last_name = first_author.split(',')[0] if ',' in first_author else first_author.split()[-1]
    return (last_name.lower(), entry.get('year', ''), entry.get('title', ''))

def convert_to_apa(input_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_apa.txt")

    with open(input_file, 'r', encoding='utf-8') as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser(ignore_nonstandard_types=False)
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    sorted_entries = sorted(bib_database.entries, key=get_sort_key)

    with open(output_file, 'w', encoding='utf-8') as apa_file:
        for entry in sorted_entries:
            authors = format_authors(clean_text(entry.get('author', '')))
            year = entry.get('year', 'n.d.')
            title = format_title(entry.get('title', ''))
            journal = format_journal(entry.get('journal', entry.get('booktitle', '')))
            volume = entry.get('volume', '')
            number = entry.get('number', '')
            pages = format_pages(entry.get('pages', ''))
            doi = format_doi(entry.get('doi', ''))

            if not authors:
                authors = "Unknown Author"

            citation = f"{authors} ({year}). {title}. "
            
            if journal:
                citation += f"{journal}"
                if volume:
                    citation += f", {volume}"
                    if number:
                        citation += f"({number})"
                if pages:
                    citation += f", {pages}"
            citation += "."
            
            if doi:
                citation += f" {doi}"
            
            apa_file.write(citation + "\n")

    print(f"APA citations have been written to {output_file}")

if __name__ == "__main__":
    input_file = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\Draft10\My Library.bib"
    output_dir = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\Draft10"
    convert_to_apa(input_file, output_dir)