import os
import shelve
import time
from threading import RLock
from queue import Queue
from urllib.parse import urlparse

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = Queue()
        self.domain_last_access = {}  # Tracks last access time per domain
        self.lock = RLock()

        if not os.path.exists(self.config.save_file) and not restart:
            self.logger.info(f"Did not find save file {self.config.save_file}, starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            self.logger.info(f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)

        self.save = shelve.open(self.config.save_file)
        
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.put(url)
                tbd_count += 1
        self.logger.info(f"Found {tbd_count} URLs to be downloaded from {total_count} total URLs discovered.")

    def get_tbd_url(self):
        """Retrieves the next URL while enforcing politeness."""
        with self.lock:
            while not self.to_be_downloaded.empty():
                url = self.to_be_downloaded.get()
                domain = urlparse(url).netloc
                
                # Enforce politeness delay (500ms = 0.5s)
                last_access = self.domain_last_access.get(domain, 0)
                elapsed_time = time.time() - last_access
                
                if elapsed_time < 0.5:
                    time.sleep(0.5 - elapsed_time)  # Wait to enforce politeness
                
                self.domain_last_access[domain] = time.time()
                return url
        return None

    def add_url(self, url):
        """Adds a URL to the frontier if it's new."""
        with self.lock:
            url = normalize(url)
            urlhash = get_urlhash(url)
            if urlhash not in self.save:
                self.save[urlhash] = (url, False)
                self.save.sync()
                self.to_be_downloaded.put(url)

    def mark_url_complete(self, url):
        """Marks a URL as completed."""
        with self.lock:
            urlhash = get_urlhash(url)
            if urlhash not in self.save:
                self.logger.error(f"Completed URL {url}, but have not seen it before.")
            self.save[urlhash] = (url, True)
            self.save.sync()