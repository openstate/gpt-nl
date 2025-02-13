import os
import logging.config

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_LOG_FILE = os.path.join(PROJECT_PATH, 'kb.log')
OBK_LOG_FILE = os.path.join(PROJECT_PATH, 'officiele_bekendmakingen.log')
PBL_LOG_FILE = os.path.join(PROJECT_PATH, 'pbl.log')
NATURALIS_LOG_FILE = os.path.join(PROJECT_PATH, 'naturalis.log')
EP_LOG_FILE = os.path.join(PROJECT_PATH, 'ep.log')

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
        },
        'obk': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'gpt',
            'filename': OBK_LOG_FILE
        },
        'pbl': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'gpt',
            'filename': PBL_LOG_FILE
        },
        'naturalis': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'gpt',
            'filename': NATURALIS_LOG_FILE
        },
        'ep': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'gpt',
            'filename': EP_LOG_FILE
        }

    },
    'loggers': {
        'kb': {
            'handlers': ['kb'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'obk': {
            'handlers': ['obk'],
            'level': 'INFO',
            'propagate': False,
        },
        'pbl': {
            'handlers': ['pbl'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'naturalis': {
            'handlers': ['naturalis'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ep': {
            'handlers': ['ep'],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
}
logging.config.dictConfig(LOGGING)
