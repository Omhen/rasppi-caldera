import ConfigParser
import logging
import os
import os.path
import threading
import time
from datetime import datetime
from config.flags import Status, Watching
import RPIO
import config.flags as flags
from watcher import Watcher


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config/all.conf')
OUT_ENDLESS_FULL_LOAD = getattr(flags, 'OUT_ENDLESS_FULL_LOAD')
OUT_ENDLESS_REGULATED_LOAD = getattr(flags, 'OUT_ENDLESS_REGULATED_LOAD')
OUT_START = getattr(flags, 'OUT_START')
OUT_REGULATED_SPEED = getattr(flags, 'OUT_REGULATED_SPEED')
OUT_CLEANUP_SPEED = getattr(flags, 'OUT_CLEANUP_SPEED')
OUT_ALARM = getattr(flags, 'OUT_ALARM')


logger = logging.getLogger('')


def activate_load():
    RPIO.output(OUT_ENDLESS_FULL_LOAD, False)


def activate_regulated_load():
    RPIO.output(OUT_ENDLESS_FULL_LOAD, True)
    RPIO.output(OUT_ENDLESS_REGULATED_LOAD, False)
    RPIO.output(OUT_START, False)
    RPIO.output(OUT_REGULATED_SPEED, False)


def deactivate_start_and_load():
    RPIO.output(OUT_ENDLESS_FULL_LOAD, True)
    RPIO.output(OUT_ENDLESS_REGULATED_LOAD, True)
    RPIO.output(OUT_START, True)
    RPIO.output(OUT_REGULATED_SPEED, True)


class Cycle(object):

    def __init__(self):
        self.status = Status.STOPPED
        self.runner = threading.currentThread()
        self.start_time = None

        config = ConfigParser.SafeConfigParser()
        config.read(CONFIG_FILE)
        self.CLEANUP_TIME = config.getint('Times', 'cleanup_time')
        self.MAX_START_TIME = config.getint('Times', 'max_start_time')
        self.FULL_LOAD_TIME = config.getint('Times', 'full_load_time')

        self.watcher = Watcher(self)

    def start(self):
        self.runner = threading.current_thread()
        logger.info('Starting cycle on %s' % self.runner.name)
        self.status = Status.RUNNING
        self.start_time = datetime.now()
        activate_load()
        time.sleep(self.FULL_LOAD_TIME)
        if self.status == Status.RUNNING:
            activate_regulated_load()

    def cleanup(self):
        logger.info('Doing cleanup')
        self.status = Status.CLEANING
        deactivate_start_and_load()
        RPIO.output(OUT_CLEANUP_SPEED, False)
        time.sleep(self.CLEANUP_TIME)
        if self.status == Status.CLEANING:
            RPIO.output(OUT_CLEANUP_SPEED, True)
            self.stop()


    def stop(self):
        logger.info('Stopping cycle on %s' % self.runner.name)
        self.status = Status.STOPPED
        if self.watcher.watching == Watching.YES:
            self.watcher.stop_watch()
        deactivate_start_and_load()
        RPIO.output(OUT_CLEANUP_SPEED, True)
        end_time = datetime.now()
        delta = end_time - self.start_time
        logger.info('Ciclo ejecutado durante %f segundos' % delta.total_seconds())

    def start_watch(self):
        self.watcher.start_watch()

    def stop_watch(self):
        self.watcher.stop_watch()

    def alarm(self):
        logger.info('Alarm being raised')
        self.stop()
        self.status = Status.ALARMED
        RPIO.output(OUT_ALARM, False)

    def deactivate_alarm(self):
        self.status = Status.STOPPED
        RPIO.output(OUT_ALARM, True)
