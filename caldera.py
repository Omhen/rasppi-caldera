#!/usr/bin/python
"""
Basic led + push button circuit. When the button is pushd, the led is turned on.
"""
from datetime import datetime, timedelta
import logging.config
import logging
import threading

import RPIO
import time
from config import logging as conf_logging
from cycle import Cycle
import config.flags as flags


OUT_ENDLESS_FULL_LOAD = getattr(flags, 'OUT_ENDLESS_FULL_LOAD')
OUT_ENDLESS_REGULATED_LOAD = getattr(flags, 'OUT_ENDLESS_REGULATED_LOAD')
OUT_START = getattr(flags, 'OUT_START')
OUT_REGULATED_SPEED = getattr(flags, 'OUT_REGULATED_SPEED')
OUT_CLEANUP_SPEED = getattr(flags, 'OUT_CLEANUP_SPEED')
OUT_ALARM = getattr(flags, 'OUT_ALARM')
output_list = [OUT_ENDLESS_FULL_LOAD, OUT_ENDLESS_REGULATED_LOAD, OUT_START,
               OUT_REGULATED_SPEED, OUT_CLEANUP_SPEED, OUT_ALARM]

IN_THERMO = getattr(flags, 'IN_THERMO')
IN_START_FLAG = getattr(flags, 'IN_START_FLAG')
IN_RESET_ALARM = getattr(flags, 'IN_RESET_ALARM')
input_list = [IN_THERMO, IN_START_FLAG, IN_RESET_ALARM]


cycle = None
current_cycle_status = None
current_start_status = None
current_alarm_status = None

logger = logging.getLogger('')


def setup():
    RPIO.setmode(RPIO.BOARD)
    for out in output_list:
        logger.info('Setting as output %d' % out)
        RPIO.setup(out, RPIO.OUT, initial=RPIO.HIGH)
    for inp in input_list:
        RPIO.setup(inp, RPIO.IN)


def positive_gt_negative(inp):
    positive, negative = 0, 0
    for _ in xrange(5000):
        if RPIO.input(inp):
            positive += 1
        else:
            negative += 1
    #print "Positive: ", positive, " Negative: ", negative
    return positive > negative


def pushed(value, inp):
    if not value and not positive_gt_negative(inp):
        return True
    return False


def released(value, inp):
    if value and positive_gt_negative(inp):
        return True
    return False


def manage_cycle(gpio_id, value):
    global cycle
    global current_cycle_status
    if current_cycle_status == value:
        return
    current_cycle_status = value
    logger.debug('Detectado cambio %d, value %d' % (gpio_id, value))
    if released(value, IN_THERMO):
        if cycle:
            if cycle.status == flags.Status.RUNNING:
                cleaner = threading.Thread(target=cycle.cleanup, name='CycleCleaner')
                cleaner.start()
            elif cycle.status == flags.Status.CLEANING:
                cycle.stop()
                cycle = None
    elif pushed(value, IN_THERMO):
        if cycle and cycle.status == flags.Status.ALARMED:
            logger.error('Alarma activada, revisar estado de caldera y reiniciar programa')
            return
        if cycle:
            cycle.stop()
        cycle = Cycle()
        runner = threading.Thread(target=cycle.start, name='CycleRunner')
        runner.start()


def manage_start_time(gpio_id, value):
    global cycle
    global current_start_status
    if current_start_status == value:
        return
    current_start_status = value
    if not cycle:
        return
    if pushed(value, IN_START_FLAG):
        #The startup process began, so start monitoring it ends in a timely manner
        cycle.start_watch()
    elif released(value, IN_START_FLAG):
        cycle.stop_watch()


def manage_reset_alarm(gpio_id, value):
    global cycle
    global current_alarm_status
    if current_alarm_status == value:
        return
    current_alarm_status = value
    if pushed(value, IN_RESET_ALARM):
        if cycle and cycle.status == flags.Status.ALARMED:
            cycle.deactivate_alarm()
            global current_cycle_status
            current_cycle_status = None
            manage_cycle(IN_THERMO, RPIO.input(IN_THERMO))


def main():
    try:
        setup()
        time.sleep(1)
        manage_cycle(IN_THERMO, RPIO.input(IN_THERMO))
        RPIO.add_interrupt_callback(IN_THERMO, manage_cycle, threaded_callback=False)
        RPIO.add_interrupt_callback(IN_START_FLAG, manage_start_time, threaded_callback=False)
        RPIO.add_interrupt_callback(IN_RESET_ALARM, manage_reset_alarm, threaded_callback=False)
        RPIO.wait_for_interrupts()
    except KeyboardInterrupt as k:
        RPIO.cleanup()


if __name__ == '__main__':
    logging.config.dictConfig(conf_logging.LOGGING)
    main()


