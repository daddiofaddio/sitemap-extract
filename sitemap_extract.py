import os
import xml.etree.ElementTree as ET
import gzip
import logging
import argparse
import cloudscraper
import random
import glob
from datetime import datetime
import sys
from urllib.parse import urljoin, urlparse
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Logging will be configured dynamically in main()

# Enhanced user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

BROWSER_HEADERS = [
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    },
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
]


class HumanizedSitemapProcessor:
    def __init__(
        self,
        use_cloudscraper=True,
        proxy_file=None,
        user_agent_file=None,
        min_delay=2.0,
        max_delay=5.0,
        max_retries=3,
        max_workers=1,
        save_dir=None,
    ):
        self.use_cloudscraper = use_cloudscraper
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.processed_urls = set()
        self.interrupted = False
        self.save_dir = save_dir if save_dir else "."

        # Enhanced failure tracking
        self.failed_urls = (
            {}
        )  # {url: {'error': 'description', 'status_code': code, 'attempts': n}}

        # Load proxies and user agents from files
        self.proxies = self.load_proxies(proxy_file) if proxy_file else []
        self.custom_user_agents = (
            self.load_user_agents(user_agent_file) if user_agent_file else []
        )

        # Use custom user agents if available, otherwise fallback to built-in
        self.user_agents = (
            self.custom_user_agents if self.custom_user_agents else USER_AGENTS
        )

        self.session_stats = {
            "sitemaps_processed": 0,
            "pages_found": 0,
            "errors": 0,
            "retries": 0,
            "start_time": time.time(),
        }
        self.last_request_time = 0
        self.current_proxy = None
        self.current_user_agent = None

    def load_proxies(self, proxy_file):
        """Load proxies from file"""
        try:
            with open(proxy_file, "r") as f:
                proxies = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Support formats: ip:port, ip:port:user:pass, http://ip:port
                        if line.startswith("http"):
                            proxies.append({"http": line, "https": line})
                        elif ":" in line:
                            parts = line.split(":")
                            if len(parts) == 2:  # ip:port
                                proxy_url = f"http://{line}"
                                proxies.append({"http": proxy_url, "https": proxy_url})
                            elif len(parts) == 4:  # ip:port:user:pass
                                ip, port, user, password = parts
                                proxy_url = f"http://{user}:{password}@{ip}:{port}"
                                proxies.append({"http": proxy_url, "https": proxy_url})
                self.print_status(f"Loaded {len(proxies)} proxies from {proxy_file}")
                return proxies
        except Exception as e:
            self.print_status(f"Error loading proxies: {str(e)}")
            return []

    def load_user_agents(self, ua_file):
        """Load user agents from file"""
        try:
            with open(ua_file, "r") as f:
                user_agents = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            self.print_status(f"Loaded {len(user_agents)} user agents from {ua_file}")
            return user_agents
        except Exception as e:
            self.print_status(f"Error loading user agents: {str(e)}")
            return []

    def get_current_ip(self):
        """Get current IP address for monitoring"""
        try:
            if self.current_proxy:
                proxy_str = str(self.current_proxy.get("http", "Unknown"))
                if "@" in proxy_str:
                    return proxy_str.split("@")[1].split(":")[0]
                else:
                    return proxy_str.replace("http://", "").split(":")[0]
            else:
                return "Direct Connection"
        except:
            return "Unknown"

    def print_status(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        sys.stdout.flush()

    def human_delay(self):
        """Add human-like delays between requests"""
        if self.interrupted:
            raise KeyboardInterrupt()

        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        delay = random.uniform(self.min_delay, self.max_delay)

        # 15% chance of longer pause
        if random.random() < 0.15:
            delay += random.uniform(3.0, 8.0)
            self.print_status("Taking a longer human-like break...")

        if time_since_last < delay:
            sleep_time = delay - time_since_last
            self.print_status(f"Waiting {sleep_time:.2f} seconds...")

            # Sleep in small chunks to allow interruption
            end_time = time.time() + sleep_time
            while time.time() < end_time:
                if self.interrupted:
                    raise KeyboardInterrupt()
                time.sleep(0.1)

        self.last_request_time = time.time()

    def create_enhanced_scraper(self):
        """Create sophisticated scraper with rotating proxies and user agents"""
        # Rotate proxy for each request
        if self.proxies:
            self.current_proxy = random.choice(self.proxies)
        else:
            self.current_proxy = None

        # Rotate user agent for each request
        self.current_user_agent = random.choice(self.user_agents)

        if self.use_cloudscraper:
            scraper = cloudscraper.create_scraper(
                browser={
                    "browser": random.choice(["chrome", "firefox"]),
                    "platform": random.choice(["windows", "darwin"]),
                    "desktop": True,
                }
            )
        else:
            scraper = requests.Session()
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            scraper.mount("http://", adapter)
            scraper.mount("https://", adapter)

        # Set headers and FORCE our user agent (override cloudscraper)
        headers = random.choice(BROWSER_HEADERS).copy()
        headers["User-Agent"] = self.current_user_agent

        # Add some randomness
        if random.random() < 0.3:
            headers[
                "X-Forwarded-For"
            ] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

        # Enhanced browser headers
        if random.random() < 0.5:
            headers.update(
                {
                    "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120"',
                    "Sec-CH-UA-Mobile": "?0",
                    "Sec-CH-UA-Platform": '"Windows"'
                    if "Windows" in self.current_user_agent
                    else '"macOS"',
                }
            )

        scraper.headers.update(headers)

        # CRITICAL: Force our user agent again after all header updates
        scraper.headers["User-Agent"] = self.current_user_agent

        # Set proxy
        if self.current_proxy:
            scraper.proxies.update(self.current_proxy)

        return scraper

    def fetch_with_retries(self, url, is_compressed=False):
        """Fetch URL with retries and anti-detection measures"""
        for attempt in range(self.max_retries + 1):
            if self.interrupted:
                raise KeyboardInterrupt()

            try:
                self.human_delay()
                scraper = self.create_enhanced_scraper()

                # Enhanced monitoring output
                current_ip = self.get_current_ip()
                ua_display = self.current_user_agent
                if len(ua_display) > 60:
                    ua_display = ua_display[:60] + "..."

                self.print_status(f"Fetching (attempt {attempt + 1}): {url}")
                self.print_status(f"Using IP: {current_ip}")
                self.print_status(f"Using User-Agent: {ua_display}")

                timeout = random.uniform(15, 30)
                response = scraper.get(url, timeout=timeout, stream=is_compressed)

                if response.status_code == 200:
                    self.print_status(f"SUCCESS with {current_ip}")
                    if is_compressed:
                        with gzip.open(response.raw, "rb") as f:
                            content = f.read()
                        return ET.fromstring(content)
                    else:
                        return ET.fromstring(response.content)

                elif response.status_code == 403:
                    self.print_status(
                        f"403 Forbidden with {current_ip} - attempt {attempt + 1}/{self.max_retries + 1}"
                    )
                    if attempt < self.max_retries:
                        wait_time = (2**attempt) + random.uniform(5, 15)
                        self.print_status(
                            f"Waiting {wait_time:.2f} seconds before retry..."
                        )

                        # Sleep in chunks to allow interruption
                        end_time = time.time() + wait_time
                        while time.time() < end_time:
                            if self.interrupted:
                                raise KeyboardInterrupt()
                            time.sleep(0.1)

                        self.session_stats["retries"] += 1
                        continue
                    else:
                        # Final attempt failed, record detailed failure
                        self.failed_urls[url] = {
                            "error": f"HTTP 403 Forbidden after {self.max_retries + 1} attempts",
                            "status_code": 403,
                            "attempts": self.max_retries + 1,
                        }

                elif response.status_code == 429:
                    self.print_status(
                        f"Rate limited with {current_ip} - attempt {attempt + 1}/{self.max_retries + 1}"
                    )
                    if attempt < self.max_retries:
                        wait_time = random.uniform(20, 40)
                        self.print_status(
                            f"Rate limit hit, waiting {wait_time:.2f} seconds..."
                        )

                        # Sleep in chunks to allow interruption
                        end_time = time.time() + wait_time
                        while time.time() < end_time:
                            if self.interrupted:
                                raise KeyboardInterrupt()
                            time.sleep(0.1)

                        self.session_stats["retries"] += 1
                        continue
                    else:
                        # Final attempt failed, record detailed failure
                        self.failed_urls[url] = {
                            "error": f"HTTP 429 Rate Limited after {self.max_retries + 1} attempts",
                            "status_code": 429,
                            "attempts": self.max_retries + 1,
                        }

                else:
                    self.print_status(
                        f"HTTP {response.status_code} with {current_ip} - attempt {attempt + 1}/{self.max_retries + 1}"
                    )
                    if attempt < self.max_retries:
                        wait_time = random.uniform(3, 8)
                        time.sleep(wait_time)
                        self.session_stats["retries"] += 1
                        continue
                    else:
                        # Final attempt failed, record detailed failure
                        self.failed_urls[url] = {
                            "error": f"HTTP {response.status_code} after {self.max_retries + 1} attempts",
                            "status_code": response.status_code,
                            "attempts": self.max_retries + 1,
                        }

            except KeyboardInterrupt:
                raise
            except Exception as e:
                current_ip = self.get_current_ip()
                error_msg = str(e)
                self.print_status(
                    f"Error with {current_ip}: {error_msg} - attempt {attempt + 1}/{self.max_retries + 1}"
                )
                if attempt < self.max_retries:
                    time.sleep(random.uniform(5, 10))
                    self.session_stats["retries"] += 1
                    continue
                else:
                    # Final attempt failed, record detailed failure
                    if "timeout" in error_msg.lower():
                        error_description = (
                            f"Timeout after {self.max_retries + 1} attempts"
                        )
                    else:
                        error_description = (
                            f"{error_msg} after {self.max_retries + 1} attempts"
                        )

                    self.failed_urls[url] = {
                        "error": error_description,
                        "status_code": None,
                        "attempts": self.max_retries + 1,
                    }

        logging.error(f"Failed to fetch {url} after {self.max_retries + 1} attempts")
        self.session_stats["errors"] += 1
        return None

    def save_urls(self, source_url, urls):
        """Save URLs to file"""
        if not urls and source_url != "all_sitemaps_summary":
            return

        try:
            if source_url == "all_sitemaps_summary":
                # Special handling for sitemap summary with failure annotations
                filename = os.path.join(self.save_dir, "all_sitemaps_summary.log")
                successful_urls = sorted(urls) if urls else []
                total_urls = len(successful_urls) + len(self.failed_urls)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"Source URL: all_sitemaps_summary\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"Total URLs: {total_urls}\n")
                    f.write(f"Successful URLs: {len(successful_urls)}\n")
                    f.write(f"Failed URLs: {len(self.failed_urls)}\n")
                    f.write("-" * 50 + "\n")

                    # Write successful URLs
                    for url in successful_urls:
                        f.write(f"{url}\n")

                    # Write failed URLs with detailed annotations
                    for failed_url, failure_info in sorted(self.failed_urls.items()):
                        error_detail = failure_info.get("error", "Unknown error")
                        f.write(f"{failed_url} [*{error_detail}*]\n")

                self.print_status(
                    f"Saved sitemap summary: {len(successful_urls)} successful, {len(self.failed_urls)} failed URLs to {filename}"
                )

                # Also create the clean failed URLs file for easy reprocessing
                if self.failed_urls:
                    failed_filename = os.path.join(
                        self.save_dir, "failed_sitemap_urls.txt"
                    )
                    with open(failed_filename, "w", encoding="utf-8") as f:
                        f.write(f"# Failed sitemap URLs for reprocessing\n")
                        f.write(f"# Generated: {datetime.now().isoformat()}\n")
                        f.write(f"# Total failed URLs: {len(self.failed_urls)}\n")
                        f.write(
                            f"# Usage: python sitemap_extract.py --file {failed_filename}\n"
                        )
                        f.write("-" * 50 + "\n")
                        for failed_url in sorted(self.failed_urls.keys()):
                            f.write(f"{failed_url}\n")
                    self.print_status(
                        f"Saved {len(self.failed_urls)} failed URLs to {failed_filename} for reprocessing"
                    )

            else:
                # Normal URL file handling
                parsed_url = urlparse(source_url)
                filename = (
                    parsed_url.netloc.replace(".", "_")
                    + "_"
                    + parsed_url.path.replace("/", "_").strip("_")
                )
                filename = "".join(
                    c for c in filename if c.isalnum() or c in ("_", "-")
                )
                filename = f"{filename}.txt" if filename else "sitemap_urls.txt"
                filepath = os.path.join(self.save_dir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"Source URL: {source_url}\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"Total URLs: {len(urls)}\n")
                    f.write("-" * 50 + "\n")
                    for url in sorted(urls):
                        f.write(f"{url}\n")

                self.print_status(f"Saved {len(urls)} URLs to {filepath}")

        except Exception as e:
            self.print_status(f"Failed to save URLs: {str(e)}")

    def process_sitemap(self, url):
        """Process single sitemap"""
        if url in self.processed_urls or self.interrupted:
            return [], []

        self.processed_urls.add(url)

        is_compressed = url.endswith(".xml.gz")
        root = self.fetch_with_retries(url, is_compressed)

        if not root:
            return [], []

        sitemap_urls = []
        page_urls = []
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        for sitemap in root.findall(".//sm:sitemap", namespace):
            loc_element = sitemap.find("sm:loc", namespace)
            if loc_element is not None and loc_element.text:
                sitemap_url = urljoin(url, loc_element.text.strip())
                if sitemap_url not in self.processed_urls:
                    sitemap_urls.append(sitemap_url)

        for page in root.findall(".//sm:url", namespace):
            loc_element = page.find("sm:loc", namespace)
            if loc_element is not None and loc_element.text:
                page_urls.append(loc_element.text.strip())

        self.session_stats["sitemaps_processed"] += 1
        self.session_stats["pages_found"] += len(page_urls)

        self.print_status(
            f"Processed: {len(sitemap_urls)} nested sitemaps, {len(page_urls)} pages"
        )

        if page_urls:
            self.save_urls(url, page_urls)

        return sitemap_urls, page_urls

    def process_sitemap_delayed(self, url, initial_delay):
        """Process sitemap with initial stagger delay"""
        if initial_delay > 0:
            time.sleep(initial_delay)
        return self.process_sitemap(url)

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.print_status("Received interrupt signal, stopping gracefully...")
        self.interrupted = True

    def process_all_sitemaps(self, start_urls):
        """Process all sitemaps with optional threading"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

        all_sitemap_urls = set()
        all_page_urls = set()
        queue = list(set(start_urls))

        self.print_status(f"Starting processing of {len(queue)} initial sitemaps")
        self.print_status(
            f"Using delays between {self.min_delay}-{self.max_delay} seconds"
        )
        self.print_status(f"Proxies available: {len(self.proxies)}")
        self.print_status(f"User agents available: {len(self.user_agents)}")
        self.print_status(f"Max concurrent workers: {self.max_workers}")
        self.print_status("Press Ctrl+C to stop gracefully...")

        try:
            if self.max_workers == 1:
                # Sequential processing for maximum stealth
                while queue and not self.interrupted:
                    url = queue.pop(0)
                    try:
                        sitemap_urls, page_urls = self.process_sitemap(url)

                        new_sitemaps = [
                            surl
                            for surl in sitemap_urls
                            if surl not in all_sitemap_urls
                            and surl not in self.processed_urls
                        ]
                        queue.extend(new_sitemaps)

                        all_sitemap_urls.update(sitemap_urls)
                        all_page_urls.update(page_urls)

                        self.print_status(
                            f"Queue size: {len(queue)}, Total URLs found: {len(all_page_urls)}"
                        )

                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logging.error(f"Error processing {url}: {str(e)}")
                        self.print_status(f"Error processing {url}: {str(e)}")
                        self.session_stats["errors"] += 1
            else:
                # Multi-threaded processing
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    while queue and not self.interrupted:
                        # Process batch
                        current_batch = queue[: self.max_workers]
                        queue = queue[self.max_workers :]

                        # Stagger request starts to avoid simultaneous hits
                        future_to_url = {}
                        for i, url in enumerate(current_batch):
                            if self.interrupted:
                                break
                            # Stagger by 0.5-2 seconds per thread
                            delay = i * random.uniform(0.5, 2.0)
                            future = executor.submit(
                                self.process_sitemap_delayed, url, delay
                            )
                            future_to_url[future] = url

                        # Collect results
                        for future in as_completed(future_to_url):
                            if self.interrupted:
                                break
                            url = future_to_url[future]
                            try:
                                sitemap_urls, page_urls = future.result()

                                new_sitemaps = [
                                    surl
                                    for surl in sitemap_urls
                                    if surl not in all_sitemap_urls
                                    and surl not in self.processed_urls
                                ]
                                queue.extend(new_sitemaps)

                                all_sitemap_urls.update(sitemap_urls)
                                all_page_urls.update(page_urls)

                            except Exception as e:
                                logging.error(f"Error processing {url}: {str(e)}")
                                self.print_status(f"Error processing {url}: {str(e)}")
                                self.session_stats["errors"] += 1

                        self.print_status(
                            f"Queue size: {len(queue)}, Total URLs found: {len(all_page_urls)}"
                        )

        except KeyboardInterrupt:
            self.print_status("Processing interrupted by user")

        if all_sitemap_urls:
            self.save_urls("all_sitemaps_summary", sorted(all_sitemap_urls))

        return all_sitemap_urls, all_page_urls

    def print_summary(self, all_sitemap_urls, all_page_urls):
        """Print summary"""
        elapsed_time = time.time() - self.session_stats["start_time"]
        successful_sitemaps = len(all_sitemap_urls) - len(self.failed_urls)

        self.print_status("=" * 60)
        self.print_status("PROCESSING COMPLETE")
        self.print_status("=" * 60)
        self.print_status(f"Total runtime: {elapsed_time:.2f} seconds")
        self.print_status(f"Unique sitemap URLs found: {len(all_sitemap_urls)}")
        self.print_status(f"Sitemap URLs successfully processed: {successful_sitemaps}")
        self.print_status(f"Total page URLs extracted: {len(all_page_urls)}")
        if self.failed_urls:
            self.print_status(
                f'Sitemap URLs failed to process: {len(self.failed_urls)} [specific URLs listed in "failed_sitemap_urls.txt"]'
            )
        else:
            self.print_status(f"Sitemap URLs failed to process: 0")
        self.print_status(f"Errors encountered: {self.session_stats['errors']}")
        self.print_status(f"Retries performed: {self.session_stats['retries']}")


def main():
    parser = argparse.ArgumentParser(
        description="Humanized XML sitemap processor with proxy rotation"
    )
    parser.add_argument("--url", type=str, help="Direct URL of sitemap file")
    parser.add_argument("--file", type=str, help="File containing list of sitemap URLs")
    parser.add_argument("--directory", type=str, help="Directory containing XML files")
    parser.add_argument(
        "--save-dir",
        type=str,
        help="Directory to save all output files (default: current directory)",
    )
    parser.add_argument(
        "--no-cloudscraper",
        action="store_true",
        help="Use requests instead of CloudScraper",
    )
    parser.add_argument("--proxy-file", type=str, help="File containing proxy list")
    parser.add_argument(
        "--user-agent-file", type=str, help="File containing user agent list"
    )
    parser.add_argument(
        "--min-delay", type=float, default=3.0, help="Minimum delay (default: 3.0)"
    )
    parser.add_argument(
        "--max-delay", type=float, default=8.0, help="Maximum delay (default: 8.0)"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3, help="Max retries (default: 3)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Concurrent workers (default: 1, max stealth)",
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Extra stealth mode (forces max-workers=1)",
    )

    args = parser.parse_args()

    # Create save directory if specified and doesn't exist
    save_dir = args.save_dir if args.save_dir else "."
    if args.save_dir:
        try:
            os.makedirs(args.save_dir, exist_ok=True)
            print(f"[INFO] Using save directory: {os.path.abspath(args.save_dir)}")
        except Exception as e:
            print(f"[ERROR] Could not create save directory {args.save_dir}: {str(e)}")
            return 1

    # Configure logging to use save directory
    log_filepath = os.path.join(save_dir, "sitemap_processing.log")
    logging.basicConfig(
        filename=log_filepath,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",  # Overwrite log file each run
    )

    # Stealth adjustments
    if args.stealth:
        if args.min_delay < 5.0:
            print(
                f"[WARNING] Stealth mode overriding min-delay from {args.min_delay} to 5.0 seconds"
            )
        if args.max_delay < 12.0:
            print(
                f"[WARNING] Stealth mode overriding max-delay from {args.max_delay} to 12.0 seconds"
            )
        args.min_delay = max(args.min_delay, 5.0)
        args.max_delay = max(args.max_delay, 12.0)
        if args.max_workers > 1:
            print(
                f"[WARNING] Using {args.max_workers} workers in stealth mode may reduce stealth effectiveness"
            )

    # Collect URLs to process
    urls_to_process = []
    if args.url:
        urls_to_process.append(args.url)
    if args.file:
        try:
            with open(args.file, "r") as f:
                urls_to_process.extend([line.strip() for line in f if line.strip()])
        except Exception as e:
            print(f"[ERROR] Could not read file {args.file}: {str(e)}")
            return 1
    if args.directory:
        urls_to_process.extend(glob.glob(os.path.join(args.directory, "*.xml*")))

    if not urls_to_process:
        print("[ERROR] No URLs provided")
        return 1

    # Instantiate and run processor
    processor = HumanizedSitemapProcessor(
        use_cloudscraper=not args.no_cloudscraper,
        proxy_file=args.proxy_file,
        user_agent_file=args.user_agent_file,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_retries=args.max_retries,
        max_workers=args.max_workers,
        save_dir=args.save_dir,
    )

    try:
        all_sitemap_urls, all_page_urls = processor.process_all_sitemaps(
            urls_to_process
        )
        processor.print_summary(all_sitemap_urls, all_page_urls)
        return 0
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Processing stopped by user")
        processor.print_summary(set(), set())
        return 130


if __name__ == "__main__":
    sys.exit(main())
