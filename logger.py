'''Simple wrapper around python's logging package'''

import os
import logging

try:
    import settings
except ImportError:
    # This is shared module, but settings are necessary only for server side
    settings = None
    
def get_logger(name):
    logger = logging.getLogger(name)
    logger.addHandler(stream_handler)

    if settings:
        logger.setLevel(getattr(logging, settings.LOGLEVEL))
        logger.addHandler(file_handler)
    
    logger.info("Logging initialized")
    return logger

fmt = logging.Formatter("%(asctime)s %(name)s %(module)s.%(funcName)s # %(message)s")

if settings:
    file_handler = logging.FileHandler(os.path.join(settings.LOGDIR, settings.LOGFILE))
    file_handler.setFormatter(fmt)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(fmt)