import os
import click
import requests


REMOTE_BASE_URL = "https://kryptos-205115.appspot.com"
LOCAL_BASE_URL = "http://web:8080"


@click.command()
@click.argument("strat_id", type=str)
@click.option("--hosted", "-h", is_flag=True, help="Kill on a GCP instance via the API")
def run(strat_id, hosted):
    click.secho(f"Killing strat {strat_id}", fg="yellow")

    resp = kill_from_api(strat_id, hosted=hosted)
    resp.raise_for_status()
    return


def kill_from_api(strat_id, hosted=False):
    click.secho("Killing strat via API", fg="cyan")
    if hosted:
        click.secho("Running remotely", fg="yellow")
        base_url = REMOTE_BASE_URL
    else:
        click.secho("Running locally", fg="yellow")
        base_url = LOCAL_BASE_URL

    api_url = os.path.join(base_url, "api")

    data = {"strat_id": strat_id}

    endpoint = os.path.join(api_url, "strat/delete")
    click.secho(f"Killing strat {strat_id} at {endpoint}", fg="yellow")

    resp = requests.post(endpoint, json=data)
    click.echo(resp)
    return resp
