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
import config.flags as flags
import event_handler


IN_THERMO = getattr(flags, 'IN_THERMO')
IN_START_FLAG = getattr(flags, 'IN_START_FLAG')
IN_RESET_ALARM = getattr(flags, 'IN_RESET_ALARM')
input_list = [IN_THERMO, IN_START_FLAG, IN_RESET_ALARM]


current_cycle_status = None
current_start_status = None
current_alarm_status = None

logger = logging.getLogger('')


def manage_cycle(gpio_id, value):
    global current_cycle_status
    if current_cycle_status == value:
        return
    current_cycle_status = value
    logger.info('manage_cycle: change detected on %d, value %d' % (gpio_id, value))
    event_handler.manage_cycle_event()


def manage_start_time(gpio_id, value):
    global current_start_status
    if current_start_status == value:
        return
    current_start_status = value
    event_handler.manage_start_time_event()


def manage_reset_alarm(gpio_id, value):
    global current_alarm_status
    if current_alarm_status == value:
        return
    current_alarm_status = value
    logger.info('Alarm reset detected %d, value %d' % (gpio_id, value))
    if event_handler.manage_reset_alarm_event():
        global current_cycle_status
        # 'not' bacause True means thermo disabled and tick_cycle_management returns True if thermo enabled
        current_cycle_status = not event_handler.is_thermo_active()
        event_handler.manage_cycle_event()


def main():
    try:
        event_handler.setup()
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


