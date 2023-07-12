from os import getenv

import click as click
from actions_toolkit import core
from testmo_wcli.client import TestmoWebClient
from testmo_wcli.upload import upload, upload_handler

client = TestmoWebClient(getenv("TESTMO_ENDPOINT") or core.get_input("testmo_endpoint"))
client.user = getenv("TESTMO_USER") or core.get_input("testmo_user")
client.password = getenv("TESTMO_PASSWORD") or core.get_input("testmo_password")


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = client


cli.add_command(upload)


if __name__ == "__main__":
    action = core.get_input("action") or "upload"

    if action == "upload":
        upload_handler(
            client=client,
            project_id=core.get_input("project_id"),
            report=core.get_input("report"),
            service=core.get_input("service"),
            version=core.get_input("version"),
            create_milestone=core.get_input("create_milestone"),
            pr=core.get_input("pr"),
            ci_run=core.get_input("ci_run"),
            feature=core.get_input("feature"),
            feature_link=core.get_input("feature_link"),
            features=core.get_input("features"),
        )
