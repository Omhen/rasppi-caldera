import ConfigParser
from datetime import datetime, time
import os
import threading
from config.flags import Status
from cycle import Cycle
import logging
import event_handler


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config/all.conf')
logger = logging.getLogger('')


class CycleManager(object):

    def __init__(self):
        self.cycle = None
        self.check_stop_later = None
        config = ConfigParser.SafeConfigParser()
        config.read(CONFIG_FILE)
        self.MIN_CYCLE_TIME = config.getint('Times', 'min_cycle_time')

    def start_cycle(self):
        if not self.cycle or self.cycle.status == Status.STOPPED:
            logger.info('cycle_manager.start_cycle creating new cycle object')
            self.cycle = Cycle()
            runner = threading.Thread(target=self.cycle.start, name='CycleRunner')
            runner.start()
        elif self.cycle.status == Status.ALARMED:
            logger.error('start_cycle: Alarma activada, revisa el estado de la caldera y reinicia programa')
        elif self.cycle.status == Status.RUNNING:
            logger.warn('start_cycle: Ya existe un ciclo en ejecucion. No se puede iniciar uno nuevo hasta que el ciclo actual termine')
        elif self.cycle.status == Status.CLEANING:
            logger.warn('start_cycle: Ciclo acutal haciendo barrido. Imposible iniciar nuevo ciclo hasta que barrido termine')
        else:
            logger.error('start_cycle: Should not have reached this code')

    def stop_cycle(self):
        if not self.cycle or self.cycle.status == Status.STOPPED:
            logger.warn('stop_cycle: No hay ciclos en ejecucion')
        elif self.cycle.status == Status.RUNNING and not event_handler.is_thermo_active():
            delta = datetime.now() - self.cycle.start_time
            logger.info('stop_cycle: delta %f' % delta.total_seconds())
            if delta.total_seconds() < self.MIN_CYCLE_TIME:
                if not self.check_stop_later:
                    self.check_stop_later = \
                        threading.Timer(self.MIN_CYCLE_TIME - delta.total_seconds() + 1,
                                        self.stop_cycle)
                    self.check_stop_later.start()
                return
            #If the thermo is deactivated, start cleanup
            self.check_stop_later = None
            logger.info('Starting cleanup thread')
            cleaner = threading.Thread(target=self.cycle.cleanup, name='CycleCleaner')
            cleaner.start()

    def start_watch(self):
        if self.cycle and self.cycle.status == Status.RUNNING:
            self.cycle.start_watch()

    def stop_watch(self):
        if self.cycle:
            self.cycle.stop_watch()

    def reset_alarm(self):
        if self.cycle and self.cycle.status == Status.ALARMED:
            self.cycle.deactivate_alarm()
            return True
        return False
