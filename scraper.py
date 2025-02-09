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

# Define allowed domains
ALLOWED_DOMAINS = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}

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

        page_hash = hashlib.md5(text.encode()).hexdigest()
        if page_hash in visited_hashes:
            print(f"⚠️ Skipping duplicate/similar page: {url}")
            return []
        visited_hashes[page_hash] = url

        if word_count < 50:
            print(f"⚠️ Skipping low-content page: {url}")
            return []

        if len(resp.raw_response.content) > 2_000_000:
            print(f"⚠️ Skipping large file: {url}")
            return []

        parsed_url = urlparse(url)
        if parsed_url.netloc.endswith("ics.uci.edu"):
            subdomains[parsed_url.netloc].add(url)

        page_count += 1
        if page_count % 100 == 0:
            save_data(append=True)

        links = extract_next_links(url, tree)
        return [link for link in links if is_valid(link)]

    except Exception as e:
        print(f"❌ Error in scraper: {e}")
        return []


def save_data(append=False):
    """Saves collected data to files for analysis."""
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

    print("\n✅ Data successfully saved!")
