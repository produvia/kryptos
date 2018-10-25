import click
from kryptos.scripts import build_strategy, stress_worker


@click.group(name="strat")
def cli():
    pass


cli.add_command(build_strategy.run, "build")
cli.add_command(stress_worker.run, "stress")
