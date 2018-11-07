import click
import time

import google.cloud.logging
cloud_client = google.cloud.logging.Client()

@click.command()
@click.option('--strat-id', '-id', help='Strategy ID to monitor')
@click.option('--user-id', '-u')
@click.option('--mode', '-m')
@click.option('--logger', '-l')
def run(strat_id, user_id, mode, logger):

    FILTER = 'logName:STRATEGY'
    if logger:
        FILTER = f'logName:{logger}'
    if strat_id:
        FILTER += f' AND jsonPayload.strat_id={strat_id}'
    if user_id:
        FILTER += f' AND jsonPayload.user_id={user_id}'
    if mode:
        FILTER += f' AND jsonPayload.mode={mode}'

    iterator = cloud_client.list_entries(filter_=FILTER)
    pages = iterator.pages

    while True:
        try:
            page = next(pages)
            for entry in page:
                click.secho(entry.payload['message'])
        except StopIteration:
            click.secho('No logs, waiting for more')
            time.sleep(5)
