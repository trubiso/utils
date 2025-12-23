import json
import subprocess
import time
import requests

base_url = "http://127.0.0.1:8765"
version = 5
version_ensured = False


def send_request(action: str, params: dict = {}):
    r = requests.post(
        base_url,
        json.dumps(
            {
                "action": action,
                "version": version,
                "params": params,
            }
        ),
    )
    response = r.json()
    if response["error"]:
        raise Exception(response["error"])
    else:
        return response["result"]


def ensure_anki():
    try:
        out = subprocess.check_output('pgrep -af "/usr/sbin/anki"', shell=True)
        print(out)
    except Exception:
        subprocess.Popen(
            "anki",
            shell=False,
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=True,
        )
        time.sleep(5)  # wait until Anki is open


def ensure_version():
    global version_ensured
    if version_ensured:
        return
    ensure_anki()
    send_request("version")
    version_ensured = True


def deck_names() -> list[str]:
    ensure_version()
    return send_request("deckNames")


def ensure_deck(deck: str):
    if deck not in deck_names():
        raise Exception(f"Deck '{deck}' not found!")


def model_names() -> list[str]:
    ensure_version()
    return send_request("modelNames")


def ensure_model(model: str):
    if model not in model_names():
        raise Exception(f"Model '{model}' not found!")


def model_field_names(model: str) -> list[str]:
    ensure_version()
    return send_request("modelFieldNames", {"modelName": model})


def ensure_model_fields(model: str, fields: list[str]):
    field_names = model_field_names(model)
    for field in fields:
        if field not in field_names:
            raise Exception(f"Field '{field}' not in model '{model}'!")


def add_note(deck: str, model: str, fields: dict, tags: list[str] = []) -> int:
    ensure_version()
    ensure_deck(deck)
    ensure_model(model)
    ensure_model_fields(model, list(fields.keys()))

    return send_request(
        "addNote",
        {
            "note": {
                "deckName": deck,
                "modelName": model,
                "fields": fields,
                "tags": tags,
            }
        },
    )


def add_notes(notes: dict) -> list[int]:
    ensure_version()
    actual_notes = []
    for note in notes:
        if (
            "deck" not in note
            or "model" not in note
            or "fields" not in note
            or "tags" not in note
        ):
            raise Exception(f"Ill-formed note '{note}'!")
        deck: str = note["deck"]
        model: str = note["model"]
        fields: dict = note["fields"]
        tags: list[str] = note["tags"]
        ensure_deck(deck)
        ensure_model(model)
        ensure_model_fields(model, list(fields.keys()))
        actual_notes.append(
            {
                "deckName": deck,
                "modelName": model,
                "fields": fields,
                "tags": tags,
            }
        )

    return send_request("addNotes", {"notes": actual_notes})


def find_notes(query: str) -> list[int]:
    ensure_version()
    return send_request("findNotes", {"query": query})


def note_exists(deck: str, bare: str) -> bool:
    return len(find_notes(f"deck:{deck} bare:{bare}")) > 0
