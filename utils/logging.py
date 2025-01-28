import os
import logging.config

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_LOG_FILE = os.path.join(PROJECT_PATH, 'kb.log')

LOGGING = {
    'version': 1,
    'formatters': {
        'gpt': {
            'format': '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'kb': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'gpt',
            'filename': KB_LOG_FILE
        }
    },
    'loggers': {
        'kb': {
            'handlers': ['kb'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
logging.config.dictConfig(LOGGING)
