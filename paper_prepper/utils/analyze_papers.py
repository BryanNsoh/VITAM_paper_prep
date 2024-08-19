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


class DocumentType(BaseModel):
    research_study: int = Field(description="Set to 1 if this is primarily an original research study presenting new data or findings. This should be the core focus, not just a minor component.")
    review_paper: int = Field(description="Set to 1 if the paper's main purpose is to comprehensively review and synthesize existing literature. It should provide a broad overview of the field, not just a brief literature review section.")
    standards_and_guidelines: int = Field(description="Set to 1 if the paper's primary focus is on establishing, discussing, or analyzing standards or guidelines in the field. This should be the main thrust of the paper, not a passing mention.")
    conference_proceeding: int = Field(description="Set to 1 if this is a conference paper or proceeding. Look for explicit mentions of being presented at or prepared for a conference.")
    thesis_or_dissertation: int = Field(description="Set to 1 if this is clearly identified as a thesis or dissertation. This should be obvious from the document structure or explicit statements.")
    industry_report: int = Field(description="Set to 1 if this is primarily a report produced by or for industry, focusing on practical applications or market analysis rather than academic research.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't fit into any of the above categories. This should be rare; carefully consider all other options first.")

class AdjacentFields(BaseModel):
    general_iot: int = Field(description="Set to 1 if the paper significantly focuses on IoT concepts beyond just irrigation, such as broader agricultural or industrial IoT applications.")
    general_ml: int = Field(description="Set to 1 if the paper delves deeply into machine learning concepts beyond their specific application to irrigation, discussing ML theory or broad applications.")
    cybersecurity: int = Field(description="Set to 1 if the paper substantially addresses cybersecurity issues in smart agriculture. This should be a major focus, not just a passing mention of security concerns.")
    data_analytics: int = Field(description="Set to 1 if the paper significantly focuses on data analytics techniques or challenges in agriculture, beyond just basic data processing for irrigation.")
    environmental_monitoring: int = Field(description="Set to 1 if the paper puts significant emphasis on environmental monitoring in agriculture, beyond just the factors directly related to irrigation.")
    crop_science: int = Field(description="Set to 1 if the paper delves deeply into crop science aspects, such as plant physiology or crop responses, not just mentioning crops in the context of irrigation.")
    not_applicable: int = Field(description="Set to 1 ONLY if none of the above fields are a significant focus of the paper.")

class PrimaryResearchFocus(BaseModel):
    automated_irrigation_systems: int = Field(description="Set to 1 if the paper's primary focus is on the development, implementation, or analysis of automated irrigation systems. This should be a central theme, not just a mention of automation.")
    iot_in_irrigation: int = Field(description="Set to 1 if the paper primarily discusses the application of IoT technologies specifically in irrigation contexts. This should be a major focus, not just a brief mention of IoT use.")
    ml_in_irrigation: int = Field(description="Set to 1 if the paper's main thrust is about applying machine learning techniques to irrigation problems or data. This should be a central theme, not just a passing reference to ML.")
    combined_iot_and_ml_in_irrigation: int = Field(description="Set to 1 if the paper specifically focuses on the integration of both IoT and ML technologies in irrigation systems. Both aspects should be substantially discussed.")
    irrigation_scheduling: int = Field(description="Set to 1 if the paper primarily deals with methods, algorithms, or systems for determining when and how much to irrigate. This should be a central focus, not just a mention of scheduling.")
    sensor_technologies_for_irrigation: int = Field(description="Set to 1 if the paper's main focus is on sensor technologies specifically used in irrigation systems. This should involve substantial discussion of sensor types, implementations, or data.")
    water_management_in_agriculture: int = Field(description="Set to 1 if the paper primarily addresses broader water management issues in agriculture, beyond just irrigation. This could include water conservation, runoff management, etc.")
    precision_agriculture_non_irrigation: int = Field(description="Set to 1 if the paper focuses on precision agriculture techniques not directly related to irrigation, such as precision fertilization or pest management.")
    adjacent_fields: AdjacentFields
    not_applicable: int = Field(description="Set to 1 ONLY if none of the above categories accurately capture the primary focus of the paper. This should be used rarely, as most papers in this field will fit one of the above categories.")

