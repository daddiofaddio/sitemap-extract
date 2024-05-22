import os
import xml.etree.ElementTree as ET
import gzip
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse
import cloudscraper
import random
import glob

# Setup logging
logging.basicConfig(filename='sitemap_processing.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    # Add more user agents as necessary
]

def create_scraper(use_cloudscraper=True, use_proxy=False):
    if use_cloudscraper:
        scraper = cloudscraper.create_scraper()
    else:
        import requests
        scraper = requests.Session()
    
    if use_proxy:
        proxy = "http://your-proxy-server:port"
        scraper.proxies.update({
            'http': proxy,
            'https': proxy,
        })
    
    return scraper

def fetch_xml(url, use_cloudscraper=True, use_proxy=False):
    scraper = create_scraper(use_cloudscraper, use_proxy)
    scraper.headers['User-Agent'] = random.choice(USER_AGENTS)
    response = scraper.get(url)
    if response.status_code == 200:
        return ET.fromstring(response.content)
    logging.error(f"Failed to fetch URL {url}: HTTP {response.status_code}")
    return None

def decompress_gz(url, use_cloudscraper=True, use_proxy=False):
    scraper = create_scraper(use_cloudscraper, use_proxy)
    scraper.headers['User-Agent'] = random.choice(USER_AGENTS)
    response = scraper.get(url, stream=True)
    if response.status_code == 200:
        with gzip.open(response.raw, 'rb') as f:
            return ET.fromstring(f.read())
    logging.error(f"Failed to decompress URL {url}: HTTP {response.status_code}")
    return None

def save_urls(url, urls):
    filename = url.split('/')[-1].split('.')[0]
    filename = f"{filename}.txt" if filename else "sitemap_urls.txt"
    with open(filename, 'w') as f:
        f.write(f"Source URL: {url}
")
        for url in urls:
            f.write(f"{url}
")
    logging.info(f"URLs saved to {filename} with {len(urls)} URLs.")

def read_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def find_xml_files_in_directory(directory):
    return glob.glob(os.path.join(directory, '*.xml')) + glob.glob(os.path.join(directory, '*.xml.gz'))

def process_sitemap(url, is_compressed=False, use_cloudscraper=True, use_proxy=False):
    root = decompress_gz(url, use_cloudscraper, use_proxy) if is_compressed else fetch_xml(url, use_cloudscraper, use_proxy)
    if not root:
        return [], []

    sitemap_urls = []
    page_urls = []
    namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for sitemap in root.findall('.//sm:sitemap', namespace):
        loc = sitemap.find('.//sm:loc', namespace).text
        sitemap_urls.append(loc)
    for page in root.findall('.//sm:url', namespace):
        loc = page.find('.//sm:loc', namespace).text
        page_urls.append(loc)

    save_urls(url, page_urls)
    return sitemap_urls, page_urls

def process_all_sitemaps(start_urls, use_cloudscraper=True, use_proxy=False):
    all_sitemap_urls = set()
    all_page_urls = set()
    queue = start_urls[:]
    with ThreadPoolExecutor() as executor:
        while queue:
            current_url = queue.pop(0)
            future = executor.submit(process_sitemap, current_url, current_url.endswith('.xml.gz'), use_cloudscraper, use_proxy)
            sitemap_urls, page_urls = future.result()
            all_sitemap_urls.update(sitemap_urls)
            all_page_urls.update(page_urls)
            queue.extend(sitemap_urls)

    save_urls("sitemap_index", all_sitemap_urls)
    return all_sitemap_urls, all_page_urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process XML sitemaps.')
    parser.add_argument('--url', type=str, help='Direct URL of the sitemap index file.')
    parser.add_argument('--file', type=str, help='File containing list of URLs.')
    parser.add_argument('--directory', type=str, help='Directory containing XML and XML.GZ files.')
    parser.add_argument('--no-cloudscraper', action='store_true', help='Disable Cloudscraper and use standard requests.')
    parser.add_argument('--proxy', action='store_true', help='Enable proxy support.')
    args = parser.parse_args()

    urls_to_process = []
    if args.url:
        urls_to_process.append(args.url)
    if args.file:
        urls_to_process.extend(read_urls_from_file(args.file))
    if args.directory:
        urls_to_process.extend(find_xml_files_in_directory(args.directory))

    if urls_to_process:
        logging.info(f"Starting to process {len(urls_to_process)} sitemaps.")
        all_sitemap_urls, all_page_urls = process_all_sitemaps(urls_to_process, not args.no_cloudscraper, args.proxy)
        logging.info(f"Completed processing. Extracted {len(all_page_urls)} URLs.")
    else:
        logging.error("No URLs provided to process.")

    for sitemap in root.findall('.//sm:sitemap', namespace):
        loc = sitemap.find('.//sm:loc', namespace).text
        sitemap_urls.append(loc)
    for page in root.findall('.//sm:url', namespace):
        loc = page.find('.//sm:loc', namespace).text
        page_urls.append(loc)

    save_urls(url, page_urls)
    return sitemap_urls, page_urls

def process_all_sitemaps(start_urls, use_cloudscraper=True, use_proxy=False):
    all_sitemap_urls = set()
    all_page_urls = set()
    queue = start_urls[:]
    with ThreadPoolExecutor() as executor:
        while queue:
            current_url = queue.pop(0)
            future = executor.submit(process_sitemap, current_url, current_url.endswith('.xml.gz'), use_cloudscraper, use_proxy)
            sitemap_urls, page_urls = future.result()
            all_sitemap_urls.update(sitemap_urls)
            all_page_urls.update(page_urls)
            queue.extend(sitemap_urls)

    save_urls("sitemap_index", all_sitemap_urls)
    return all_sitemap_urls, all_page_urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process XML sitemaps.')
    parser.add_argument('--url', type=str, help='Direct URL of the sitemap index file.')
    parser.add_argument('--file', type=str, help='File containing list of URLs.')
    parser.add_argument('--directory', type=str, help='Directory containing XML and XML.GZ files.')
    parser.add_argument('--no-cloudscraper', action='store_true', help='Disable Cloudscraper and use standard requests.')
    parser.add_argument('--proxy', action='store_true', help='Enable proxy support.')
    args = parser.parse_args()

    urls_to_process = []
    if args.url:
        urls_to_process.append(args.url)
    if args.file:
        urls_to_process.extend(read_urls_from_file(args.file))
    if args.directory:
        urls_to_process.extend(find_xml_files_in_directory(args.directory))

    if urls_to_process:
        logging.info(f"Starting to process {len(urls_to_process)} sitemaps.")
        all_sitemap_urls, all_page_urls = process_all_sitemaps(urls_to_process, not args.no_cloudscraper, args.proxy)
        logging.info(f"Completed processing. Extracted {len(all_page_urls)} URLs.")
    else:
        logging.error("No URLs provided to process.")
