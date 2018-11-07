import click
from kryptos.scripts import build_strategy, stress_worker, kill_strat, stream_logs


@click.group(name="strat")
def cli():
    pass


cli.add_command(build_strategy.run, "build")
cli.add_command(stress_worker.run, "stress")
cli.add_command(kill_strat.run, "kill")
cli.add_command(stream_logs.run, "logs")