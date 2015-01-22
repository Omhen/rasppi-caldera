from datetime import datetime
import time
import threading
from config.flags import Watching
import logging


logger = logging.getLogger('')


class Watcher(object):

    def __init__(self, cycle):
        self.cycle = cycle
        self.max_time = cycle.MAX_START_TIME
        self.watching = Watching.NO
        self.start_time = None
        self.thread = None

    def start_watch(self):
        self.watching = Watching.YES
        self.start_time = datetime.now()
        if not self.thread or not self.thread.isAlive():
            self.thread = threading.Thread(target=self.watch_tick, name='CycleWatcher')
            self.thread.start()

    def watch_tick(self):
        logger.info('Watching the cycle')
        while True:
            time.sleep(0.5)
            if self.watching == Watching.NO:
                return
            current_time = datetime.now()
            delta = current_time - self.start_time
            if delta.total_seconds() >= self.max_time:
                self.cycle.alarm()
                return

    def stop_watch(self):
        logger.info('Stopping watch')
        self.watching = Watching.NO
