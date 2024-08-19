import os
import json
import time
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Tuple
import argparse


# Load environment variables
load_dotenv()

# Global variables
DB_PATH = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\source_papers\iot_ml_review.db"
DB_DIR = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\source_papers"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class DocumentTypes(BaseModel):
    research_studies: int
    review_papers: int
    standards_and_guidelines: int
    conference_proceedings: int
    theses_and_dissertations: int
    industry_reports: int
    not_applicable: int

class AdjacentFields(BaseModel):
    general_iot: int
    general_ml: int
    cybersecurity: int
    data_analytics: int
    environmental_monitoring: int
    crop_science: int
    not_applicable: int

class PrimaryResearchFocus(BaseModel):
    automated_irrigation_systems: int
    iot_in_irrigation: int
    ml_in_irrigation: int
    combined_iot_and_ml_in_irrigation: int
    irrigation_scheduling: int
    sensor_technologies_for_irrigation: int
    water_management_in_agriculture: int
    precision_agriculture_non_irrigation: int
    adjacent_fields: AdjacentFields
    not_applicable: int

class AutomationLevel(BaseModel):
    fully_automated: int
    partially_automated: int
    manual: int
    not_applicable: int

class IrrigationSystemsStudied(BaseModel):
    drip: int
    sprinkler: int
    surface: int
    center_pivot: int
    subsurface: int
    micro_irrigation: int
    not_applicable: int

class MLTechniques(BaseModel):
    neural_networks: int
    deep_learning: int
    support_vector_machines: int
    random_forests: int
    reinforcement_learning: int
    fuzzy_logic: int
    regression_models: int
    bayesian_networks: int
    genetic_algorithms: int
    ensemble_methods: int
    not_applicable: int

class Sensors(BaseModel):
    soil_moisture: int
    temperature: int
    humidity: int
    precipitation: int
    leaf_wetness: int
    sap_flow: int
    spectral: int
    not_applicable: int

class CommunicationProtocols(BaseModel):
    lora: int
    zigbee: int
    wifi: int
    cellular: int
    satellite: int
    bluetooth: int
    nfc: int
    not_applicable: int

class DataProcessing(BaseModel):
    edge_computing: int
    fog_computing: int
    cloud_computing: int
    not_applicable: int

class IoTTechnologies(BaseModel):
    sensors: Sensors
    communication_protocols: CommunicationProtocols
    data_processing: DataProcessing
    not_applicable: int

class DataSources(BaseModel):
    in_situ_sensors: int
    remote_sensing: int
    weather_forecasts: int
    historical_data: int
    farmer_input: int
    soil_maps: int
    crop_models: int
    not_applicable: int

class EvaluationMetrics(BaseModel):
    water_use_efficiency: int
    crop_yield: int
    energy_consumption: int
    economic_performance: int
    environmental_impact: int
    system_reliability: int
    user_adoption: int
    water_stress_index: int
    irrigation_uniformity: int
    soil_moisture_content: int
    nutrient_use_efficiency: int
    not_applicable: int

class ChallengesAddressed(BaseModel):
    data_quality_and_reliability: int
    system_interoperability: int
    scalability: int
    cost_effectiveness: int
    farmer_adoption: int
    energy_efficiency: int
    cybersecurity: int
    environmental_variability: int
    data_integration: int
    real_time_decision_making: int
    water_scarcity: int
    climate_change_adaptation: int
    regulatory_compliance: int
    not_applicable: int

class ImplementationScale(BaseModel):
    laboratory: int
    greenhouse: int
    small_field: int
    large_field: int
    commercial_farm: int
    regional: int
    theoretical_model: int
    not_applicable: int

class DecisionMaking(BaseModel):
    real_time: int
    hourly: int
    daily: int
    weekly: int
    seasonal: int
    not_applicable: int

class DataCollectionFrequency(BaseModel):
    soil: int
    weather: int
    crop: int
    not_applicable: int

class DataCollection(BaseModel):
    continuous: DataCollectionFrequency
    hourly: DataCollectionFrequency
    daily: DataCollectionFrequency
    weekly: DataCollectionFrequency
    monthly: DataCollectionFrequency
    seasonal: DataCollectionFrequency
    not_applicable: int

class TemporalResolution(BaseModel):
    decision_making: DecisionMaking
    data_collection: DataCollection
    not_applicable: int

class SystemIntegration(BaseModel):
    fully_integrated_with_farm_management: int
    partially_integrated: int
    standalone: int
    not_applicable: int

class InteroperabilityStandardsMentioned(BaseModel):
    iso_11783: int
    agroxml: int
    sensorml: int
    ogc_sensorthings_api: int
    mqtt: int
    coap: int
    not_applicable: int

class CropsStudied(BaseModel):
    cereals: int
    vegetables: int
    fruits: int
    nuts: int
    oilseeds: int
    fiber_crops: int
    forage_crops: int
    not_applicable: int

