import os
import logging
from logging.handlers import RotatingFileHandler
import logging_config

def test_root_logger_has_rotating_file_handler():
    """
    Test that the root logger has a RotatingFileHandler writing to the expected log file.
    This test ensures that the logging configuration is set up correctly and that
    the log file is being written to as expected.
    """

    # Clear out any handlers pytest or other libs already put on the root logger
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    # Invoke our setup_logging (it will unconditionally add the two handlers)
    logging_config.setup_logging()  # :contentReference[oaicite:0]{index=0}

    # Assert that at least one RotatingFileHandler writing to our log file is present
    log_basename = os.path.basename(logging_config.LOG_FILE)
    assert any(
        isinstance(h, RotatingFileHandler)
        and os.path.basename(h.baseFilename) == log_basename
        for h in root.handlers
    ), f"No RotatingFileHandler writing to {log_basename} found on root.handlers"