import multiprocessing
from configparser import ConfigParser
from argparse import ArgumentParser
from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)

    def main(config_file, restart):
        cparser = ConfigParser()
        cparser.read(config_file)
        config = Config(cparser)

        print(f"🚀 Starting cache server for {config.host}:{config.port}")
        config.cache_server = get_cache_server(config, restart)

        if config.cache_server is None:
            print("❌ ERROR: Cache server did not start. Make sure the Spacetime server is running.")
            return

        print("✅ Cache server started successfully!")
        crawler = Crawler(config, restart)
        crawler.start()

    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)