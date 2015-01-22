import logging
import RPIO
import config.flags as flags
from cycle_manager import CycleManager


logger = logging.getLogger('')


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

cycle_manager = CycleManager()

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


def pushed(inp):
    return not positive_gt_negative(inp)


def released(inp):
    return positive_gt_negative(inp)


def is_thermo_active():
    return not positive_gt_negative(IN_THERMO)


def is_start_active():
    return not positive_gt_negative(IN_START_FLAG)


def is_alarm_reset_active():
    return positive_gt_negative(IN_RESET_ALARM)


def manage_cycle_event():
    if pushed(IN_THERMO):
        logger.info('event_manager: start_cycle')
        cycle_manager.start_cycle()
    elif released(IN_THERMO):
        logger.info('event_manager: stop_cycle')
        cycle_manager.stop_cycle()
    else:
        logger.info('event_manager.manage_cycle: cannot reach this point')


def manage_start_time_event():
    if pushed(IN_START_FLAG):
        cycle_manager.start_watch()
        return True
    elif released(IN_START_FLAG):
        cycle_manager.stop_watch()
        return False


def manage_reset_alarm_event():
    if pushed(IN_RESET_ALARM):
        return cycle_manager.reset_alarm()
    return False
