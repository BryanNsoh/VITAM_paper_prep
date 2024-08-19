import asyncio
import json
import os
import logging
from typing import List, Dict
from async_llm_handler import Handler
from utils.bibtex_utils import get_bibtex_from_title
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Rate limiting settings
MAX_REQUESTS_PER_MINUTE = 25
REQUEST_INTERVAL = 60 / MAX_REQUESTS_PER_MINUTE

async def load_text_file(file_path: str) -> str:
    logger.info(f"Loading text file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.debug(f"Successfully loaded {len(content)} characters from {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {str(e)}")
        raise

async def analyze_reference(handler: Handler, source_text: str, reference_text: str, reference_file: str) -> Dict:
    logger.info(f"Analyzing reference: {reference_file}")
    
    prompt = f"""
    Analyze the provided source text and reference text to determine if the reference should be cited. 
    Return a JSON object with the following structure:

    {{
        "title": "Paper title",
        "authors": ["Author 1", "Author 2"],
        "year": YYYY,
        "doi": "DOI if available",
        "analysis": {{
            "include": 0 or 1,
            "section": "Section name",
            "paragraph": "First 5 words of the paragraph",
            "after_line": "First 5 words of the line",
            "explanation": "Detailed explanation of why this paper should be included, where it fits in the review, and what point it supports"
        }},
        "relevant_quotes": [
            "Quote 1",
            "Quote 2",
            "Quote 3"
        ],
        "bibtex": "BibTeX entry"
    }}
    
    Here is what a good acceptance might look like:
    
        {{
    "title": "Machine Learning Approaches for IoT Security: A Comprehensive Survey",
    "authors": ["John Doe", "Jane Smith"],
    "year": 2022,
    "doi": "10.1234/example.doi.2022",
    "analysis": {{
        "include": 1,
        "section": "Security Challenges in IoT",
        "paragraph": "One of the primary concerns",
        "after_line": "Various security threats in IoT",
        "explanation": "This paper should be included in the review as it provides a comprehensive survey of machine learning approaches specifically tailored for IoT security. It fits well in the 'Security Challenges in IoT' section, supporting the point that machine learning can be effectively used to address various security threats in IoT systems. The paper's findings on the effectiveness of different ML algorithms for threat detection and prevention would significantly strengthen our argument about the importance of advanced security measures in IoT environments."
    }},
    "relevant_quotes": [
        "Our survey reveals that supervised learning techniques, particularly deep learning models, show promising results in detecting and classifying IoT security threats.",
        "The study found that ensemble methods combining multiple ML algorithms outperform single-algorithm approaches in IoT intrusion detection systems.",
        "Despite the advantages, the survey highlights challenges in implementing ML-based security solutions in resource-constrained IoT devices, emphasizing the need for lightweight algorithms."
    ],
    "bibtex": "@article{{doe2022machine,\n  title={{Machine Learning Approaches for IoT Security: A Comprehensive Survey}},\n  author={{Doe, John and Smith, Jane}},\n  journal={{Journal of IoT Security}},\n  year={{2022}},\n  publisher={{Example Publisher}}\n}}"
    }}
    
    And here is what a good rejection might look like:
    
        {{
    "title": "Energy-Efficient Machine Learning Algorithms for IoT Devices",
    "authors": null,
    "year": null,
    "doi": null,
    "analysis": {{
        "include": 0,
        "section": "IoT and Machine Learning Integration",
        "paragraph": "Challenges in implementing ML on",
        "after_line": "Resource constraints of IoT devices",
        "explanation": "While this paper presents interesting research on energy-efficient machine learning algorithms for IoT devices, it doesn't quite meet the threshold for inclusion in our review. The paper addresses an important aspect of IoT and ML integration - the energy efficiency of ML algorithms on resource-constrained devices. However, our review already covers this topic sufficiently in the 'Challenges in implementing ML on IoT devices' subsection. 

        The paper's main contributions - a new lightweight neural network architecture and an energy-aware training method - are noteworthy, but they don't provide a significant enough advancement or novel perspective to warrant inclusion in our already comprehensive review. The energy savings reported (15-20%) are modest and in line with what we've already discussed from other sources.

        Furthermore, the paper's focus is quite narrow, dealing specifically with energy efficiency in ML algorithms, while our review aims to provide a broader overview of IoT and ML integration challenges and solutions. Including this paper might skew the balance of our review towards energy efficiency at the expense of other equally important aspects.

        In summary, while the paper is of good quality and relevant to our topic, its contributions are not sufficiently novel or impactful to justify expanding our already well-rounded review. It would be more appropriate to reference this work in a more specialized survey focusing specifically on energy efficiency in IoT-based machine learning systems."
    }},
    "relevant_quotes": null,
    "bibtex": null
    }}
    
    It is just as important to reject references as it is to accept them.

    Instructions:
    1. Be extremely selective about including references. The default decision should be to reject unless the reference adds substantial, novel information to the source text.
    2. If you decide not to include the reference (analysis.include = 0), set ALL fields except "title" and "analysis" to null. This includes authors, year, doi, relevant_quotes, and bibtex.
    3. The analysis field should always be filled, regardless of the inclusion decision.
    4. If including the reference, provide exactly 3 relevant quotes from the reference text to support its inclusion.
    5. In the analysis, clearly state the section, paragraph (first 5 words), and line (first 5 words) where the reference should be inserted.
    6. In the explanation, provide a detailed rationale for including the paper, specifying where it fits in the review and what point it supports.

    Your task is to enhance the source text with only the most pertinent and impactful references. Reject any reference that doesn't significantly strengthen or expand upon the source text's content.

    Source text:
    {source_text}

    Reference text:
    {reference_text}
    """

    try:
        response = await handler.query(prompt, model="gpt_4o_mini", json_mode=True)
        result = json.loads(response)
        logger.debug(f"Successfully analyzed reference: {reference_file}")
    except Exception as e:
        logger.error(f"Error analyzing reference {reference_file}: {str(e)}")
        return None

    if result['analysis']['include'] == 0:
        logger.info(f"Reference rejected: {reference_file}")
        result = {
            "title": result.get('title'),
            "authors": None,
            "year": None,
            "doi": None,
            "analysis": result['analysis'],
            "relevant_quotes": None,
            "bibtex": None
        }
    elif result.get('title') and result.get('authors') and result.get('year'):
        logger.info(f"Reference accepted: {reference_file}")
        try:
            result['bibtex'] = get_bibtex_from_title(result['title'], result['authors'], result['year'])
        except Exception as e:
            logger.warning(f"Failed to generate BibTeX for {result['title']}: {str(e)}")
    
    return result

async def process_references(source_file: str, reference_folder: str, output_file: str):
    logger.info("Starting reference processing")
    handler = Handler()
    
    try:
        source_text = await load_text_file(source_file)
    except Exception as e:
        logger.error(f"Failed to load source text. Aborting process. Error: {str(e)}")
        return

    reference_files = [f for f in os.listdir(reference_folder) if f.endswith('.txt')]
    logger.info(f"Found {len(reference_files)} reference files to process")

    results = []
    for ref_file in reference_files:
        ref_path = os.path.join(reference_folder, ref_file)
        try:
            ref_text = await load_text_file(ref_path)
            result = await analyze_reference(handler, source_text, ref_text, ref_file)
            if result is not None:
                results.append(result)
            await asyncio.sleep(REQUEST_INTERVAL)  # Rate limiting
        except Exception as e:
            logger.error(f"Error processing reference file {ref_file}: {str(e)}")

    accepted_results = [result for result in results if result['analysis']['include'] == 1]
    logger.info(f"Accepted {len(accepted_results)} out of {len(results)} references")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(accepted_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results written to {output_file}")
    except Exception as e:
        logger.error(f"Error writing results to {output_file}: {str(e)}")

if __name__ == "__main__":
    source_file = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\Draft7\full_papers\source_text.txt.txt"
    reference_folder = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\Draft7\full_papers"
    output_file = os.path.join(reference_folder, "citation_analysis.json")

    logger.info("Citation analyzer started")
    asyncio.run(process_references(source_file, reference_folder, output_file))
    logger.info("Citation analyzer finished")