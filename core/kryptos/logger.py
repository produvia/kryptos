import os
import sys
import logbook
from logbook.more import ColorizedStderrHandler
from logbook.handlers import StringFormatterHandlerMixin
import google.cloud.logging


from kryptos.settings import LOG_DIR, CLOUD_LOGGING

logger_group = logbook.LoggerGroup()
# logger_group.level = logbook.INFO

logbook.set_datetime_format("utc")

cloud_client = google.cloud.logging.Client()

APP_LOG = os.path.join(LOG_DIR, "app.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")


def add_logger(logger, *handlers):
    logger.handlers.extend(handlers)
    logger_group.add_logger(logger)


class GoogleCloudHandler(logbook.Handler, StringFormatterHandlerMixin):
    def __init__(self, level=0, filter=None, bubble=False, format_string=None):

        logbook.Handler.__init__(self, level, filter, bubble)
        StringFormatterHandlerMixin.__init__(self, format_string)

    def log_to_cloud(self, record):
        cloud_logger = cloud_client.logger(record.channel)
        # StratLogger logs extra info
        if record.channel == "STRATEGY":
            cloud_logger.log_struct(
                {
                    "strat_id": record.extra["strat_id"],
                    "mode": record.extra["mode"],
                    "message": self.format(record),
                    "user_id": record.extra["user_id"],
                },
                severity=record.level_name,
                labels={"channel": record.channel},
            )

        else:
            cloud_logger.log_text(self.format(record), severity=record.level_name)

    def emit(self, record):
        if CLOUD_LOGGING:
            try:
                self.log_to_cloud(record)
            except Exception:
                Warning("Could not emit cloud log")


def setup_logging(*handlers):
    os.makedirs(LOG_DIR, exist_ok=True)

    format_string = "[{record.time:%H:%M:%S}] {record.level_name}: {record.channel}:{record.extra[strat_id]} {record.message}"

    file_handler = logbook.RotatingFileHandler(
        APP_LOG, level="DEBUG", bubble=True, format_string=format_string
    )

    stream_handler = logbook.StreamHandler(sys.stdout, level="INFO", bubble=True)
    stream_handler.format_string = format_string

    cloud_handler = GoogleCloudHandler(level="INFO", bubble=True, format_string=format_string)

    stder_handler = ColorizedStderrHandler(level="WARNING", bubble=False)
    stder_handler.format_string = format_string

    error_file_handler = logbook.RotatingFileHandler(ERROR_LOG, level="ERROR", bubble=True)
    error_file_handler.format_string = """
----------------------------------------------------------------------------------
{record.time:%H:%M:%S} KRYPTOS:{record.channel}:{record.level_name}:

{record.message}

Module: {record.module}:{record.lineno}
Function: {record.func_name}

Channel: {record.channel}
Trade Date: {record.extra[strat_date]}

Exception: {record.formatted_exception}

----------------------------------------------------------------------------------
"""

    setup = logbook.NestedSetup(
        [
            logbook.NullHandler(),
            file_handler,
            stream_handler,
            cloud_handler,
            stder_handler,
            error_file_handler,
            *handlers,
        ]
    )

    setup.push_thread()
    cloud_client.setup_logging()