class AutomationLevel(BaseModel):
    fully_automated: int = Field(description="Set to 1 if the paper primarily discusses or proposes fully automated irrigation systems that require minimal to no human intervention for regular operation.")
    partially_automated: int = Field(description="Set to 1 if the paper mainly focuses on systems that automate some aspects of irrigation but still require significant human oversight or input.")
    manual: int = Field(description="Set to 1 if the paper primarily deals with manual irrigation methods or systems, or if it's comparing manual methods to automated ones.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't substantially discuss the level of automation in irrigation systems.")

class IrrigationSystemFocus(BaseModel):
    drip: int = Field(description="Set to 1 if the paper significantly focuses on drip irrigation systems or techniques.")
    sprinkler: int = Field(description="Set to 1 if the paper significantly focuses on sprinkler irrigation systems or techniques.")
    surface: int = Field(description="Set to 1 if the paper significantly focuses on surface irrigation methods (e.g., flood irrigation).")
    center_pivot: int = Field(description="Set to 1 if the paper significantly focuses on center pivot irrigation systems.")
    subsurface: int = Field(description="Set to 1 if the paper significantly focuses on subsurface irrigation methods.")
    micro_irrigation: int = Field(description="Set to 1 if the paper significantly focuses on micro-irrigation techniques other than drip irrigation.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't focus on any specific irrigation system type or if irrigation systems are not a significant part of the paper's discussion.")

class MLTechniques(BaseModel):
    neural_networks: int = Field(description="Set to 1 if the paper significantly discusses or applies neural network techniques, including deep learning, in the context of irrigation or related agricultural problems.")
    deep_learning: int = Field(description="Set to 1 if the paper specifically focuses on deep learning methods (a subset of neural networks) for irrigation-related tasks.")
    support_vector_machines: int = Field(description="Set to 1 if the paper significantly discusses or applies support vector machines in irrigation-related analysis or decision making.")
    random_forests: int = Field(description="Set to 1 if the paper significantly uses or discusses random forest algorithms for irrigation-related predictions or classifications.")
    reinforcement_learning: int = Field(description="Set to 1 if the paper applies reinforcement learning techniques to irrigation control or optimization problems.")
    fuzzy_logic: int = Field(description="Set to 1 if the paper significantly incorporates fuzzy logic methods in irrigation decision making or system design.")
    regression_models: int = Field(description="Set to 1 if the paper heavily utilizes regression models (linear, nonlinear, logistic, etc.) for irrigation-related predictions or analysis.")
    bayesian_networks: int = Field(description="Set to 1 if the paper significantly applies Bayesian network models to irrigation-related problems or decision making.")
    genetic_algorithms: int = Field(description="Set to 1 if the paper uses genetic algorithms or other evolutionary computation techniques for optimizing irrigation systems or schedules.")
    ensemble_methods: int = Field(description="Set to 1 if the paper focuses on ensemble learning methods, combining multiple ML techniques for irrigation-related tasks.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or apply any machine learning techniques in the context of irrigation or agriculture.")

class Sensors(BaseModel):
    soil_moisture: int = Field(description="Set to 1 if the paper significantly discusses or utilizes soil moisture sensors in irrigation systems or agricultural monitoring.")
    temperature: int = Field(description="Set to 1 if the paper significantly incorporates temperature sensors for irrigation control or agricultural monitoring.")
    humidity: int = Field(description="Set to 1 if the paper significantly uses humidity sensors in irrigation decision making or environmental monitoring.")
    precipitation: int = Field(description="Set to 1 if the paper significantly incorporates precipitation sensors or rain gauges in irrigation systems or water management.")
    leaf_wetness: int = Field(description="Set to 1 if the paper significantly discusses or uses leaf wetness sensors for irrigation control or disease management.")
    sap_flow: int = Field(description="Set to 1 if the paper significantly utilizes sap flow sensors for monitoring plant water use or stress.")
    spectral: int = Field(description="Set to 1 if the paper significantly incorporates spectral sensors (e.g., multispectral or hyperspectral) for crop or soil monitoring related to irrigation.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or use any specific sensor types in the context of irrigation or agricultural monitoring.")

