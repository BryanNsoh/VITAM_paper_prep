import os
import re
import asyncio
import random
import aiohttp
from aiohttp import ClientTimeout
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from fake_useragent import UserAgent
import logging
import sys
import json
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import pyperclip
import time
from aiohttp_retry import RetryClient, ExponentialRetry

class UnifiedWebScraper:
    def __init__(self, session, max_concurrent_tasks=10, initial_timeout=15, log_dir="scraper_logs"):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.user_agent = UserAgent()
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
        self.logger.addHandler(file_handler)

        self.logger.info("UnifiedWebScraper initialized")

    async def initialize(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.logger.info("Playwright browser initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright browser: {str(e)}")
            raise

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.logger.info("Playwright browser closed")
        if self.playwright:
            await self.playwright.stop()
            self.logger.info("Playwright stopped")

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

        content = await self.escalating_scrape(normalized_url, min_words, max_retries)
        
        if len(content.split()) >= min_words:
            return content
        
        # If content is still below threshold, look for PDF links
        pdf_links = await self.find_pdf_links(normalized_url)
        
        if pdf_links:
            self.logger.info(f"Found {len(pdf_links)} PDF-like links for URL: {normalized_url}")
            for link in pdf_links:
                self.logger.info(f"PDF-like link found: {link}")
            
            pdf_contents = []
            for pdf_link in pdf_links:
                pdf_content = await self.escalating_scrape(pdf_link, min_words, max_retries)
                if len(pdf_content.split()) >= min_words:
                    pdf_contents.append(pdf_content)
            
            if pdf_contents:
                best_content = max(pdf_contents, key=len)
                if len(best_content.split()) >= min_words:
                    return best_content
        
        self.logger.warning(f"Failed to scrape sufficient content from URL: {normalized_url}")
        self.failed_urls.append(normalized_url)
        return ""  # Return empty string if no content meets the threshold

    async def escalating_scrape(self, url, min_words, max_retries):
        methods = [
            self.scrape_with_aiohttp,
            self.scrape_with_playwright,
            self.scrape_with_headful_playwright
        ]
        
        for method in methods:
            for attempt in range(1, max_retries + 1):
                timeout = self.initial_timeout * attempt
                try:
                    self.logger.info(f"Attempt {attempt} using {method.__name__} for URL: {url}")
                    content = await method(url, timeout)
                    word_count = len(content.split())
                    self.logger.info(f"{method.__name__} returned {word_count} words for URL: {url}")
                    if word_count >= min_words:
                        self.logger.info(f"Successfully scraped URL: {url} using {method.__name__}")
                        return content
                    else:
                        self.logger.warning(f"Scraped content below threshold for URL: {url} using {method.__name__}")
                except Exception as e:
                    self.logger.error(f"Error in {method.__name__} (attempt {attempt}) for URL: {url}: {str(e)}")

                if attempt < max_retries:
                    wait_time = random.uniform(1, 3) * attempt
                    self.logger.info(f"Waiting for {wait_time:.2f} seconds before retrying...")
                    await asyncio.sleep(wait_time)
        
        return ""  # Return empty string if all methods fail

    async def find_pdf_links(self, url):
        try:
            context = await self.browser.new_context(user_agent=self.user_agent.random)
            page = await context.new_page()
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

    async def scrape_with_aiohttp(self, url, timeout):
        headers = {"User-Agent": self.user_agent.random}
        retry_options = ExponentialRetry(attempts=3)
        async with RetryClient(retry_options=retry_options) as client:
            try:
                async with client.get(url, headers=headers, timeout=ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                            self.logger.info(f"Detected PDF content for URL: {url}")
                            pdf_bytes = await response.read()
                            return self.extract_text_from_pdf(pdf_bytes)
                        else:
                            text = await response.text()
                            return self.extract_text_from_html(text)
                    else:
                        self.logger.warning(f"Received status code {response.status} for URL: {url}")
                        return ""
            except Exception as e:
                self.logger.error(f"aiohttp request failed for URL: {url} with error: {str(e)}")
                raise

    async def scrape_with_playwright(self, url, timeout):
        context = await self.browser.new_context(
            user_agent=self.user_agent.random,
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            
            # Handle cookie consent popups
            await self.handle_cookie_consent(page)
            
            content = await page.content()
            await page.close()
            await context.close()

            # Check if content is PDF
            if 'application/pdf' in page.url.lower() or url.lower().endswith('.pdf'):
                self.logger.info(f"Playwright detected PDF content for URL: {url}")
                pdf_bytes = await self.download_pdf(url)
                return self.extract_text_from_pdf(pdf_bytes)

            return self.extract_text_from_html(content)
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

    async def scrape_with_headful_playwright(self, url, timeout):
        browser = await self.playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=self.user_agent.random,
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            
            # Handle cookie consent popups
            await self.handle_cookie_consent(page)
            
            # Scroll to load all content
            await self.scroll_page(page)
            
            # Try multiple selection strategies
            content = await self.try_multiple_selections(page)
            
            await page.close()
            await context.close()
            await browser.close()

            return content
        except Exception as e:
            self.logger.error(f"Headful Playwright error for URL: {url}: {str(e)}")
            await page.close()
            await context.close()
            await browser.close()
            raise

    async def handle_cookie_consent(self, page):
        consent_button_selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "a[id*='accept']",
            "a[class*='accept']"
        ]
        for selector in consent_button_selectors:
            try:
                await page.click(selector, timeout=5000)
                self.logger.info(f"Clicked cookie consent button with selector: {selector}")
                await asyncio.sleep(1)  # Wait for any animations to complete
                break
            except:
                pass

    async def scroll_page(self, page):
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)

    async def try_multiple_selections(self, page):
        selection_strategies = [
            self.select_all_content,
            self.select_by_main_content,
            self.select_by_paragraphs
        ]
        
        for strategy in selection_strategies:
            content = await strategy(page)
            if len(content.split()) > 100:  # Arbitrary threshold
                return content
        
        return ""

    async def select_all_content(self, page):
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Control+C")
        return pyperclip.paste()

    async def select_by_main_content(self, page):
        main_content_selectors = ["main", "article", "#content", ".content"]
        for selector in main_content_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return await element.inner_text()
            except:
                pass
        return ""

    async def select_by_paragraphs(self, page):
        paragraphs = await page.query_selector_all("p")
        text = ""
        for p in paragraphs:
            text += await p.inner_text() + "\n"
        return text

    async def download_pdf(self, url):
        headers = {"User-Agent": self.user_agent.random}
        async with self.session.get(url, headers=headers, timeout=ClientTimeout(total=self.initial_timeout)) as response:
            if response.status == 200:
                return await response.read()
            else:
                self.logger.warning(f"Failed to download PDF for URL: {url}")
                return b""

    def extract_text_from_pdf(self, pdf_bytes):
        self.logger.info("Extracting text from PDF")
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
        self.logger.info("Extracting text from HTML")
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
        url = re.sub(r'^https?://(www\.)?', '', url)
        filename = re.sub(r'[^\w\-_\.]', '_', url)
        return filename[:255] + '.txt'

    def save_content(self, content, filename, output_folder):
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
        content = await self.scrape(url, min_words=min_words)
        end_time = time.time()
        scraping_time = end_time - start_time
        
        word_count = len(content.split())
        normalized_url = self.normalize_url(url)
        filename = self.sanitize_filename(normalized_url)
        
        if word_count >= min_words:
            self.save_content(content, filename, output_folder)
            self.logger.info(f"URL: {url} | Status: Success | Word count: {word_count} | Scraping time: {scraping_time:.2f}s | Saved as: {filename}")
            print(f"\nURL: {url}\nStatus: Success\nWord count: {word_count}\nScraping time: {scraping_time:.2f}s\nSaved as: {filename}\n" + "-" * 80)
            return True
        else:
            self.logger.warning(f"URL: {url} | Status: Failure (insufficient words) | Word count: {word_count} | Scraping time: {scraping_time:.2f}s")
            print(f"\nURL: {url}\nStatus: Failure (insufficient words)\nWord count: {word_count}\nScraping time: {scraping_time:.2f}s\n" + "-" * 80)
            return False

    async def run_scraper(self, urls, output_folder):
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.process_url(url, output_folder))
            tasks.append(task)
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
        logger.info(f"Loaded {len(failed_urls)} failed URLs from previous run")
    else:
        failed_urls = []

    initial_urls = [
        "https://doi.org/10.3390/agronomy13082113",
        "https://doi.org/10.17159/wsa/2019.v45.i3.6750",
        "https://doi.org/10.1049/cth2.12554",
        "https://doi.org/10.3390/w14162457",
        "https://doi.org/10.1136/bmj.p2739",
        "https://doi.org/10.3390/su16093575",
        "https://doi.org/10.1007/s11227-021-03914-1",
        "https://doi.org/10.3390/agronomy13020342",
        "https://doi.org/10.1109/jas.2021.1003925",
        "https://doi.org/10.1029/2007WR006767",
        "https://doi.org/10.1016/j.agwat.2024.108741",
        "https://doi.org/10.1111/jac.12191",
        "https://doi.org/10.1002/cft2.20217",
        "https://doi.org/10.1111/j.1600-0047.2004.00296.x",
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10638802/pdf/12884_2023_Article_6089.pdf",
        "https://doi.org/10.17795/whb-34991",
        "https://doi.org/10.1046/j.1523-536x.2000.00112.x",
        "https://doi.org/10.1080/03630242.2022.2077508",
    ]

    all_urls = initial_urls + failed_urls

    async with aiohttp.ClientSession() as session:
        scraper = UnifiedWebScraper(session=session, max_concurrent_tasks=10, initial_timeout=15)
        try:
            await scraper.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {str(e)}")
            return

        await scraper.run_scraper(all_urls, output_folder)
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())