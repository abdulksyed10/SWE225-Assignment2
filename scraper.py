import re
import json
from urllib.parse import urlparse, urljoin, urldefrag
from lxml import html
from collections import defaultdict


unique_urls_file = "unique_urls.txt"
page_word_count_file = "page_word_count.json"
all_words_file = "all_words.txt"
subdomains_and_pages_file = "subdomain_and_page_count.json"

unique_urls = set()
page_word_counts = {}
subdomains = defaultdict(set)


def scraper(url, resp):
    try:
        # Returning empty list of an status code is not 200
        if resp.status != 200:
            return []
        
        # Removing url fragments
        url, _ = urldefrag(url)
        if url in unique_urls:
            return []
        unique_urls.add(url) # adding unique links to the set

        # HTML content parsing using lxml
        tree = html.fromstring(resp.raw_response.content)

        # Extracting just words
        for element in tree.xpath("//script | //style | //noscript"):
            element.getparent().remove(element)
        
        text = " ".join(tree.xpath("//body//text()"))
        words = re.findall(r"\b[A-Za-z]{2,}\b", text)

        # Getting the page count for the longest page in term so number of words (question 2)
        page_word_counts[url] = len(words)

        # Appending all words to all_words.txt to store words for processing in question 3
        with open(all_words_file, "a", encoding="utf-8") as f:
            f.write(" ".join(words) + " ")
        
        # Keeping track of the subdomains
        parsed_url = urlparse(url)
        if parsed_url.netloc.endswith("ics.uci.edu"):
            subdomains[parsed_url.netloc].add(url)
        
        links = extract_next_links(url, resp)
        return [link for link in links if is_valid(link)]

    except Exception as e:
        print(f"Error while running scrapper function: ", e)
        return []

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    try:
        links = set()
        tree = html.fromstring(resp.raw_response.content)

        for link in tree.xpath("//a/@href"):
            full_url, _ = urldefrag(urljoin(url, link))
            links.add(full_url)
        
        return list(links)

    except Exception as e:
        print(f"Error while extracting links: ", e)
        return []

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Only these are the allowed domains
        allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
        if not parsed.netloc.endswith(tuple(allowed_domains)):
            return False
        
        # Only for the today.uci.edu/department/information_computer_sciences/* (we are goig to ignore this path, prof. responded to a student on Ed Discussion as said to ignore it)
        # if not parsed.netloc == "today.uci.edu" and parsed.path.startswith("/department/information_computer_sciences/"):
        #     return False

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
        print ("TypeError for ", parsed)
        raise

def save_data():
    with open(unique_urls_file, "w", encoding="utf-8") as f:
        for url in unique_urls:
            f.write(url + "\n")
    
    with open(page_word_count_file, "w", encoding="utf-8") as f:
        json.dump(page_word_counts, f, indent=4)
    
    subdomain_counts = {subdomain: len(urls) for subdomain, urls in sorted(subdomains.items())}
    with open(subdomains_and_pages_file, "w", encoding="utf-8") as f:
        json.dump(subdomain_counts, f, indent=4)
    
    print("\nData saved successfully!")
    print(f"- Unique URLs saved to `{unique_urls_file}` (TXT)")
    print(f"- Page word counts saved to `{page_word_count_file}` (JSON)")
    print(f"- Words saved to `{all_words_file}` (TXT)")
    print(f"- Subdomains saved to `{subdomains_and_pages_file}` (JSON)")