import re
from urllib.parse import urlparse
from urllib.parse import urljoin  # Import urljoin to handle relative links

# make sure to pip install lxml within the project directory
from lxml import html



def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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


    # making sure to only grab links that are valid and have content
    try:
        if resp.status != 200 or not resp.raw_response:
            return []  # Skip if the response is invalid

        tree = html.fromstring(resp.raw_response.content)

        # Getting any links that are in anchor tags
        links = []
        for href in tree.xpath('//a/@href'):
            full_url = urljoin(url, href).split("#")[0]  # Convert relative links and remove fragments
            if full_url not in links:
                links.append(full_url)

        # getting the list of links we crawled. Implement some logic to use for our report
        return links

    # Just some error handling if link is invalid. Could add to display the exact URL that was invalid
    except Exception as e:
        print(f"Error while extracting links")
        return []

# Added some logic (see *) so that the crawler only crawls within the allowed UCI/ICS domains.
def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        #(*) Only crawls the below domains
        domains_allowed = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu", "today.uci.edu"}
        if parsed.netloc not in domains_allowed:
            return False
        
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
