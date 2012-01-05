'''Simple wrapper around python's logging package'''

import os
import logging

import settings

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOGLEVEL))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.info("Logging initialized")
    return logger

fmt = logging.Formatter("%(asctime)s %(name)s %(module)s.%(funcName)s # %(message)s")

file_handler = logging.FileHandler(os.path.join(settings.LOGDIR, settings.LOGFILE))
file_handler.setFormatter(fmt)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(fmt)