from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker

class Crawler:
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.worker = worker_factory(0, self.config, self.frontier)  # Single worker

    def start(self):
        self.worker.run()
