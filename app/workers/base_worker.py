import threading
import time


class BaseWorker:
    """Base class for a worker that runs in its own thread."""
    def __init__(self, name: str):
        self.name = name
        self.thread_ref = None
        self.running=True

    def setup(self):
        "Setup method to be overridden by subclasses"
        pass

    def process(self):
        "Process method to be overridden by subclasses"
        pass
    
    def run(self):
        "Loop wrapper that runs inside a thread"
        self.thread_ref = threading.current_thread()
        self.setup() 
        print(f"{self.name} running in thread {self.thread_ref.name}")

        while self.running:
            try:
                self.process()
            except Exception as e:
                print(f"Error in {self.name} process: {e}")

            time.sleep(1)  

    def stop(self):
        "Signal the worker to stop"
        self.running = False
        print(f"{self.name} stopping...")

    