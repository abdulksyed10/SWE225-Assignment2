import re
import os
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
from configparser import ConfigParser
from utils.config import Config

# File paths
STOPWORDS_FILE = "stopwords.txt"
REPORT_FILE = "report.txt"

# Storage variables
unique_urls = set()
page_word_counts = {}  # {url: word_count}
subdomains = defaultdict(set)  # {subdomain: set(urls)}
word_frequencies = Counter()

# Load stopwords from stopwords.txt
def load_stopwords():
    """Loads stopwords from stopwords.txt."""
    stopwords = set()
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            stopwords = {line.strip().lower() for line in f if line.strip()}
    return stopwords

STOPWORDS = load_stopwords()

def get_allowed_domains():
    """Extracts allowed domains from SEEDURL in config.ini."""
    config_parser = ConfigParser()
    config_parser.read("config.ini")
    config = Config(config_parser)

    # Extract domains from SEEDURL
    return {urlparse(seed_url).netloc for seed_url in config.seed_urls}

ALLOWED_DOMAINS = get_allowed_domains()

def scraper(url, resp):
    """Processes the page, extracts text, filters valid URLs, and tracks statistics."""
    try:
        # Ignore responses with non-200 status or empty content
        if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
            return []

        # Remove URL fragment (e.g., #section1)
        url, _ = urldefrag(url)

        # Ignore duplicate URLs (same URL different fragment)
        if url in unique_urls:
            return []
        unique_urls.add(url)  # Store unique URL

        # Parse HTML content using BeautifulSoup
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")

        # Remove scripts, styles, and noscript content
        for script in soup(["script", "style", "noscript"]):  
            script.extract()

        # Extract visible text
        text = soup.get_text(separator=" ")
        words = re.findall(r"\b[A-Za-z]{2,}\b", text.lower())  # Tokenize words

        # Filter out stopwords
        filtered_words = [word for word in words if word not in STOPWORDS]
        word_frequencies.update(filtered_words)  # Update word frequency counter

        # Track page word count
        page_word_counts[url] = len(filtered_words)

        # Track subdomains under "ics.uci.edu"
        parsed_url = urlparse(url)
        if parsed_url.netloc.endswith("ics.uci.edu"):
            subdomains[parsed_url.netloc].add(url)

        # Extract valid links from page
        links = extract_next_links(url, soup)
        return [link for link in links if is_valid(link)]

    except Exception as e:
        print(f"Error in scraper: {e}")
        return []

def extract_next_links(url, soup):
    """Extracts and normalizes links from a web page using BeautifulSoup."""
    try:
        links = set()
        for link in soup.find_all("a", href=True):
            full_url, _ = urldefrag(urljoin(url, link["href"]))  # Normalize and remove fragments
            links.add(full_url)

        return list(links)

    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

def is_valid(url):
    """Ensures URL is within allowed domains and not a restricted file type."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        # Only allow URLs within the configured domains
        if parsed.netloc not in ALLOWED_DOMAINS and not parsed.netloc.endswith(tuple(ALLOWED_DOMAINS)):
            return False

        # Ignore non-text file types
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print(f"TypeError for {parsed}")
        raise

def save_data():
    """Saves all crawl results in report.txt."""
    # Find longest page
    longest_page = max(page_word_counts, key=page_word_counts.get, default=None)
    longest_page_info = {"url": longest_page, "word_count": page_word_counts.get(longest_page, 0)}

    # Find 50 most common words
    top_50_words = word_frequencies.most_common(50)

    # Subdomain counts
    subdomain_counts = {subdomain: len(urls) for subdomain, urls in sorted(subdomains.items())}

    # Write results to report.txt
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=== Web Crawler Report ===\n\n")

        # Unique pages count
        f.write(f"1. Unique Pages Found: {len(unique_urls)}\n\n")

        # Longest page
        f.write(f"2. Longest Page:\n   URL: {longest_page}\n   Word Count: {longest_page_info['word_count']}\n\n")

        # Most common words
        f.write("3. 50 Most Common Words (excluding stopwords):\n")
        for word, count in top_50_words:
            f.write(f"   {word}: {count}\n")
        f.write("\n")

        # Subdomains found
        f.write("4. Subdomains Found in ics.uci.edu:\n")
        for subdomain, count in subdomain_counts.items():
            f.write(f"   {subdomain}, {count}\n")

    # Print summary
    print("\nCrawl Data Saved Successfully!")
    print(f"- Final report saved in `{REPORT_FILE}`")
