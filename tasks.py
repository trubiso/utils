#! /usr/sbin/python
import argparse

import api.rofi as rofi
import api.todoist as todoist

total_cols = 147


def ask_tasks(tasks: list[dict], *, separate_dates: bool = False) -> int:
    global total_cols
    text_tasks = []
    urgent_rows = []
    col_qty = 6
    for i, task in enumerate(tasks):
        if separate_dates and i > 0 and tasks[i - 1]["date"] != task["date"]:
            text_tasks.append(None)
        project = task["project"]
        section = task["section"]
        section = f"/{section}" if section is not None else ""
        labels = [f"@{label}" for label in task["labels"]]
        recurring = task["recurring"]
        date = task["date"]
        priority = task["priority"]
        content = task["content"]
        content = content.replace('`', '\'')
        date_info = ("* " if recurring else "") + date
        if task["overdue"]:
            urgent_rows.append(len(text_tasks))

        cols = []
        cols.append(f"{priority}")
        cols.append(content)
        cols.append(f"#{project}")
        cols.append(section)
        cols.append(" ".join(labels))
        cols.append(date_info)
        assert len(cols) == col_qty
        text_tasks.append(cols)

    max_lens = [
        max(map(lambda x: len(x[i]) if x else 0, text_tasks)) for i in range(col_qty)
    ]
    inter_col = "  "
    final_pad = total_cols - \
        (sum(max_lens[:-1]) + len(inter_col) * (col_qty - 1))

    priority_colors = ["#dc322f", "#ffc600", "#0000ff", "#000000"]

    final_tasks = []
    fillers = 0
    for i, task in enumerate(text_tasks):
        if task is None:
            final_tasks.append("─" * total_cols)
            fillers += 1
            continue
        cols = [
            col.ljust(max_lens[i]) if i + 1 < col_qty else col.rjust(final_pad)
            for i, col in enumerate(task)
        ]
        text_task = inter_col.join(cols)
        assert len(text_task) >= total_cols
        priority = tasks[i - fillers]["priority"]
        color = priority_colors[priority - 1]
        text_task = text_task.replace("&", "&amp;")
        text_task = f"<span background='{
            color}' bgalpha='20%'>{text_task}</span>"
        final_tasks.append(text_task)

    idx = rofi.ask(
        "tasks", final_tasks, lines=min(30, len(final_tasks)), urgent_rows=urgent_rows
    )

    if idx is None:
        return

    actual_idx = 0
    for i, task in enumerate(text_tasks):
        if task is None:
            continue
        if i == idx:
            break
        actual_idx += 1

    todoist.complete_task(tasks[actual_idx]["id"])


# TODO: support cli
parser = argparse.ArgumentParser(
    prog="tasks",
    description="Displays and manages Todoist tasks through rofi",
)
parser.add_argument(
    "mode", choices=["get", "add", "quest"], help="specifies the mode of the program"
)
parser.add_argument(
    "-w",
    "--when",
    type=str,
    choices=["today", "future"],
    required=False,
    default="today",
    help="in the 'get' mode, specifies date",
)
args = parser.parse_args()

match args.mode:
    case "get":
        tasks = []
        match args.when:
            case "today":
                tasks = todoist.get_tasks("date before: tomorrow")
                if not len(tasks):
                    rofi.msg("No tasks left for today.")
                    exit()

                tasks.sort(key=lambda x: x["order"])
                tasks.sort(key=lambda x: x["priority"])
            case "future":
                tasks = todoist.get_tasks("date after: today")
                if not len(tasks):
                    rofi.msg("No tasks after today.")
                    exit()

                tasks.sort(key=lambda x: x["order"])
                tasks.sort(key=lambda x: x["priority"])
                tasks.sort(key=lambda x: x["date"])
        ask_tasks(tasks, separate_dates=(not args.when == "today"))
    case "add":
        text = rofi.ask("add task", lines=0)
        if text is not None:
            todoist.add_task(text)
    case "quest":
        # FIXME: Todoist won't let me do #Quest board. the # filter is broken
        tasks = todoist.get_tasks(
            "/Languages | /Music | /Programming * | /Other")
        tasks.sort(key=lambda x: x["created"])
        tasks.sort(
            key=lambda x: (
                x["section"].replace("Other", "ZZZOther")
                if x["section"].endswith("Other")
                else x["section"]
            )
        )
        task_names = [
            task["content"]
            + " "
            * (
                total_cols
                - len(task["content"])
                - len(task["section"])
                - 3
                - len("YYYY-MM-DD")
            )
            + "/"
            + task["section"]
            + "  "
            + task["created"]
            for task in tasks
        ]
        which = rofi.ask("embark", task_names, lines=min(30, len(task_names)))
        if which is not None:
            id = tasks[which]["id"]
            todoist.update_task(id, {"due_string": "tod"})