class PaperAnalysis(BaseModel):
    reasoning: str
    total_documents_reviewed: int
    document_types: DocumentTypes
    primary_research_focus: PrimaryResearchFocus
    automation_level: AutomationLevel
    irrigation_systems_studied: IrrigationSystemsStudied
    ml_techniques: MLTechniques
    iot_technologies: IoTTechnologies
    data_sources: DataSources
    evaluation_metrics: EvaluationMetrics
    challenges_addressed: ChallengesAddressed
    implementation_scale: ImplementationScale
    temporal_resolution: TemporalResolution
    system_integration: SystemIntegration
    interoperability_standards_mentioned: InteroperabilityStandardsMentioned
    crops_studied: CropsStudied

# Prompts
ANALYSIS_PROMPT = """
You are an expert at analyzing research papers in the field of agriculture, focusing on irrigation, IoT, and machine learning applications. Your task is to extract key information and classify the paper based on its content with ABSOLUTE CERTAINTY and UTMOST RIGOR.

CRITICAL INSTRUCTIONS:
1. CERTAINTY: Only classify a field as 1 if you are 100% certain it is a MAJOR and PRIMARY focus of the paper. If there's ANY doubt whatsoever, classify as 0.
2. PRIMARY FOCUS: A field must be a central, substantial component of the paper to be classified as 1. Mere mentions or tangential references MUST be classified as 0.
3. REVIEW PAPERS: Only classify as a review paper if its SOLE PURPOSE is to review and synthesize existing literature. Papers with introductory literature reviews do NOT qualify as review papers.
4. DEFAULT TO ZERO: If you're not ABSOLUTELY CERTAIN about a classification, it MUST be 0. NO exceptions.
5. NO PARTIAL CLASSIFICATIONS: There is no middle ground. Each field is either a 1 (absolutely certain, primary focus) or a 0 (anything less than absolute certainty).
6. THRESHOLD FOR CLASSIFICATION: The threshold for a 1 classification is EXTREMELY HIGH. The topic must be extensively discussed, analyzed, or be a core component of the paper's methodology or results.

For each category in the structure:
- Scrutinize the paper's content rigorously.
- Only mark 1 if the category is undeniably a major focus, extensively discussed, or crucial to the paper's core argument or methodology.
- If a category is present but not a primary focus, it MUST be 0.
- 'Not applicable' should be used when the entire category is completely irrelevant to the paper's scope.

Now, analyze the following paper:

Title: {title}
Authors: {authors}
Full Text: {full_text}

The analysis must follow this structure:
{structure}

CRITICAL INSTRUCTION ON REASONING:
Use the reasoning field as a space to meticulously work through the choices you will make and why. Your reasoning must reflect your careful deliberation and unwavering commitment to the absolute rigor demanded in this task. It should be a comprehensive, step-by-step explanation of your thought process, demonstrating how you arrived at each classification with utmost certainty. Include specific evidence from the paper that led to your decisions, and explain why certain elements did not meet the extremely high threshold for a positive classification. Your reasoning should be a testament to the exhaustive analysis and uncompromising standards applied in this classification process.

FINAL REMINDER:
This analysis demands the HIGHEST level of certainty and rigor. When in doubt, classify as 0. Only use 1 for classifications that are UNDENIABLE based on the paper's primary focus and content. Your response must be a JSON object matching the provided structure, including the detailed reasoning field. The standards for this task are uncompromising - reflect this in every aspect of your analysis.
"""

def get_all_fields(model, prefix=''):
    fields = []
    for field_name, field in model.__annotations__.items():
        if isinstance(field, type) and issubclass(field, BaseModel):
            fields.extend(get_all_fields(field, f"{prefix}{field_name}_"))
        else:
            fields.append(f"{prefix}{field_name}")
    return fields

def update_table_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(papers)")
    existing_columns = set(row[1] for row in cursor.fetchall())
    
    # Get all fields from PaperAnalysis
    all_fields = get_all_fields(PaperAnalysis)
    
    # Add new columns
    for field in all_fields:
        if field not in existing_columns:
            try:
                if field == 'reasoning':
                    cursor.execute(f"ALTER TABLE papers ADD COLUMN {field} TEXT")
                else:
                    cursor.execute(f"ALTER TABLE papers ADD COLUMN {field} INTEGER DEFAULT 0")
                print(f"Added column: {field}")
            except sqlite3.OperationalError as e:
                print(f"Error adding column {field}: {e}")
    
    conn.commit()
    conn.close()

def get_all_paper_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM papers")
    paper_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return paper_ids

