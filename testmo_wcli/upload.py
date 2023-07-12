import arrow
import click
from junitparser import JUnitXml
from loguru import logger

from testmo_wcli.client import TestmoWebClient, MilestoneType
from testmo_wcli.utils import get_properties


def upload_handler(
    client: TestmoWebClient,
    project_id,
    report,
    service,
    version,
    create_milestone,
    pr,
    ci_run,
    feature,
    feature_link,
    features=features,
):

    client.login()

    name = f"{service} [{version}]"

    if create_milestone:
        logger.debug("Requested milestone creation")
        milestones = client.get_milestones(project=project_id)
        parent = milestones.get(feature)
        logger.debug(f"Feature milestone: {parent}")
        if not parent or parent.get("type") != "feature":
            parent = client.create_milestone(
                project_id, feature, type=MilestoneType.FEATURE
            )

            logger.debug(f"Created feature milestone: {parent}")

            client.add_milestone_link(
                project=project_id,
                milestone=parent.get("id"),
                name="Feature spec",
                target=feature_link,
            )

        milestone = milestones.get(name)
        logger.debug(f"Version milestone: {milestone}")
        if not milestone:
            milestone = client.create_milestone(project_id, name=name, parent=parent)
            logger.debug(f"Created version milestone: {milestone}")
            client.add_milestone_link(
                project=project_id,
                milestone=milestone.get("id"),
                name="Code changes",
                target=pr,
            )

    tags = client.get_tags(project=project_id)
    tests = client.get_tests_by_tag(project_id, tags.get(service))

    logger.debug(f"Tags: {tags}")
    logger.debug(f"Tests: {tests}")

    runs = client.get_runs(project=project_id)

    run = runs.get(name)
    logger.debug(f"Run: {run}")
    if not run:
        run = client.create_run(
            project=project_id,
            name=name or f"Release candidate: {service}[{version}]",
            groups=[],
            cases=list(tests.values()),
            milestone=int(milestone.get("id")),
            tags=[service],
        )
        logger.debug(f"Created run: {run}")

    run_time = arrow.now().format("YYYY-MM-DD HH:mm:ss")
    client.add_run_link(
        project=project_id,
        run=run.get("id"),
        name=f"CI Run [{run_time}]",
        target=ci_run,
    )

    run_tests = client.get_tests_for_run(run=run.get("id"), project=project_id)
    logger.debug(f"Tests from run: {run_tests}")

    testcase_map = {}
    for test_id in run_tests.keys():
        run_tests[test_id] = client.get_test_from_run(run.get("id"), test_id)
        testcase_map[run_tests[test_id].get("case_id")] = test_id

    logger.debug(f"Testcase map: {testcase_map}")

    test_runs = {}
    for suite in JUnitXml.fromfile(report):
        for test in suite:
            properties = get_properties(test._elem.find("properties"))

            test_id = testcase_map.get(properties.get("testcase"))

            if not test_id:
                continue

            if test_id not in test_runs:
                test_runs[test_id] = []

            reason = None
            if test._elem.find("./failure") is not None:
                result = 3
                reason = test._elem.find("./failure").findtext(".")
            elif test._elem.find("./skipped") is not None:
                result = 6
                reason = test._elem.find("./skipped").findtext(".")
            else:
                result = 2

            test_runs[test_id].append(
                {
                    "reason": reason,
                    "result": result,
                    "source": test.classname + "::" + test.name,
                }
            )

    logger.debug(f"Junit results: {test_runs}")

    for test_id, results in test_runs.items():
        for result in sorted(results, key=lambda x: x["result"]):
            client.add_test_result(
                test=test_id,
                reason=result.get("reason"),
                result=result.get("result"),
                source=f"CI [{run_time}] @ " + result.get("source"),
            )


@click.command()
@click.pass_obj
@click.option("--project-id", help="ID of the testmo project", required=True)
@click.option("--service", help="Service name", required=True)
@click.option("--version", help="Version", required=True)
@click.option("--feature", help="Name of the feature")
@click.option("--feature-link", help="Link to the feature definition")
@click.option("--pr", help="PR link")
@click.option("--ci-run", help="CI run link")
@click.option("--create-milestone", is_flag=True, default=False, help="Version")
@click.option("--features", help="Map of the features to include in note")
@click.argument("report", type=click.Path(exists=True))
def upload(
    client: TestmoWebClient,
    project_id,
    report,
    service,
    version,
    create_milestone,
    pr,
    ci_run,
    feature,
    feature_link,
    features,
):
    upload_handler(
        client=client,
        project_id=project_id,
        report=report,
        service=service,
        version=version,
        create_milestone=create_milestone,
        pr=pr,
        ci_run=ci_run,
        feature=feature,
        feature_link=feature_link,
        features=features,
    )
