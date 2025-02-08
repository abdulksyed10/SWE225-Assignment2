from threading import Thread
from utils.download import download
from utils import get_logger
import scraper
import time

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)

    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            self.logger.info(f"Worker {self.name} processing URL: {tbd_url}")

            resp = download(tbd_url, self.config, self.logger)
            print(f"📥 Downloading: {tbd_url} | Status: {resp.status}")  # Debugging
            if resp.status != 200:
                self.logger.warning(f"Worker {self.name} received non-200 status ({resp.status}) for {tbd_url}")
                continue
            
            scraped_urls = scraper.scraper(tbd_url, resp)
            self.logger.info(f"Worker {self.name} extracted {len(scraped_urls)} new URLs from {tbd_url}")

            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)

            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
