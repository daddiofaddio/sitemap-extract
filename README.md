# sitemap-extract

This script is designed to efficiently process XML sitemaps and extract URLs. It supports both plain XML and compressed XML (.xml.gz) files and can fetch sitemaps directly from URLs, from a file containing a list of URLs, or from a directory containing XML files. The script uses multithreading to speed up the processing and includes robust logging for monitoring its execution.

## Features

1. **Multiple Input Sources**:
   - Fetch sitemaps directly from a URL.
   - Read a list of sitemap URLs from a file.
   - Scan a directory for XML and compressed XML (.xml.gz) files.

2. **User-Agent Rotation**:
   - Randomly select user agents from a predefined list to mimic different browsers and avoid detection.

3. **Cloudscraper Integration**:
   - Use Cloudscraper to handle requests, including bypassing anti-bot measures. This can be turned on or off.

4. **Proxy Support**:
   - Optionally use proxies for requests. This can be turned on or off.

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

12. **Highly Customizable**:
    - Easily customize for various use cases and sitemap structures, including sitemaps with tens of millions of URLs.

13. **High Performance**:
    - Designed for speed, capable of processing large sitemaps quickly.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/sitemap_processor.git
    cd sitemap_processor
    ```

2. Ensure you have Python 3 installed.

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Basic Usage
  
    ```bash
    python -m sitemap_processor.sitemap_processor --url <sitemap_url>
    python -m sitemap_processor.sitemap_processor --file <file_with_urls>
    python -m sitemap_processor.sitemap_processor --directory <directory_with_xml_files>
    ```

### Examples

Fetch a single sitemap directly from a URL:

    ```bash
    python -m sitemap_processor.sitemap_processor --url https://example.com/sitemap_index.xml
    ```

Read a list of sitemap URLs from a file:

    ```bash
    python -m sitemap_processor.sitemap_processor --file sitemaps.txt
    ```

Scan a directory for XML and compressed XML (.xml.gz) files:

    ```bash
    python -m sitemap_processor.sitemap_processor --directory ./sitemaps/
    ```

### Advanced Options

#### Turn on/off Cloudscraper

To disable Cloudscraper and use standard requests:

    ```bash
    python -m sitemap_processor.sitemap_processor --url <sitemap_url> --no-cloudscraper
    ```

#### Turn on/off Proxy

To enable proxy support:

     ```bash
     python -m sitemap_processor.sitemap_processor --url <sitemap_url> --proxy
     ```

## Requirements

- `Python 3.x`
- `cloudscraper`
- `argparse`

## Customization

In addition to proxies, users can choose to utilize the default or advanced options of Cloudscraper or use features such as rotating headers and user-agents directly in the script.

### Proxy Configuration

Proxies can be configured in the script or via environment variables.

### Rotating Headers and User-Agents

You can customize the list of user-agents and headers directly in the script to better mimic different browsers and avoid detection.

## Logging

Logs are saved to `sitemap_processing.log` in the following format:

```bash
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```

Each sitemap processed will also generate a separate text file containing the source URL and all extracted URLs.

## Disclaimer

I am a self-taught, beginner coder. Although I found some similar repositories involving sitemap extraction, I couldn't find any that included all the features I needed for my projects. So I decided to write my first script from scratch. PLEASE GO EASY ON ME, HAHA. I have no idea about the quality of the code since I have no training, but it's worked astoundingly well with every site I've thrown at it so far. It's pretty fast but I've never encountered any issues with being blocked (or other errors), and it's been tested on sites with very different sitemap structures, including multiple sites with hundreds of nested/child sitemaps and millions of total URLs.

Everyone on GitHub has been such a wonderful help to me -- hopefully this will help someone else. That said, if you find any major bugs, run into any major issues, or think it can otherwise be improved, please open an issue or let me know!
