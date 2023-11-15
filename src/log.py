import time


class Log():
    def __init__(self, path):
        self.log_path = str(path)
    
    def write(self, text):
        
        event_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        text = f"[{event_time}] {text}\n"
        with open(self.log_path, "a") as f:
            f.write(text)
        
    def clear(self):
        with open(self.log_path, "w") as f:
            f.write("")
    def read(self):
        with open(self.log_path, "r") as f:
            return f.read()