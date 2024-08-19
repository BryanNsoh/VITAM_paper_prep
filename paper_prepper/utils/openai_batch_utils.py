# paper_prepper/utils/openai_batch_utils.py

from openai import OpenAI
import json
import os
import time

client = OpenAI()

DB_DIR = r"C:\Users\bnsoh2\OneDrive - University of Nebraska-Lincoln\Projects\Students\Bryan Nsoh\Papers\Real-Time-IoT-ML\First_Sumbission\Final\source_papers"

def list_batches(limit=10):
    """List recent batches."""
    return client.batches.list(limit=limit)

def retrieve_batch(batch_id):
    """Retrieve a specific batch."""
    return client.batches.retrieve(batch_id)

def save_batch_results(file_id, output_filename):
    """Save batch results to a file in the specified directory."""
    file_response = client.files.content(file_id)
    
    output_path = os.path.join(DB_DIR, output_filename)
    with open(output_path, "w") as output_file:
        output_file.write(file_response.text)
    
    print(f"Batch results saved to {output_path}")

def monitor_batch_progress(batch_id, check_interval=10):
    """
    Monitor the progress of a batch job.
    
    :param batch_id: The ID of the batch to monitor.
    :param check_interval: Time in seconds between status checks.
    """
    print(f"Monitoring progress of batch {batch_id}")
    while True:
        batch = retrieve_batch(batch_id)
        print(f"Status: {batch.status}")
        
        if batch.status == "completed":
            print("Batch processing completed!")
            return batch
        elif batch.status in ["failed", "canceled"]:
            print(f"Batch processing {batch.status}.")
            return batch
        
        print(f"Checking again in {check_interval} seconds...")
        time.sleep(check_interval)

def main():
    # List recent batches
    recent_batches = list_batches(limit=10)
    print("Recent batches:")
    for i, batch in enumerate(recent_batches.data, 1):
        print(f"{i}. Batch ID: {batch.id}, Status: {batch.status}")
    
    # Ask user to select a batch
    while True:
        try:
            selection = int(input("\nEnter the number of the batch you want to retrieve (or 0 to exit): "))
            if selection == 0:
                print("Exiting the program.")
                return
            if 1 <= selection <= len(recent_batches.data):
                selected_batch = recent_batches.data[selection - 1]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    try:
        # Retrieve the specified batch
        specific_batch = retrieve_batch(selected_batch.id)
        print(f"\nRetrieved batch: {specific_batch.id}")
        print(f"Initial status: {specific_batch.status}")
        
        # Ask if the user wants to monitor progress
        monitor = input("Do you want to monitor the batch progress? (y/n): ").lower() == 'y'
        
        if monitor:
            specific_batch = monitor_batch_progress(specific_batch.id)
        
        # If the batch is completed and has an output file:
        if specific_batch.status == "completed" and specific_batch.output_file_id:
            # Ask user if they want to save the results
            save_results = input("Do you want to save the batch results? (y/n): ").lower()
            if save_results == 'y':
                output_filename = f"batch_{specific_batch.id}_output.jsonl"
                save_batch_results(specific_batch.output_file_id, output_filename)
        else:
            print("Batch is not completed or does not have output file.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()