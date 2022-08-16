# -*- coding: utf-8 -*-

"""
This moduel is a work in progress and therefore unused at the moment. 

This is an attempt to add coloring to logging.
"""

import logging

# All the code below is just to add coloring to our logger. If coloring isn't
# needed, the same result can be achieved with the following:
# logging.basicConfig(
#     format="SIMMATE-%(levelname)-s | %(asctime)-s | %(message)s",
#     level=logging.INFO,
#     datefmt="%Y-%m-%d %H:%M:%S",
# )


class CustomFormatter(logging.Formatter):
    """
    Logging colored formatter, adapted from the following sources:
    https://stackoverflow.com/a/56944256/3638629
    https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/
    """

    # These colors are ANSI escape codes
    # I don't fully understand them, but I used the following script to print
    # out all of the options
    # https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html#256-colors
    #
    # import sys
    # for i in range(0, 16):
    #     for j in range(0, 16):
    #         code = str(i * 16 + j)
    #         sys.stdout.write(u"\u001b[38;5;" + code + "m " + code.ljust(4))
    #     print(u"\u001b[0m")
    #
    # The number corresponds to the final part of the code below (I think)

    debug_color = "\u001b[38;5;13m"  # purple
    info_color = "\u001b[38;5;15m"  # white
    warning_color = "\u001b[38;5;11m"  # yellow
    error_color = "\u001b[38;5;9m"  # red
    critical_color = "\u001b[38;5;9m"  # red
    reset = "\x1b[0m"

    datefmt = "%Y-%m-%d %H:%M:%S"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.debug_color + self.fmt + self.reset,
            logging.INFO: self.info_color + self.fmt + self.reset,
            logging.WARNING: self.warning_color + self.fmt + self.reset,
            logging.ERROR: self.error_color + self.fmt + self.reset,
            logging.CRITICAL: self.critical_color + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


# Create custom logger logging all five levels
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define format for logs
fmt = "[SIMMATE-%(levelname)-s | %(asctime)-s] %(message)s"

# Create stdout handler for logging to the console (logs all five levels)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(CustomFormatter(fmt))

# Add both handlers to the logger
logger.addHandler(stdout_handler)

# Example logging and also for testing.
# logger.debug("this is a debug message")
# logger.info("this is a info message")
# logger.warning("this is a warning message")
# logger.error("this is a error message")
# logger.critical("this is a critical message")
