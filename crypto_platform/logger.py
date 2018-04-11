import sys
import logbook

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

    file_handler = logbook.RotatingFileHandler('app.log', level='DEBUG', bubble=True, format_string=format_string)

    error_file_handler = logbook.RotatingFileHandler('error.log', level='ERROR', bubble=True)
    error_file_handler.format_string = '''\
    Application Error at {record.filename}:{record.lineno}

    Message type:       {record.level_name}
    Location:           {record.filename}:{record.lineno}
    Module:             {record.module}
    Function:           {record.func_name}
    Time:               {record.time:%Y-%m-%d %H:%M:%S}

    channel     {record.channel}

    Trade Date: {record.extra[strat_date]}

    Message:

    {record.message}
    '''

    setup = logbook.NestedSetup([
        logbook.NullHandler(),
        stream_handler,
        file_handler,
        error_file_handler,
        *handlers
    ])

    setup.push_thread()
