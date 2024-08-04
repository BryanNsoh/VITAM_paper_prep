# paper_prepper/reference_processor.py

import os
import json
import shutil
from scraper import UnifiedWebScraper
import asyncio
import aiohttp

class ReferenceProcessor:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    async def process_references(self, source_paper_name):
        source_paper_dir = os.path.join(self.data_dir, source_paper_name)
        json_file = os.path.join(source_paper_dir, "references.json")

        if not os.path.exists(json_file):
            raise FileNotFoundError(f"references.json not found in {source_paper_dir}")

        with open(json_file, "r") as f:
            references = json.load(f)

        scraped_dir = os.path.join(source_paper_dir, "scraped_references")
        os.makedirs(scraped_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            scraper = UnifiedWebScraper(session=session)
            await scraper.initialize()

            for ref_name, ref_data in references.items():
                ref_dir = os.path.join(scraped_dir, ref_name)
                os.makedirs(ref_dir, exist_ok=True)

                for i, link in enumerate(ref_data["links"]):
                    content = await scraper.scrape(link)
                    with open(os.path.join(ref_dir, f"link_{i+1}.md"), "w", encoding="utf-8") as f:
                        f.write(content)

                # Find the largest markdown file for this reference
                largest_file = max(
                    (os.path.join(ref_dir, f) for f in os.listdir(ref_dir) if f.endswith('.md')),
                    key=os.path.getsize
                )

                # Move the largest file to the source paper directory
                shutil.move(largest_file, os.path.join(source_paper_dir, f"{ref_name}_full.md"))

            await scraper.close()

        print(f"Finished processing references for {source_paper_name}")

async def main():
    processor = ReferenceProcessor("data")
    
    while True:
        source_paper_name = "bergworth_sugar_cardiovascular"

        try:
            await processor.process_references(source_paper_name)
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        print("\n")  # Add a blank line for readability between runs

if __name__ == "__main__":
    asyncio.run(main())