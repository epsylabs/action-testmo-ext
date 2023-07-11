from os import getenv

import click as click

from testmo_wcli.client import TestmoWebClient
from testmo_wcli.upload import upload

client = TestmoWebClient(getenv("TESTMO_ENDPOINT"))
client.user = getenv("TESTMO_USER")
client.password = getenv("TESTMO_PASSWORD")


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = client


cli.add_command(upload)


if __name__ == "__main__":
    cli()
