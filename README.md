# sitemap-extract

This script is designed to efficiently process XML sitemaps and extract URLs. It supports both plain XML and compressed XML (.xml.gz) files and can fetch sitemaps directly from URLs, from a file containing a list of URLs, or from a directory containing XML files. The script uses multithreading to speed up processing, allows for processing of unlimited nested/child sitemaps, includes protection against anti-bot measures, optional features such as rotating proxies and headers/useragents, and includes detailed logging for monitoring its execution.

## Features

1. **Multiple Input Sources**:
   - Fetch sitemaps directly from a URL.
   - Read a list of sitemap URLs from a file.
   - Scan a directory for XML and compressed XML (.xml.gz) files.

2. **User-Agent Rotation**:
   - Randomly select user agents from a predefined list to mimic different browsers and avoid detection (or use settings from Cloudscraper, or use both together, see below).

3. **Cloudscraper Integration**:
   - Use Cloudscraper to handle requests, including bypassing anti-bot measures. This can be turned on or off.

4. **Proxy Support**:
   - Optionally use rotating proxies for requests. This can be turned on or off.

5. **Compressed File Handling**:
   - Automatically detect and decompress .gz files to extract XML content.

6. **Multithreading**:
   - Utilize a thread pool to process multiple sitemaps concurrently, enhancing performance.

7. **Namespace-Aware XML Parsing**:
   - Properly handle XML namespaces to accurately extract URLs.

8. **Unlimited Nested Sitemaps**:
   - Scrape unlimited nested sitemaps, efficiently handling complex sitemap structures.

9. **Detailed Logging**:
   - Log all significant actions, errors, and the overall progress to a log file.
   - Generate separate log and text files for each sitemap, listing the master sitemap and all extracted links.

10. **URL Extraction and Saving**:
    - Extract URLs from sitemaps and save them to appropriately named text files.

11. **Command-Line Interface**:
    - Use command-line arguments to specify the URL, file, or directory to process.

12. **Customizable**:
    - Is customizable for various use cases and sitemap structures, including sitemaps with hundreds of nested sitemaps and millions of total URLs.

13. **High Performance**:
    - Speedy; capable of processing large sitemaps quickly.

## Installation

1. Doownload the zip file or clone the repository:

```bash
    git clone https://github.com/daddiofaddio/sitemap-extract.git
    cd sitemap-extract
```

2. Ensure you have Python 3 installed.

3. Install the required dependencies:

```bash
    pip install -r requirements.txt
```

## Usage

### Basic Usage
  
   ```bash
    python -m sitemap_extract.sitemap_extract --url <sitemap_url>
    python -m sitemap_extract.sitemap_extract --file <file_with_urls>
    python -m sitemap_extract.sitemap_extract --directory <directory_with_xml_files>
   ```

### Examples

Fetch a single sitemap directly from a URL (the script will automatically process the master sitemap and all nested sitemaps and generate a separate text file containing the source URL and all extracted URLs for each):

   ```bash
    python -m sitemap_extract.sitemap_extract --url https://example.com/sitemap_index.xml
   ```

Read a list of sitemap URLs from a file:

   ```bash
    python -m sitemap_extract.sitemap_extract --file sitemaps.txt
   ```

Scan a directory for XML and compressed XML (.xml.gz) files:

   ```bash
    python -m sitemap_extract.sitemap_extract --directory ./sitemaps/
   ```

### Additional Options

#### Enable/Disable Cloudscraper

Cloudscraper is enabled by default. To disable Cloudscraper and use standard requests:

   ```bash
    python -m sitemap_extract.sitemap_extract --url <sitemap_url> --no-cloudscraper
   ```

#### Enable/Disable Proxies

To enable proxy support:

   ```bash
     python -m sitemap_extract.sitemap_extract --url <sitemap_url> --proxy
   ```

## Requirements

- `Python 3.x`
- `cloudscraper`
- `argparse`

## Customization

In addition to proxies, users can choose to utilize the default or advanced options of Cloudscraper or use features such as rotating headers and user-agents directly in the script to better mimic different browsers and avoid detection.

### Proxy Configuration

Proxies can be configured in the script or via environment variables.

## Logging

Logs are saved to `sitemap_processing.log` in the following format:

```bash
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```
## Output Files

As noted above, each sitemap processed will also generate a separate text file containing the source URL and all extracted URLs.

## DISCLAIMER

I am a self-taught, beginner coder. Although I found some similar repositories involving sitemap extraction, I couldn't find any that included all the features I needed for my projects. So I decided to write one from scratch. PLEASE GO EASY ON ME, HAHA. I have no idea about the quality of the code since I have no training. It's worked well for me and I've never encountered any issues with being blocked (or other errors). It's been tested on sites with very different sitemap structures, including multiple sites with hundreds of nested/child sitemaps and millions of total URLs.

Everyone on GitHub has been such a wonderful help -- hopefully this will help someone else. That said, if you find any major bugs, run into any major issues, or think it can otherwise be improved, please open an issue or let me know!
