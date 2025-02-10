import re
import os
import json
import hashlib
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from collections import defaultdict, Counter
from lxml import html

# File paths for saved data
UNIQUE_URLS_FILE = "unique_urls.txt"
PAGE_WORD_COUNT_FILE = "page_word_count.json"
ALL_WORDS_FILE = "top_50_words.json"
SUBDOMAINS_FILE = "subdomain_and_page_count.json"
VISITED_HASHES_FILE = "visited_hashes.json"

# Crawler storage
unique_urls = set()
page_word_counts = {}  # {url: word_count}
subdomains = defaultdict(set)  # {subdomain: set(urls)}
word_frequencies = Counter()
visited_hashes = {}  # {hash(content): url} to detect similar pages
visited_urls = set()  # Stores URLs to detect loops

# Define allowed domains
ALLOWED_DOMAINS = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}

# Patterns that indicate loop-generating URLs
BLOCKED_PATTERNS = [
    r"git/\?p=.*;a=blobdiff",  # Avoid git blobdiff files
    r"git/\?p=.*;a=blob_plain",  # Avoid redundant plaintext versions
    r"git/\?p=.*;a=history",  # Avoid infinite history pages
    r"git/\?p=.*;a=search",  # Avoid infinite search pages
    r"git/\?p=.*;a=commit",  # Avoid endless commit history
    r"git/\?p=.*;a=tree",  # Avoid tree views cycling indefinitely
]

# Load stopwords (to filter common words)
STOPWORDS_FILE = "stopwords.txt"
stopwords = set()
if os.path.exists(STOPWORDS_FILE):
    with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
        stopwords = {line.strip().lower() for line in f if line.strip()}

page_count = 0  # Track number of pages processed


def scraper(url, resp):
    """Processes a page, extracts valid links, and tracks statistics."""
    global page_count
    try:
        if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
            return []

        url, _ = urldefrag(url)
        parsed_url = urlparse(url)

        # Prevent crawling the same page multiple times that leads from different query string variations
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = frozenset(parse_qs(parsed_url.query).items())
        if (normalized_url, query_params) in visited_urls:
            return []
        visited_urls.add((normalized_url, query_params))

        # Prevent known cyclic URL patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, url):
                return []

        if url in unique_urls:
            return []
        unique_urls.add(url)

        tree = html.fromstring(resp.raw_response.content)
        for element in tree.xpath("//script | //style | //noscript"):
            element.getparent().remove(element)

        text = " ".join(tree.xpath("//body//text()"))
        words = re.findall(r"\b[A-Za-z]{2,}\b", text.lower())
        filtered_words = [word for word in words if word not in stopwords]
        word_frequencies.update(filtered_words)
        word_count = len(filtered_words)
        page_word_counts[url] = word_count

        # Avoiding duplicate pages by storing and checking content using hashes
        page_hash = hashlib.md5(text.encode()).hexdigest()
        if page_hash in visited_hashes:
            return []
        visited_hashes[str(page_hash)] = url
        
        # Skipping low-content pages by measuring the word count in the page
        if word_count < 50:
            return []
        
        # Skipping large file
        if len(resp.raw_response.content) > 2_000_000:
            return []

        if parsed_url.netloc.endswith("ics.uci.edu"):
            subdomains[parsed_url.netloc].add(url)

        page_count += 1
        if page_count % 100 == 0:
            save_data(append=True)

        links = extract_next_links(url, tree)
        return [link for link in links if is_valid(link)]

    except Exception as e:
        print(f"Error in scraper: {e}")
        return []


def extract_next_links(url, tree):
    # Extracts and normalizes valid links from a page.
    try:
        links = set()
        for link in tree.xpath("//a/@href"):
            full_url, _ = urldefrag(urljoin(url, link))  # Normalizing & removing fragments
            # Skip event pages with dates in URLs
            if re.search(r"(\?|&)tribe-bar-date=\d{4}-\d{2}-\d{2}", full_url):
                continue
            links.add(full_url)
        return list(links)
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []


def is_valid(url):
    """Determines if a URL should be crawled."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        if parsed.netloc not in ALLOWED_DOMAINS and not parsed.netloc.endswith(tuple(ALLOWED_DOMAINS)):
            return False

        # Detecting Looping URLs like calendars
        if re.search(r"(\?|&)tribe-bar-date=\d{4}-\d{2}-\d{2}", url):  # ICS Calendar trap
            return False

        if re.search(r"(\?|&)(a=history|a=blobdiff|a=commit)", url):  # Git URL loops
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower(),
        )
    except TypeError:
        print(f"TypeError for {parsed}")
        return False


def save_data(append=False):
    # Saves collected data to files for analysis
    mode = "a" if append else "w"

    with open(UNIQUE_URLS_FILE, mode, encoding="utf-8") as f:
        for url in unique_urls:
            f.write(url + "\n")

    with open(PAGE_WORD_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(page_word_counts, f, indent=4)

    with open(ALL_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(word_frequencies.most_common(50), f, indent=4)

    with open(SUBDOMAINS_FILE, "w", encoding="utf-8") as f:
        json.dump({subdomain: len(urls) for subdomain, urls in subdomains.items()}, f, indent=4)

    print("\nData successfully saved!")