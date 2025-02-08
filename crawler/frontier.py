import os
import shelve
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier:
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()

        if os.path.exists(self.config.save_file) and restart:
            print(f"🗑️ Deleting {self.config.save_file} because --restart was set.")
            os.remove(self.config.save_file)

        # Check if the file was really deleted
        if os.path.exists(self.config.save_file):
            print("🚨 Warning: frontier.shelve was NOT deleted!")
        else:
            print("✅ frontier.shelve successfully deleted.")


        # Open the shelve file (it will create a new one if it was deleted)
        self.save = shelve.open(self.config.save_file)

        if restart:
            print("🌱 Adding fresh seed URLs after restart...")
            for url in self.config.seed_urls:
                print(f"🌍 Adding: {url}")
                self.add_url(url)

        else:
            print("📂 Loading existing save file.")
            self._parse_save_file()  # Load previously saved URLs


    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            print(f"📂 Checking saved URL: {url} | Completed: {completed}")  # Debugging
            if not completed and is_valid(url):
                print(f"✅ Adding {url} to the frontier for re-crawling")  # Debugging
                self.to_be_downloaded.append(url)
                tbd_count += 1

        self.logger.info(
            f"Found {tbd_count} URLs to be downloaded from {total_count} total URLs discovered.")



    def get_tbd_url(self):
        if self.to_be_downloaded:
            url = self.to_be_downloaded.pop()
            print(f"📡 Fetching URL for processing: {url}")  # Debugging
            return url
        print("🚫 No URLs available in the frontier!")  # Debugging
        return None



    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        
        if urlhash not in self.save:
            print(f"➕ Adding URL to queue: {url}")  # Debugging
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
        else:
            print(f"🔁 URL already exists: {url}")  # Debugging



    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash in self.save:
            self.save[urlhash] = (url, True)
            self.save.sync()
