# paper_prepper/reference_processor.py

import os
import json
import shutil
import logging
from utils.scraper import UnifiedWebScraper
import asyncio
import aiohttp
from utils.file_utils import read_file, write_file
import re

class ReferenceProcessor:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def clean_filename(filename):
        # Remove or replace characters not allowed in Windows filenames
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    async def process_references(self, source_paper_name):
        source_paper_dir = os.path.join(self.data_dir, source_paper_name)
        original_json_file = os.path.join(source_paper_dir, "references.json")
        successful_scrapes_json = os.path.join(source_paper_dir, "successful_scrapes.json")
        failed_scrapes_json = os.path.join(source_paper_dir, "failed_scrapes.json")

        if not os.path.exists(original_json_file):
            raise FileNotFoundError(f"references.json not found in {source_paper_dir}")

        # Load original references
        references = json.loads(read_file(original_json_file))

        # Load successful scrapes
        successful_scrapes = self.load_json(successful_scrapes_json, {})

        # Check if failed_scrapes.json exists
        if os.path.exists(failed_scrapes_json):
            failed_scrapes = json.loads(read_file(failed_scrapes_json))
            references_to_process = {k: v for k, v in references.items() if k in failed_scrapes}
            self.logger.info("Processing only failed scrapes from previous run.")
        else:
            failed_scrapes = {}
            references_to_process = references
            self.logger.info("Processing all references.")

        scraped_dir = os.path.join(source_paper_dir, "scraped_references")
        os.makedirs(scraped_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            scraper = UnifiedWebScraper(session=session, max_concurrent_tasks=5, initial_timeout=30)
            await scraper.initialize()

            async def process_reference(ref_name, ref_data):
                clean_ref_name = self.clean_filename(ref_name)
                ref_dir = os.path.join(scraped_dir, clean_ref_name)
                os.makedirs(ref_dir, exist_ok=True)

                successful_scrape = False
                for i, link in enumerate(ref_data["links"]):
                    try:
                        content = await scraper.scrape(link)
                        if content:
                            write_file(os.path.join(ref_dir, f"link_{i+1}.md"), content)
                            successful_scrape = True
                    except Exception as e:
                        self.logger.error(f"Error scraping link {link} for reference {clean_ref_name}: {str(e)}")

                if successful_scrape:
                    md_files = [f for f in os.listdir(ref_dir) if f.endswith('.md')]
                    if md_files:
                        largest_file = max(
                            (os.path.join(ref_dir, f) for f in md_files),
                            key=os.path.getsize
                        )
                        target_file = os.path.join(source_paper_dir, f"{clean_ref_name}_full.md")
                        shutil.move(largest_file, target_file)
                        
                        if os.path.getsize(target_file) < 60 * 1024:
                            os.remove(target_file)
                            self.logger.warning(f"Scraped content for {clean_ref_name} is less than 60KB")
                            return ref_name, {"reason": "Content less than 60KB", "links": ref_data["links"]}, None
                        else:
                            self.logger.info(f"Successfully processed reference {clean_ref_name}")
                            return ref_name, None, {"file": f"{clean_ref_name}_full.md", "size": os.path.getsize(target_file)}
                    else:
                        self.logger.warning(f"No markdown files found for reference {clean_ref_name}")
                        return ref_name, {"reason": "No markdown files created", "links": ref_data["links"]}, None
                else:
                    self.logger.warning(f"Failed to scrape any content for reference {clean_ref_name}")
                    return ref_name, {"reason": "Failed to scrape any content", "links": ref_data["links"]}, None

            tasks = [process_reference(ref_name, ref_data) for ref_name, ref_data in references_to_process.items()]
            results = await asyncio.gather(*tasks)

            for ref_name, failed_data, success_data in results:
                if failed_data:
                    failed_scrapes[ref_name] = failed_data
                    if ref_name in successful_scrapes:
                        del successful_scrapes[ref_name]
                elif success_data:
                    successful_scrapes[ref_name] = success_data
                    if ref_name in failed_scrapes:
                        del failed_scrapes[ref_name]

            await scraper.close()

        # Write updated successful and failed scrapes
        write_file(successful_scrapes_json, json.dumps(successful_scrapes, indent=2))
        if failed_scrapes:
            write_file(failed_scrapes_json, json.dumps(failed_scrapes, indent=2))
        elif os.path.exists(failed_scrapes_json):
            os.remove(failed_scrapes_json)
            self.logger.info("All failed scrapes have been successfully processed. Removed failed_scrapes.json.")

        self.logger.info(f"Finished processing references for {source_paper_name}")
        self.logger.info(f"Successful scrapes have been written to: {successful_scrapes_json}")
        if failed_scrapes:
            self.logger.info(f"Failed scrapes have been written to: {failed_scrapes_json}")

        # Check if all references have been processed
        all_processed = set(successful_scrapes.keys()).union(set(failed_scrapes.keys()))
        if all_processed == set(references.keys()):
            self.logger.info("All references have been processed. No further processing needed.")
            return False  # Indicate that no further processing is needed
        else:
            remaining = set(references.keys()) - all_processed
            self.logger.info(f"{len(remaining)} references still need processing.")
            return True  # Indicate that further processing is needed

    @staticmethod
    def load_json(file_path, default):
        if os.path.exists(file_path):
            return json.loads(read_file(file_path))
        return default

async def main():
    processor = ReferenceProcessor("data")
    
    source_paper_name = input("Enter the name of the source paper directory: ")

    try:
        needs_further_processing = await processor.process_references(source_paper_name)
        if not needs_further_processing:
            print("All references have been processed. The script will now exit.")
        else:
            print("Some references still need processing. You can run the script again to continue.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print("\nProcessing complete.")

if __name__ == "__main__":
    asyncio.run(main())