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
            project_id=core.get_input("project_id") or getenv("TESTMO_PROJECT_ID"),
            report=core.get_input("report") or getenv("TESTMO_REPORT"),
            service=core.get_input("service") or getenv("TESTMO_SERVICE"),
            version=core.get_input("version") or getenv("TESTMO_VERSION"),
            create_milestone=core.get_input("create_milestone") or getenv("TESTMO_CREATE_MILESTONE"),
            pr=core.get_input("pr") or getenv("TESTMO_PR"),
            ci_run=core.get_input("ci_run") or getenv("TESTMO_CI_RUN"),
            feature=core.get_input("feature") or getenv("TESTMO_FEATURE"),
            feature_link=core.get_input("feature_link") or getenv("TESTMO_FEATURE_LINK"),
            issues=core.get_input("issues") or getenv("TESTMO_ISSUES"),
            issues_prefix=core.get_input("issues_prefix") or getenv("TESTMO_ISSUES_PREFIX"),
        )
