import os
import re
import asyncio
import random
import aiohttp
from aiohttp import ClientTimeout
from undetected_playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from fake_useragent import UserAgent
import logging
import sys
import json
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
from aiohttp_retry import RetryClient, ExponentialRetry
from playwright_stealth import stealth_async

class UnifiedWebScraper:
    def __init__(self, session, max_concurrent_tasks=1, initial_timeout=30, log_dir="scraper_logs"):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.user_agent = self.initialize_user_agent()
        self.browser = None
        self.session = session
        self.failed_urls = []
        self.initial_timeout = initial_timeout

        # Set up logging
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create a file handler
        log_file = os.path.join(self.log_dir, "scraper.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatting for the logs
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        if not self.logger.hasHandlers():
            self.logger.addHandler(file_handler)

        # Also log to console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("UnifiedWebScraper initialized with headful browser and enhanced stealth features.")

    def initialize_user_agent(self):
        # Predefined list of realistic user agents for better rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/605.1.15 (KHTML, like Gecko)"
            " Version/16.3 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)"
            " Version/15.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)"
            " Version/14.0 Mobile/15A5341f Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)"
            " Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
            # Add more user agents as needed
        ]
        return user_agents

    async def initialize(self):
        try:
            self.playwright = await async_playwright().start()
            args = ["--disable-blink-features=AutomationControlled"]
            # Launch browser in headful mode
            self.browser = await self.playwright.chromium.launch(headless=False, args=args)
            self.logger.info("Playwright browser initialized successfully in headful (non-headless) mode.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright browser: {str(e)}")
            raise

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.logger.info("Playwright browser closed.")
        if self.playwright:
            await self.playwright.stop()
            self.logger.info("Playwright stopped.")

    def normalize_url(self, url):
        if url.startswith("10.") or url.startswith("doi:"):
            return f"https://doi.org/{url.replace('doi:', '')}"
        parsed = urlparse(url)
        if not parsed.scheme:
            return f"http://{url}"
        return url

    async def scrape(self, url, min_words=700, max_retries=3):
        normalized_url = self.normalize_url(url)
        self.logger.info(f"Starting scrape for URL: {normalized_url}")

        for attempt in range(1, max_retries + 1):
            try:
                async with self.semaphore:
                    self.logger.info(f"Attempt {attempt} for URL: {normalized_url}")
                    content, pdf_path = await self.scrape_with_headful_playwright(normalized_url)
                    
                    if len(content.split()) >= min_words:
                        self.logger.info(f"Successfully scraped URL: {normalized_url} on attempt {attempt}.")
                        return content, pdf_path
                    else:
                        self.logger.warning(f"Content below threshold for URL: {normalized_url} on attempt {attempt}.")
                        # If content is insufficient, no point in retrying
                        break
            except Exception as e:
                self.logger.error(f"Error scraping URL: {normalized_url} on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    wait_time = random.uniform(10, 20)
                    self.logger.info(f"Waiting for {wait_time:.2f} seconds before retrying...")
                    await asyncio.sleep(wait_time)
                else:
                    self.failed_urls.append(normalized_url)
        return "", ""

    async def scrape_with_headful_playwright(self, url):
        context = await self.browser.new_context(
            user_agent=random.choice(self.user_agent),
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = await context.new_page()
        await stealth_async(page)
        try:
            self.logger.info(f"Navigating to URL: {url}")
            await page.goto(url, wait_until="networkidle", timeout=self.initial_timeout * 1000)
            
            # Handle cookie consent popups
            await self.handle_cookie_consent(page)
            
            # Simulate human-like reading time
            read_time = random.randint(60, 120)  # Wait between 1 to 2 minutes
            self.logger.info(f"Waiting for {read_time} seconds to mimic human reading time.")
            await asyncio.sleep(read_time)
            
            # Perform slow scrolling
            await self.scroll_page(page)
            
            # Extract text for word count
            content = await self.extract_text_from_page(page)
            word_count = len(content.split())
            self.logger.info(f"Extracted {word_count} words from URL: {url}")

            pdf_path = ""
            if word_count >= 700:
                # Save page as PDF
                pdf_path = await self.save_page_as_pdf(page, url)
                self.logger.info(f"Saved PDF for URL: {url} at {pdf_path}")
            else:
                self.logger.warning(f"Insufficient content to save PDF for URL: {url}")

            await page.close()
            await context.close()
            return content, pdf_path
        except PlaywrightTimeoutError:
            self.logger.warning(f"Playwright timeout for URL: {url}")
            await page.close()
            await context.close()
            raise
        except Exception as e:
            self.logger.error(f"Playwright error for URL: {url}: {str(e)}")
            await page.close()
            await context.close()
            raise

    async def handle_cookie_consent(self, page):
        consent_button_selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "a[id*='accept']",
            "a[class*='accept']",
            "button[aria-label*='accept']",
            "button[title*='accept']",
            "button:has-text('Accept')",
            "button:has-text('I Agree')",
            # Add more selectors as needed
        ]
        for selector in consent_button_selectors:
            try:
                if await page.is_visible(selector):
                    await page.click(selector, timeout=5000)
                    self.logger.info(f"Clicked cookie consent button with selector: {selector}")
                    await asyncio.sleep(random.uniform(1, 3))  # Wait after clicking
                    break
            except:
                continue

    async def scroll_page(self, page):
        self.logger.info("Starting slow scroll to mimic human behavior.")
        total_scrolls = random.randint(5, 15)
        scroll_pause = random.uniform(1, 3)  # Seconds between scrolls

        for _ in range(total_scrolls):
            try:
                await page.evaluate("window.scrollBy(0, window.innerHeight / 2)")
                self.logger.info("Scrolled down by half the viewport height.")
                await asyncio.sleep(scroll_pause)
            except Exception as e:
                self.logger.error(f"Error during scrolling: {str(e)}")
                break
        self.logger.info("Completed slow scrolling.")

    async def extract_text_from_page(self, page):
        self.logger.info("Extracting text from the page.")
        try:
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                script_or_style.decompose()
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            self.logger.error(f"Failed to extract text from page: {str(e)}")
            return ""

    async def save_page_as_pdf(self, page, url):
        sanitized_filename = self.sanitize_filename(url)
        output_folder = os.path.abspath("scraped_pdfs")
        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, sanitized_filename)
        try:
            await page.pdf(path=pdf_path, format="A4", print_background=True)
            return pdf_path
        except Exception as e:
            self.logger.error(f"Failed to save PDF for URL: {url}: {str(e)}")
            return ""

    def sanitize_filename(self, url):
        url = re.sub(r'^https?://(www\.)?', '', url)
        filename = re.sub(r'[^\w\-_\.]', '_', url)
        return filename[:255] + '.pdf'

    async def find_pdf_links(self, url):
        # Retained for compatibility, but may not be used in the new flow
        try:
            context = await self.browser.new_context(user_agent=random.choice(self.user_agent))
            page = await context.new_page()
            await stealth_async(page)
            await page.goto(url, wait_until="networkidle", timeout=self.initial_timeout * 1000)
            
            pdf_links = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('a'))
                        .filter(a => a.href.toLowerCase().includes('pdf') || a.href.toLowerCase().endsWith('.pdf'))
                        .map(a => a.href);
                }
            """)
            
            await page.close()
            await context.close()
            
            return [urljoin(url, link) for link in pdf_links]
        except Exception as e:
            self.logger.error(f"Error finding PDF links for URL: {url}: {str(e)}")
            return []

    def extract_text_from_pdf(self, pdf_bytes):
        self.logger.info("Extracting text from PDF.")
        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in document:
                text += page.get_text()
            return text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF: {str(e)}")
            return ""

    def extract_text_from_html(self, html_content):
        # Retained for compatibility, but may not be used in the new flow
        self.logger.info("Extracting text from HTML.")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for script_or_style in soup(['script', 'style', 'nav', 'footer']):
                script_or_style.decompose()
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            self.logger.error(f"Failed to extract text from HTML: {str(e)}")
            return ""

    def sanitize_filename(self, url):
        # Overridden to ensure uniqueness and filesystem compatibility
        url = re.sub(r'^https?://(www\.)?', '', url)
        filename = re.sub(r'[^\w\-_\.]', '_', url)
        return filename[:255] + '.pdf'

    def save_content(self, content, filename, output_folder):
        # Retained for compatibility, but may not be used in the new flow
        try:
            file_path = os.path.join(output_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"Content saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save content to {filename}: {str(e)}")

    def save_failed_urls(self, output_folder):
        if self.failed_urls:
            failed_file = os.path.join(output_folder, 'failed_urls.json')
            try:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_urls, f, indent=4)
                self.logger.info(f"Failed URLs saved to {failed_file}")
            except Exception as e:
                self.logger.error(f"Failed to save failed URLs: {str(e)}")

    async def process_url(self, url, output_folder, min_words=700):
        start_time = time.time()
        content, pdf_path = await self.scrape(url, min_words=min_words)
        end_time = time.time()
        scraping_time = end_time - start_time
        
        word_count = len(content.split())
        normalized_url = self.normalize_url(url)
        filename = self.sanitize_filename(normalized_url)
        
        if word_count >= min_words and pdf_path:
            self.save_content(content, filename, output_folder)  # Optionally save text as well
            self.logger.info(f"URL: {url} | Status: Success | Word count: {word_count} | Scraping time: {scraping_time:.2f}s | Saved as: {filename}")
            print(f"\nURL: {url}\nStatus: Success\nWord count: {word_count}\nScraping time: {scraping_time:.2f}s\nSaved as: {filename}\n" + "-" * 80)
            return True
        else:
            self.logger.warning(f"URL: {url} | Status: Failure (insufficient words or PDF not saved) | Word count: {word_count} | Scraping time: {scraping_time:.2f}s")
            print(f"\nURL: {url}\nStatus: Failure (insufficient words or PDF not saved)\nWord count: {word_count}\nScraping time: {scraping_time:.2f}s\n" + "-" * 80)
            return False

    async def run_scraper(self, urls, output_folder):
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.process_url(url, output_folder))
            tasks.append(task)
            # Introduce delay between processing URLs to mimic human behavior
            delay = random.uniform(30, 60)  # 30 to 60 seconds
            self.logger.info(f"Waiting for {delay:.2f} seconds before processing the next URL.")
            await asyncio.sleep(delay)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.save_failed_urls(output_folder)
        success_count = sum(1 for result in results if result is True)
        failure_count = len(urls) - success_count
        self.logger.info(f"Scraping completed. Total: {len(urls)}, Success: {success_count}, Failure: {failure_count}")
        print("\nSummary:\n" + "=" * 80)
        print(f"Total URLs scraped: {len(urls)}")
        print(f"Successful scrapes: {success_count}")
        print(f"Failed scrapes: {failure_count}")
        print(f"Results saved in: {output_folder}")

async def main():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("unified_scraper.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger(__name__)

    output_folder = os.path.abspath("scraped_content")
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"Output folder set to: {output_folder}")

    failed_urls_file = os.path.join(output_folder, 'failed_urls.json')
    if os.path.exists(failed_urls_file):
        with open(failed_urls_file, 'r', encoding='utf-8') as f:
            failed_urls = json.load(f)
        logger.info(f"Loaded {len(failed_urls)} failed URLs from previous run.")
    else:
        failed_urls = []
    initial_urls = [
        "https://doi.org/10.1371/journal.pone.0211764",
        "https://doi.org/10.1027/1016-9040/a000195",
        "https://doi.org/10.1111/j.1600-0047.2004.00296.x",
        "https://doi.org/10.1186/s12978-021-01210-y",
        "https://doi.org/10.1007/s00737-019-00956-6",
        "https://doi.org/10.1016/j.bjan.2016.03.002",
        "https://doi.org/10.1017/S1092852900008981",
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3126989/",
        "https://doi.org/10.17795/whb-34991",
        "https://doi.org/10.1037/0033-2909.98.2.310",
        "https://doi.org/10.1046/j.1365-2648.1999.01041.x"
    ]

    all_urls = initial_urls + failed_urls

    async with aiohttp.ClientSession() as session:
        scraper = UnifiedWebScraper(session=session, max_concurrent_tasks=1, initial_timeout=30)
        try:
            await scraper.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {str(e)}")
            return

        await scraper.run_scraper(all_urls, output_folder)
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
