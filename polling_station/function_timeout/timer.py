from threading import Thread
import time

class Timer(Thread):
    def __init__(self) -> None:
        super().__init__()
        self.daemon = True
        self.time = self.st = time.time()
    
    def run(self):
        while True:
            self.time = time.time() - self.st
    
    def poll(self):
        return self.time