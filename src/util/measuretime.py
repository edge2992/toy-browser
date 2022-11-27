import time


class MeasureTime:
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.total_s = 0
        self.count = 0

    def text(self):
        if self.count == 0:
            return ""
        avg = self.total_s / self.count
        return "Time in {} on average: {:>.0f}ms".format(self.name, avg * 1000)

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time is None:
            raise Exception("Timer not started")
        self.total_s += time.time() - self.start_time
        self.count += 1
        self.start_time = None
