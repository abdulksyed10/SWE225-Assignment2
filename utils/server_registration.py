import os
import multiprocessing
from spacetime import Node
from utils.pcc_models import Register

def init(df, user_agent, fresh):
    """Ensures that user agent registration runs correctly."""
    reg = df.read_one(Register, user_agent)
    if not reg:
        reg = Register(user_agent, fresh)
        df.add_one(Register, reg)
        df.commit()
        df.push_await()
    while not reg.load_balancer:
        df.pull_await()
        if reg.invalid:
            raise RuntimeError("User agent string is not acceptable.")
        if reg.load_balancer:
            df.delete_one(Register, reg)
            df.commit()
            df.push()
    return reg.load_balancer

def get_cache_server(config, restart):
    """Starts spacetime cache server properly for multiprocessing on Windows."""
    multiprocessing.set_start_method("spawn", force=True)

    try:
        if __name__ == "__main__":
            print(f"🔍 Attempting to connect to cache server at {config.host}:{config.port}")
            init_node = Node(init, Types=[Register], dataframe=(config.host, config.port))
            cache_server = init_node.start(config.user_agent, restart or not os.path.exists(config.save_file))

            if cache_server is None:
                print("❌ ERROR: Cache server returned None. Check server availability.")
            return cache_server
    except Exception as e:
        print(f"🔥 Exception in get_cache_server(): {e}")
    
    return None