class CommunicationProtocols(BaseModel):
    lora: int = Field(description="Set to 1 if the paper significantly discusses or implements LoRa (Long Range) communication protocol in IoT-based irrigation systems.")
    zigbee: int = Field(description="Set to 1 if the paper significantly incorporates ZigBee protocol in the design or implementation of irrigation control systems.")
    wifi: int = Field(description="Set to 1 if the paper significantly uses Wi-Fi for communication in irrigation systems or agricultural IoT applications.")
    cellular: int = Field(description="Set to 1 if the paper significantly discusses or implements cellular networks (e.g., 3G, 4G, 5G) for irrigation system communication.")
    satellite: int = Field(description="Set to 1 if the paper significantly incorporates satellite communication in irrigation systems or for agricultural data transmission.")
    bluetooth: int = Field(description="Set to 1 if the paper significantly uses Bluetooth technology in irrigation control or monitoring systems.")
    nfc: int = Field(description="Set to 1 if the paper significantly discusses or implements Near Field Communication (NFC) in irrigation or agricultural management systems.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or implement any specific communication protocols in the context of irrigation systems or agricultural IoT.")

class DataProcessing(BaseModel):
    edge_computing: int = Field(description="Set to 1 if the paper significantly focuses on edge computing techniques for processing irrigation or agricultural data close to the source.")
    fog_computing: int = Field(description="Set to 1 if the paper significantly discusses fog computing approaches for distributed processing of irrigation or agricultural data.")
    cloud_computing: int = Field(description="Set to 1 if the paper significantly incorporates cloud computing for processing, storing, or analyzing irrigation or agricultural data.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss any specific data processing paradigms in the context of irrigation or agricultural systems.")

class IoTTechnologies(BaseModel):
    sensors: Sensors
    communication_protocols: CommunicationProtocols
    data_processing: DataProcessing
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or implement any IoT technologies in the context of irrigation or agriculture.")

class DataSources(BaseModel):
    in_situ_sensors: int = Field(description="Set to 1 if the paper significantly utilizes data from sensors deployed directly in the field or irrigation system.")
    remote_sensing: int = Field(description="Set to 1 if the paper significantly incorporates remote sensing data (e.g., satellite or drone imagery) for irrigation management or agricultural monitoring.")
    weather_forecasts: int = Field(description="Set to 1 if the paper significantly uses weather forecast data for irrigation planning or decision making.")
    historical_data: int = Field(description="Set to 1 if the paper significantly incorporates historical data (e.g., past weather patterns, crop yields) in irrigation management or analysis.")
    farmer_input: int = Field(description="Set to 1 if the paper significantly considers farmer input or local knowledge as a data source for irrigation decision making.")
    soil_maps: int = Field(description="Set to 1 if the paper significantly uses soil map data for irrigation planning or management.")
    crop_models: int = Field(description="Set to 1 if the paper significantly incorporates crop growth models or simulations as a data source for irrigation management.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or use any specific data sources for irrigation management or agricultural monitoring.")

class EvaluationMetrics(BaseModel):
    water_use_efficiency: int = Field(description="Set to 1 if the paper significantly discusses or measures water use efficiency as a key metric for evaluating irrigation systems or strategies.")
    crop_yield: int = Field(description="Set to 1 if the paper significantly uses crop yield as a metric for assessing the effectiveness of irrigation methods or systems.")
    energy_consumption: int = Field(description="Set to 1 if the paper significantly considers energy consumption as a metric for evaluating irrigation systems or strategies.")
    economic_performance: int = Field(description="Set to 1 if the paper significantly evaluates the economic aspects or cost-effectiveness of irrigation systems or methods.")
    environmental_impact: int = Field(description="Set to 1 if the paper significantly assesses the environmental impact of irrigation practices or systems.")
    system_reliability: int = Field(description="Set to 1 if the paper significantly evaluates the reliability or robustness of irrigation systems or technologies.")
    user_adoption: int = Field(description="Set to 1 if the paper significantly considers user adoption rates or factors affecting adoption of irrigation technologies.")
    water_stress_index: int = Field(description="Set to 1 if the paper significantly uses or discusses water stress indices for plants as a metric for irrigation management.")
    irrigation_uniformity: int = Field(description="Set to 1 if the paper significantly evaluates the uniformity of water application in irrigation systems.")
    soil_moisture_content: int = Field(description="Set to 1 if the paper significantly uses soil moisture content as a key metric for irrigation control or evaluation.")
    nutrient_use_efficiency: int = Field(description="Set to 1 if the paper significantly considers nutrient use efficiency in relation to irrigation practices or systems.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or use any specific evaluation metrics for irrigation systems or practices.")

