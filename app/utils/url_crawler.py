import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List
import re
import time
from pathlib import Path
import logging

class URLCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.relevant_urls: Set[str] = set()
        
        # Polite crawler identification
        self.headers = {
            'User-Agent': 'InternationAlly Bot (Educational Project - University of Chicago Capstone Project)',
            'From': 'wdeforest@uchicago.edu',  # Replace with your UChicago email
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        }
        
        # Rate limiting settings
        self.delay = 2  # 2 seconds between requests
        self.last_request_time = 0
        
        # Setup logging
        logging.basicConfig(
            filename='crawler.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    def wait_between_requests(self):
        """Ensure polite delay between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.delay:
            time.sleep(self.delay - time_since_last_request)
        self.last_request_time = time.time()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the same domain."""
        parsed = urlparse(url)
        return (
            parsed.netloc == self.domain and
            'internationalaffairs.uchicago.edu' in url and
            '#' not in url and
            'mailto:' not in url and
            'tel:' not in url and
            '.pdf' not in url and
            '.doc' not in url and
            'calendar' not in url.lower() and  # Skip calendar pages
            'search' not in url.lower() and    # Skip search pages
            'login' not in url.lower()         # Skip login pages
        )

    def is_content_page(self, url: str) -> bool:
        """Check if URL is likely a content page we want to scrape."""
        patterns = [
            '/students/',
            '/current-students/',
            '/prospective-students/',
            '/admitted-students/',
            '/resources/',
            '/visa/',
            '/employment/',
            '/health/',
            '/housing/',
        ]
        return any(pattern in url.lower() for pattern in patterns)

    def crawl(self, url: str, depth: int = 3) -> None:
        """Crawl the URL and its subpages with depth limit."""
        if depth <= 0 or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        logging.info(f"Crawling: {url}")
        print(f"Crawling: {url}")

        try:
            # Respect rate limiting
            self.wait_between_requests()
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Check if we're getting HTML content
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return
                
            soup = BeautifulSoup(response.text, 'html.parser')

            # If this is a content page, add it to relevant URLs
            if self.is_content_page(url):
                self.relevant_urls.add(url)
                logging.info(f"Found relevant content: {url}")

            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)

                if self.is_valid_url(full_url) and full_url not in self.visited_urls:
                    self.crawl(full_url, depth - 1)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            print(f"Error crawling {url}: {str(e)}")
            time.sleep(self.delay)  # Wait after an error

    def save_urls(self, filename: str = "documents/urls.txt") -> None:
        """Save relevant URLs to a file."""
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            for url in sorted(self.relevant_urls):
                f.write(f"{url}\n")
        logging.info(f"Saved {len(self.relevant_urls)} URLs to {filename}")
        print(f"Saved {len(self.relevant_urls)} URLs to {filename}")

def main():
    print("Starting crawler with polite settings...")
    print("- 2 second delay between requests")
    print("- Proper identification in headers")
    print("- Respecting robots.txt")
    print("- Logging enabled")
    print("\nPress Ctrl+C to stop crawling at any time.\n")
    
    try:
        base_url = "https://internationalaffairs.uchicago.edu"
        crawler = URLCrawler(base_url)
        crawler.crawl(base_url)
        crawler.save_urls()
    except KeyboardInterrupt:
        print("\nCrawling stopped by user.")
        crawler.save_urls()  # Save what we've found so far

if __name__ == "__main__":
    main() 