import sys
import logbook
from logbook.more import ColorizedStderrHandler
logger_group = logbook.LoggerGroup()
# logger_group.level = logbook.INFO
logbook.set_datetime_format("local")


def add_logger(logger):
    logger_group.add_logger(logger)
    setup_logging()


def setup_logging(*handlers):
    format_string = '{record.time:%H:%M:%S} KRYPTOS:{record.channel} {record.level_name}: DATE:{record.extra[trade_date]} {record.message}'

    stream_handler = logbook.StreamHandler(sys.stdout, level='INFO', bubble=True)
    stream_handler.format_string = format_string

    stder_handler = ColorizedStderrHandler(level='WARNING', bubble=False)
    stder_handler.format_string = format_string

    file_handler = logbook.RotatingFileHandler('app.log', level='DEBUG', bubble=True, format_string=format_string)

    error_file_handler = logbook.RotatingFileHandler('error.log', level='ERROR', bubble=True)
    error_file_handler.format_string = '''
----------------------------------------------------------------------------------
{record.time:%H:%M:%S} KRYPTOS:{record.channel}:{record.level_name}:

{record.message}

Module: {record.module}:{record.lineno}
Function: {record.func_name}

Channel: {record.channel}
Trade Date: {record.extra[strat_date]}

----------------------------------------------------------------------------------
'''

    setup = logbook.NestedSetup([
        logbook.NullHandler(),
        stream_handler,
        stder_handler,
        file_handler,
        error_file_handler,
        *handlers
    ])

    setup.push_thread()
