import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

base_url = "https://api.todoist.com/api/v1"


def send_request(url: str, *, get: dict = {}, post: dict | None = None) -> dict:
    url = base_url + url
    added_first = False
    for key in get:
        if get[key] is None:
            continue
        url += "&" if added_first else "?"
        added_first = True
        url += f"{key}={get[key]}"
    headers = {"Authorization": f"Bearer {os.environ["TODOIST_TOKEN"]}"}
    r = (
        requests.post(url, post, headers=headers)
        if post is not None
        else requests.get(url, headers=headers)
    )
    try:
        response = r.json()
        if "error" in response:
            raise Exception(
                f"HTTP code {response["http_code"]}: ({response["error_code"]}) {
                    response["error"]}"
            )
        return response
    except Exception:
        return {}


def get_projects() -> dict:
    projects = {}
    for project in send_request("/projects")["results"]:
        id = project["id"]
        name = project["name"]
        projects[id] = name
    return projects


def get_sections() -> dict:
    sections = {}
    for section in send_request("/sections")["results"]:
        id = section["id"]
        name = section["name"]
        sections[id] = name
    return sections


def get_tasks(filter: str = "today") -> list[dict]:
    projects = get_projects()
    sections = get_sections()

    tasks = []
    today = datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d")

    results = []
    old_cursor = None
    for _ in range(10):
        new_results = send_request("/tasks/filter", get={"query": filter, "cursor": old_cursor})
        results.extend(new_results["results"])
        old_cursor = new_results["next_cursor"]
        if old_cursor is None:
            break

    if old_cursor is not None:
        print("Too many paginations, quitting")

    for result in results:
        id = result["id"]
        project_id = result["project_id"]
        section_id = result["section_id"]
        project = projects[project_id]
        section = sections[section_id] if section_id is not None else None
        labels = result["labels"]
        priority = 5 - result["priority"]
        content = result["content"].replace('"', '\\"')
        order = result["day_order"]
        if result["due"] is not None:
            date = result["due"]["date"][: len("YYYY-MM-DD")]
            is_recurring = result["due"]["is_recurring"]
            overdue = datetime.strptime(date, "%Y-%m-%d") < today
        else:
            date, is_recurring, overdue = None, False, False
        added_at = (
            result["added_at"][: len("YYYY-MM-DD")] if result["added_at"] else None
        )

        tasks.append(
            {
                "id": id,
                "order": order,
                "project": project,
                "section": section,
                "labels": labels,
                "date": date,
                "recurring": is_recurring,
                "overdue": overdue,
                "priority": priority,
                "created": added_at,
                "content": content,
            }
        )
    return tasks


def add_task(text: str):
    send_request("/tasks/quick", post={"text": text})


def complete_task(id: str):
    send_request(f"/tasks/{id}/close", post={})


def update_task(id: str, params: object):
    send_request(f"/tasks/{id}", post=params)
