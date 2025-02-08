import os
from utils.pcc_models import Register

def get_cache_server(config, restart):
    print("DEBUG: Running cache server (without multiprocessing)")
    
    # Instead of using `Node()`, return a fake tuple for now
    return ("styx.ics.uci.edu", 9000)  # Use correct port if different
