import logging

def setup_logger():
    logger = logging.getLogger("MajCVE")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
    logger.addHandler(handler)

    return logger
