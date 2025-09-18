import logging

def setup_logging(logger_name: str) -> logging.Logger:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            level=logging.INFO
        )

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger
