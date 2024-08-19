# paper_prepper/utils/process_batch_responses.py

import json
import sqlite3
import os
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_user_input(prompt: str, default: str = None) -> str:
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("This field is required. Please enter a value.")

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def find_files(working_dir):
    db_file = None
    output_file = None
    for file in os.listdir(working_dir):
        if file.endswith('.db'):
            db_file = os.path.join(working_dir, file)
        elif 'output' in file.lower() and file.endswith('.jsonl'):
            output_file = os.path.join(working_dir, file)
    return db_file, output_file

def update_paper_analysis(cursor: sqlite3.Cursor, paper_id: str, flattened_content: dict):
    cursor.execute("PRAGMA table_info(papers)")
    existing_columns = set(row[1] for row in cursor.fetchall())

    valid_keys = [k for k in flattened_content.keys() if k in existing_columns]

    if not valid_keys:
        logger.warning(f"No valid keys found for paper_id {paper_id}. Skipping update.")
        return

    update_query = "UPDATE papers SET " + ", ".join(f"{k} = ?" for k in valid_keys) + " WHERE id = ?"
    values = [flattened_content[k] for k in valid_keys] + [paper_id]

    logger.debug(f"Update query: {update_query}")
    logger.debug(f"Values: {values}")

    try:
        cursor.execute(update_query, values)
    except sqlite3.OperationalError as e:
        logger.error(f"SQLite error: {e}")
        logger.error(f"Query: {update_query}")
        logger.error(f"Values: {values}")
        raise

def process_batch_responses(output_file_path: str, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(output_file_path, 'r') as file:
        for line in file:
            try:
                response = json.loads(line)
                paper_id = response['custom_id'].split('_')[1]
                content = json.loads(response['response']['body']['choices'][0]['message']['content'])
                
                flattened_content = flatten_dict(content)
                update_paper_analysis(cursor, paper_id, flattened_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Problematic line: {line}")
            except KeyError as e:
                logger.error(f"KeyError: {e}")
                logger.error(f"Response structure: {response}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(f"Problematic line: {line}")

    conn.commit()
    conn.close()
    logger.info("All batch responses have been processed and the database has been updated.")

def main():
    parser = argparse.ArgumentParser(description="Process batch responses and update the database.")
    parser.add_argument("--working_dir", help="Path to the working directory containing the database and output file")
    args = parser.parse_args()

    if not args.working_dir:
        args.working_dir = get_user_input("Enter the path to the working directory")

    if not os.path.isdir(args.working_dir):
        print(f"Error: The specified directory does not exist: {args.working_dir}")
        return

    db_path, output_file_path = find_files(args.working_dir)

    if not db_path:
        print(f"Error: No database file found in the directory: {args.working_dir}")
        return

    if not output_file_path:
        print(f"Error: No output file with 'output' in its name found in the directory: {args.working_dir}")
        return

    print(f"Using database: {db_path}")
    print(f"Using output file: {output_file_path}")

    process_batch_responses(output_file_path, db_path)

if __name__ == "__main__":
    main()