class ChallengesAddressed(BaseModel):
    data_quality_and_reliability: int = Field(description="Set to 1 if the paper significantly addresses challenges related to ensuring the quality and reliability of data used in irrigation systems.")
    system_interoperability: int = Field(description="Set to 1 if the paper significantly discusses challenges or solutions related to making different irrigation system components or technologies work together.")
    scalability: int = Field(description="Set to 1 if the paper significantly addresses challenges related to scaling up irrigation technologies or systems to larger areas or more diverse conditions.")
    cost_effectiveness: int = Field(description="Set to 1 if the paper significantly discusses challenges or solutions related to making irrigation systems more cost-effective or economically viable.")
    farmer_adoption: int = Field(description="Set to 1 if the paper significantly addresses challenges related to farmer adoption of new irrigation technologies or practices.")
    energy_efficiency: int = Field(description="Set to 1 if the paper significantly discusses challenges or solutions related to improving the energy efficiency of irrigation systems.")
    cybersecurity: int = Field(description="Set to 1 if the paper significantly addresses cybersecurity challenges or solutions for IoT-based irrigation systems.")
    environmental_variability: int = Field(description="Set to 1 if the paper significantly discusses challenges related to dealing with environmental variability or climate change in irrigation management.")
    data_integration: int = Field(description="Set to 1 if the paper significantly addresses challenges related to integrating data from various sources in irrigation decision making or management.")
    real_time_decision_making: int = Field(description="Set to 1 if the paper significantly discusses challenges or solutions related to real-time decision making in irrigation systems.")
    water_scarcity: int = Field(description="Set to 1 if the paper significantly addresses challenges related to irrigation in water-scarce environments.")
    climate_change_adaptation: int = Field(description="Set to 1 if the paper significantly discusses how irrigation systems or practices can adapt to climate change.")
    regulatory_compliance: int = Field(description="Set to 1 if the paper significantly addresses challenges related to complying with water use regulations or policies in irrigation.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly address any of the above challenges in the context of irrigation or smart agriculture.")

class ImplementationScale(BaseModel):
    laboratory: int = Field(description="Set to 1 if the paper primarily focuses on laboratory-scale experiments or simulations related to irrigation systems.")
    greenhouse: int = Field(description="Set to 1 if the paper significantly discusses irrigation systems or techniques implemented in greenhouse environments.")
    small_field: int = Field(description="Set to 1 if the paper focuses on irrigation implementations in small field settings (e.g., experimental plots).")
    large_field: int = Field(description="Set to 1 if the paper discusses irrigation systems or techniques implemented in large-scale field environments.")
    commercial_farm: int = Field(description="Set to 1 if the paper significantly focuses on irrigation systems or techniques implemented in commercial farm settings.")
    regional: int = Field(description="Set to 1 if the paper addresses irrigation management or systems at a regional scale (e.g., watershed level).")
    theoretical_model: int = Field(description="Set to 1 if the paper primarily presents theoretical models or simulations without field implementation.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't specify or focus on any particular implementation scale for the irrigation systems or techniques discussed.")

class DecisionMaking(BaseModel):
    real_time: int = Field(description="Set to 1 if the paper significantly focuses on real-time decision making for irrigation control or management.")
    hourly: int = Field(description="Set to 1 if the paper discusses irrigation decision making or control on an hourly basis.")
    daily: int = Field(description="Set to 1 if the paper significantly focuses on daily irrigation decision making or scheduling.")
    weekly: int = Field(description="Set to 1 if the paper discusses irrigation decision making or planning on a weekly basis.")
    seasonal: int = Field(description="Set to 1 if the paper significantly addresses seasonal irrigation planning or decision making.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss any specific time scale for irrigation decision making.")

class DataCollectionFrequency(BaseModel):
    soil: int = Field(description="Set to 1 if the paper specifies the frequency of soil data collection (e.g., soil moisture, temperature). If multiple frequencies, choose the most prominent.")
    weather: int = Field(description="Set to 1 if the paper specifies the frequency of weather data collection. If multiple frequencies, choose the most prominent.")
    crop: int = Field(description="Set to 1 if the paper specifies the frequency of crop data collection (e.g., growth stage, stress indicators). If multiple frequencies, choose the most prominent.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't specify data collection frequency for soil, weather, or crop monitoring.")

class DataCollection(BaseModel):
    continuous: DataCollectionFrequency
    hourly: DataCollectionFrequency
    daily: DataCollectionFrequency
    weekly: DataCollectionFrequency
    monthly: DataCollectionFrequency
    seasonal: DataCollectionFrequency
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't discuss specific data collection frequencies for irrigation-related parameters.")

