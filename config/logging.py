
LOGGING = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(threadName)s - %(levelname)s - %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers':{
        'daily_file': {
            'formatter': 'standard',
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/caldera/caldera_cycle.log',
            'when': 'midnight',
            'interval': 1}
    },
    'loggers':{
        '':{
            'handlers': ['daily_file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}