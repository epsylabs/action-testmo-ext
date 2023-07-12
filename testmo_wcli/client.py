from enum import Enum

import click
import mechanicalsoup as mechanicalsoup
import requests as requests
from requests.adapters import TimeoutSauce
from bs4 import BeautifulSoup


class MyTimeout(TimeoutSauce):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("connect", 5)
        kwargs.setdefault("read", 5)
        super(MyTimeout, self).__init__(*args, **kwargs)


requests.adapters.TimeoutSauce = MyTimeout


class MilestoneType(Enum):
    RELEASE = 1
    VERSION = 2
    SPRINT = 3
    ITERATION = 4
    PLAN = 5
    CYCLE = 6
    FEATURE = 7


class RunState(Enum):
    NEW = 6
    IN_PROGRESS = 7
    UNDER_REVIEW = 8
    REJECTED = 9
    DONE = 10

    def __repr__(self):
        return self.value


class MilestoneType(Enum):
    RELEASE = 1
    VERSION = 2
    FEATURE = 7


def milestone_type(classes):
    if "fa-box-open" in classes:
        return "feature"
    if "fa-dot-circle" in classes:
        return "version"
    else:
        return "default"


class TestmoWebClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.browser = mechanicalsoup.StatefulBrowser(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        )
        self.user = None
        self.password = None

    def login(self, user=None, password=None):
        self.browser.open(self.endpoint + "/auth/login")
        try:
            self.browser.select_form(".ui.large.form")
            self.browser["email"] = self.user or user
            self.browser["password"] = self.password or password
            self.browser.submit_selected()
            self.csrf = self.browser.page.select_one('meta[name="csrf-token"]').get(
                "content"
            )
        except Exception as e:
            click.secho("Failed to login to testmo", fg="red")

    def create_milestone(self, project, name, type=MilestoneType.VERSION, parent=None):
        data = {
            "name": name,
            "note": "",
            "parent_id": int(parent.get("id")) if parent else None,
            "type_id": type.value,
            "automation_tags": [],
            "due_date": "",
            "docs": None,
            "issues": [],
            "start_date": "",
        }

        response = self.browser.post(
            self.endpoint + f"/milestones/create/{project}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return response.json()

    def get_milestones(self, project):
        response = self.browser.get(
            self.endpoint + f"/milestones/{project}",
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        l1 = {
            item.get("data-name"): {
                "id": item.get("data-id"),
                "name": item.get("data-name"),
                "started": item.get("data-started"),
                "type": milestone_type(
                    item.select_one(".avatar__text__identifier i").get("class")
                ),
            }
            for item in response.soup.select(".milestones-list-item")
        }
        l2 = {
            item.get("data-name"): {
                "id": item.get("data-id"),
                "name": item.get("data-name"),
                "started": item.get("data-started"),
                "type": milestone_type(
                    item.select_one(".avatar__text__identifier i").get("class")
                ),
            }
            for item in response.soup.select(".milestones-sub-list-item")
        }

        return {**l1, **l2}

    def add_milestone_link(self, project, milestone, name, target):
        data = {"name": name, "url": target, "note": ""}
        return self.browser.post(
            self.endpoint + f"/milestones/create_link/{milestone}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

    def add_run_link(self, project, run, name, target):
        data = {"name": name, "url": target, "note": ""}
        return self.browser.post(
            self.endpoint + f"/runs/create_link/{run}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

    def get_tags(self, project):
        response = self.browser.post(
            self.endpoint + f"/repositories/render_case_filter/{project}",
            json={"mode": 1, "conditions": {}},
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )
        tags = BeautifulSoup(
            response.soup.select_one('div[data-name="repository_cases:tags"]').get(
                "data-condition"
            ),
            "html.parser",
        )

        return {
            tag.get("data-label").strip(): int(tag.get("data-id").strip())
            for tag in tags.select("tr")
        }

    def get_tests_by_tag(self, project, tag):
        if not tag:
            return {}

        data = {
            "force_group": True,
            "case_id": None,
            "pagination_current": 1,
            "pagination_rows": 250,
            "group_by": "repository_cases:custom_priority",
            "group_id": None,
            "columns": {"repository_cases:custom_priority": {"width": 200}},
            "filter": {
                "mode": 1,
                "conditions": {"repository_cases:tags": {"values": [tag]}},
            },
        }

        result = self.browser.post(
            self.endpoint + f"/repositories/render_tree_group_containers/{project}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return {
            t.get("data-name"): int(t.get("data-id"))
            for t in result.soup.select_one(
                "table[data-target='components--table.table']"
            ).select("tr[data-id]")
        }

    def get_tests_for_run(self, project, run):
        data = {
            "test_id": None,
            "group_by": "repository_cases:state_id",
            "group_id": 4,
            "columns": {"repository_cases:custom_priority": {"width": 200}},
            "filter": None,
        }

        result = self.browser.post(
            self.endpoint + f"/runs/render_tree_group_containers/{run}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return {
            t.get("data-id"): t.get("data-name")
            for t in result.soup.select("tr[data-id]")
        }

    def add_test_result(self, test, result, source, reason=None):
        comment = [f"<p>Source: {source}</p>"]
        if reason:
            comment.append(f"<code>{reason}</code>")

        return self.browser.post(
            self.endpoint + f"/runs/create_result/{test}",
            json={
                "comment": "\n".join(comment),
                "assignee_id": None,
                "status_id": result,
                "attachments": [],
                "issues": [],
            },
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

    def get_runs(self, project):
        result = self.browser.post(
            self.endpoint + f"/runs/render_active/{project}",
            json={"tables": [], "selected": []},
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return {
            i.get("data-name"): {"id": i.get("data-id"), "name": i.get("data-name")}
            for i in result.soup.select("tr[data-id]")
        }

    def get_milestone_links(self, project, milestone):
        result = self.browser.get(
            self.endpoint + f"/milestones/view/{milestone}",
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return {
            i.select_one(".split-resource-list__item__title__content a").text.strip(): {
                "id": i.get("data-id"),
                "name": i.select_one(
                    ".split-resource-list__item__title__content a"
                ).text.strip(),
            }
            for i in result.soup.select("div.split-resource-list__item")
        }

    def create_run(
        self,
        project,
        name,
        groups,
        tags: list,
        milestone=None,
        config=None,
        cases: list = None,
        state: RunState = RunState.NEW,
    ):
        data = {
            "name": name,
            "config_id": config,
            "milestone_id": milestone,
            "state_id": state.value,
            "tags": tags,
            "docs": None,
            "include_all": (len(tags) + len(groups)) == 0,
            "cases": cases or [],
            "issues": [],
        }
        result = self.browser.post(
            self.endpoint + f"/runs/create/{project}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        return result.json()

    def get_test_from_run(self, run, test_id):
        data = {
            "test_id": int(test_id),
            "group_by": "run_tests:status_id",
            "group_id": 1,
            "columns": {"repository_cases:custom_priority": {"width": 200}},
            "filter": None,
        }

        result = self.browser.post(
            self.endpoint + f"/runs/render_test_container/{run}",
            json=data,
            headers={
                "X-CSRF-TOKEN": self.csrf,
            },
        )

        properties = result.soup.select_one("div.runs-test-properties")

        return dict(
            case_id=properties.get("data-case-id"),
            name=properties.get("data-name"),
            test_id=properties.get("data-id"),
        )