class TemporalResolution(BaseModel):
    decision_making: DecisionMaking
    data_collection: DataCollection
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't address temporal aspects of decision making or data collection in irrigation systems.")

class SystemIntegration(BaseModel):
    fully_integrated_with_farm_management: int = Field(description="Set to 1 if the paper discusses irrigation systems that are fully integrated with broader farm management systems or practices.")
    partially_integrated: int = Field(description="Set to 1 if the paper focuses on irrigation systems that have some level of integration with other farm management aspects, but not full integration.")
    standalone: int = Field(description="Set to 1 if the paper primarily discusses standalone irrigation systems without significant integration with other farm management systems.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't address the level of integration between irrigation systems and broader farm management practices.")

class InteroperabilityStandardsFocus(BaseModel):
    iso_11783: int = Field(description="Set to 1 if the paper significantly discusses or implements the ISO 11783 (ISOBUS) standard for agricultural equipment communication.")
    agroxml: int = Field(description="Set to 1 if the paper significantly focuses on or uses agroXML for agricultural data exchange in irrigation systems.")
    sensorml: int = Field(description="Set to 1 if the paper significantly discusses or uses SensorML for describing sensors or sensor data in irrigation systems.")
    ogc_sensorthings_api: int = Field(description="Set to 1 if the paper significantly focuses on or implements the OGC SensorThings API for IoT in agricultural or irrigation contexts.")
    mqtt: int = Field(description="Set to 1 if the paper significantly discusses or uses MQTT (Message Queuing Telemetry Transport) protocol in irrigation or agricultural IoT systems.")
    coap: int = Field(description="Set to 1 if the paper significantly focuses on or uses CoAP (Constrained Application Protocol) in irrigation or agricultural IoT systems.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't significantly discuss or implement any specific interoperability standards in the context of irrigation or agricultural systems.")

class CropFocus(BaseModel):
    cereals: int = Field(description="Set to 1 if the paper significantly focuses on irrigation for cereal crops (e.g., wheat, rice, corn).")
    vegetables: int = Field(description="Set to 1 if the paper significantly addresses irrigation for vegetable crops.")
    fruits: int = Field(description="Set to 1 if the paper significantly focuses on irrigation for fruit crops.")
    nuts: int = Field(description="Set to 1 if the paper significantly discusses irrigation for nut crops.")
    oilseeds: int = Field(description="Set to 1 if the paper significantly addresses irrigation for oilseed crops (e.g., soybeans, sunflowers).")
    fiber_crops: int = Field(description="Set to 1 if the paper significantly focuses on irrigation for fiber crops (e.g., cotton).")
    forage_crops: int = Field(description="Set to 1 if the paper significantly discusses irrigation for forage or pasture crops.")
    not_applicable: int = Field(description="Set to 1 ONLY if the paper doesn't focus on irrigation for any specific crop types or if crop type is not a significant aspect of the paper's discussion.")

class PaperAnalysis(BaseModel):
    reasoning: str = Field(description="Provide a comprehensive, step-by-step explanation of your classification decisions. Include specific evidence from the paper that led to each classification, especially for fields marked as 1. Explain why certain elements did not meet the threshold for a positive classification. Your reasoning should reflect the rigorous analysis and high standards applied in this classification process.")
    document_type: DocumentType
    primary_research_focus: PrimaryResearchFocus
    automation_level: AutomationLevel
    irrigation_system_focus: IrrigationSystemFocus
    ml_techniques: MLTechniques
    iot_technologies: IoTTechnologies
    data_sources: DataSources
    evaluation_metrics: EvaluationMetrics
    challenges_addressed: ChallengesAddressed
    implementation_scale: ImplementationScale
    temporal_resolution: TemporalResolution
    system_integration: SystemIntegration
    interoperability_standards_focus: InteroperabilityStandardsFocus
    crop_focus: CropFocus


def generate_structure_description(model):
    description = []
    for field_name, field in model.model_fields.items():
        if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
            description.append(f"{field_name}:")
            for subfield, subfield_info in field.annotation.model_fields.items():
                description.append(f"  {subfield}: {subfield_info.description}")
        else:
            description.append(f"{field_name}: {field.description}")
    return "\n".join(description)

structure_description = generate_structure_description(PaperAnalysis)

# Prompt
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

Your analysis must follow this structure, adhering strictly to the descriptions provided:

{structure_description}

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
            structure_description=structure_description
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