def get_paper_data(paper_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, authors, year, full_text FROM papers WHERE id = ?", (paper_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def wipe_previous_analysis(paper_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all fields from PaperAnalysis
    all_fields = get_all_fields(PaperAnalysis)
    
    # Create a list of field assignments
    field_assignments = [f"{field} = ?" for field in all_fields if field != 'id']
    
    # Create the update query
    update_query = f"UPDATE papers SET {', '.join(field_assignments)} WHERE id = ?"
    
    # Create a list of values (0 for integer fields, NULL for the reasoning field)
    values = [0 if field != 'reasoning' else None for field in all_fields if field != 'id']
    values.append(paper_id)
    
    # Execute the update query
    cursor.execute(update_query, values)
    
    conn.commit()
    conn.close()

def update_paper_analysis(paper_id, analysis):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    def flatten_dict(d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flattened_analysis = flatten_dict(analysis.dict())
    
    update_query = "UPDATE papers SET " + ", ".join(f"{k} = ?" for k in flattened_analysis.keys()) + " WHERE id = ?"
    cursor.execute(update_query, list(flattened_analysis.values()) + [paper_id])
    
    conn.commit()
    conn.close()

def get_paper_analysis(title, authors, full_text):
    structure = PaperAnalysis.model_json_schema()
    prompt = ANALYSIS_PROMPT.format(
        title=title, authors=authors, full_text=full_text, structure=structure
    )
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert at structured data extraction from research papers."},
            {"role": "user", "content": prompt}
        ],
        response_format=PaperAnalysis,
    )
    print(completion.choices[0].message.parsed)
    return completion.choices[0].message.parsed

def process_paper_sequentially(paper_id):
    paper_data = get_paper_data(paper_id)
    if paper_data:
        title, authors, year, full_text = paper_data
        if all((title, authors, full_text)):
            wipe_previous_analysis(paper_id)
            analysis = get_paper_analysis(title, authors, full_text)
            update_paper_analysis(paper_id, analysis)
            print(f"Processed paper {paper_id}")
        else:
            print(f"Skipping paper {paper_id} due to missing data")
    else:
        print(f"No data found for paper {paper_id}")
        
        
def prepare_batch_file(papers):
    batch_requests = []
    for paper in papers:
        structure = PaperAnalysis.model_json_schema()
        prompt = ANALYSIS_PROMPT.format(
            title=paper['title'], 
            authors=paper['authors'], 
            full_text=paper['full_text'], 
            structure=structure
        )
        
        request = {
            "custom_id": f"paper_{paper['id']}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are an expert at structured data extraction from research papers."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
        }
        batch_requests.append(json.dumps(request))
    
    batch_file_path = os.path.join(DB_DIR, 'batch_input.jsonl')
    with open(batch_file_path, 'w') as f:
        for request in batch_requests:
            f.write(f"{request}\n")
    return batch_file_path

def process_papers_batch(papers):
    # 1. Prepare batch file
    batch_file_path = prepare_batch_file(papers)
    
    # 2. Upload batch file
    with open(batch_file_path, 'rb') as f:
        batch_file = client.files.create(file=f, purpose="batch")
    
    # 3. Create batch
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    # 4. Store batch information
    batch_info = {
        "batch_id": batch.id,
        "input_file_id": batch.input_file_id,
        "status": batch.status,
        "created_at": batch.created_at,
        "paper_ids": [paper['id'] for paper in papers]
    }
    
    batch_info_path = os.path.join(DB_DIR, 'batch_info.json')
    with open(batch_info_path, 'w') as f:
        json.dump(batch_info, f, indent=2)
    
    print(f"Batch created with ID: {batch.id}")
    print(f"Batch information stored in: {batch_info_path}")
    print("You can check the batch status later using this information.")

def get_user_choice():
    while True:
        choice = input("Choose processing mode (sequential/batch): ").lower().strip()
        if choice in ['sequential', 'batch']:
            return choice
        print("Invalid choice. Please enter 'sequential' or 'batch'.")

def main():
    parser = argparse.ArgumentParser(description="Process papers using sequential or batch method.")
    parser.add_argument("--mode", choices=["sequential", "batch"],
                        help="Processing mode: 'sequential' for one-by-one or 'batch' for batch processing")
    args = parser.parse_args()

    # If mode is not provided as a command-line argument, ask the user
    if args.mode is None:
        args.mode = get_user_choice()

    update_table_schema()
    paper_ids = get_all_paper_ids()
    
    if not paper_ids:
        print("No papers found in the database. Please add papers before running analysis.")
        return

    if args.mode == "sequential":
        print("Processing papers sequentially...")
        for paper_id in paper_ids:
            process_paper_sequentially(paper_id)
        print("Sequential processing completed.")
    else:  # batch mode
        print("Processing papers in batch mode...")
        papers = []
        for paper_id in paper_ids:
            paper_data = get_paper_data(paper_id)
            if paper_data:
                title, authors, year, full_text = paper_data
                if all((title, authors, full_text)):
                    papers.append({'id': paper_id, 'title': title, 'authors': authors, 'full_text': full_text})
            else:
                print(f"Skipping paper {paper_id} due to missing data")
        
        if not papers:
            print("No valid papers found for processing. Exiting.")
            return

        print(f"Number of papers to process in batch: {len(papers)}")
        process_papers_batch(papers)
        print("Batch job submitted. You can check its status later using the information in batch_info.json")

if __name__ == "__main__":
    main()