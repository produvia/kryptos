import subprocess

import click

@click.command()
def run():
    subprocess.call(["docker", "exec", "-i", "-t", "web", "/bin/bash",])