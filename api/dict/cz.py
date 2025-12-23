import random
import re
import unicodedata
from collections.abc import Callable

import requests

deck = "CZ"
model = "Czech"


def empty_sense():
    return {"definition": "", "examples": []}


def merge_entries(entries):
    new_entries = {}
    for entry in entries:
        part_of_speech = entry["part_of_speech"]
        sense = entry["sense"]
        if part_of_speech in new_entries:
            new_entries[part_of_speech].append(sense)
        else:
            new_entries[part_of_speech] = [sense]
    return new_entries


def join_senses(sense, other_sense):
    if sense["definition"].endswith(":"):
        sense["definition"] += " " + other_sense["definition"]
    elif sense["definition"].endswith(" "):
        sense["definition"] = (
            sense["definition"][:-1] + ", " + other_sense["definition"]
        )
    elif sense["definition"] == "":
        sense["definition"] = other_sense["definition"]
    else:
        sense["definition"] += ", " + other_sense["definition"]
    sense["examples"].extend(other_sense["examples"])


def process_sense(sense):
    definition: str = sense["definition"]
    examples: list = sense["examples"]
    subsenses = [process_sense(s) for s in sense["subsenses"]]
    sense = {"definition": definition, "examples": examples}
    for subsense in subsenses:
        join_senses(sense, subsense)
    return sense


def bolden_form(example, form):
    punct = "\\.|,|;|:"

    def bolden(matchobj):
        x: str = matchobj.group(0)
        return x.replace(form, f"<b>{form}</b>")

    return re.sub(
        f"(?: {form}(?:$|{punct}))|(?:^{form}(?: |{punct}))|(?: {form} )",
        bolden,
        example,
        flags=re.RegexFlag.IGNORECASE,
    )


def get_word(word):
    request = requests.get(
        "https://freedictionaryapi.com/api/v1/entries/cs/" + word)
    data = request.json()
    entries = data["entries"]
    processed_entries = []
    forms = set()
    forms.add(unicodedata.normalize("NFC", word))
    for entry in entries:
        part_of_speech = entry["partOfSpeech"]
        senses = entry["senses"]
        final_sense = empty_sense()
        for sense in senses:
            join_senses(final_sense, process_sense(sense))
        processed_entry = {
            "part_of_speech": part_of_speech, "sense": final_sense}
        processed_entries.append(processed_entry)
        new_forms = [
            unicodedata.normalize("NFC", form["word"])
            for form in entry["forms"]
            if "table-tags" not in form["tags"]
            and "inflection-template" not in form["tags"]
        ]
        for form in new_forms:
            forms.add(form)
    processed_entries = merge_entries(processed_entries)
    for pos in processed_entries:
        for i, sense in enumerate(processed_entries[pos]):
            for j, example in enumerate(sense["examples"]):
                example = unicodedata.normalize("NFC", example)
                for form in forms:
                    example = bolden_form(example, form)
                processed_entries[pos][i]["examples"][j] = example
    return processed_entries


def ask_ambiguity_default(query: str, word: dict) -> str:
    prompt = f"Found several parts of speech for '{query}': {", ".join(
        [f"'{x}'" for x in word.keys()])}. Choose or merge with 'merge': "
    which = input(prompt)
    while which != "merge" and which not in word:
        print("Invalid input.")
        which = input(prompt)
    return which


def as_note(
    query: str, *, ask_ambiguity: Callable[[str, dict], str] = ask_ambiguity_default
) -> tuple[dict, list[str]] | None:
    global deck
    print(f"Fetching '{query}'...", end="")
    word = get_word(query)
    if len(word.keys()) == 0:
        print(" Error: Not found")
        return None
    else:
        print()
    parts_of_speech = list(word.keys())
    senses = word[parts_of_speech[0]]
    if len(word.keys()) > 1:
        which = ask_ambiguity(query, word)
        if which == "merge":
            senses = []
            for key in word:
                senses.extend(word[key])
        else:
            senses = word[which]
            parts_of_speech = [which]
    else:
        parts_of_speech = [parts_of_speech[0]]

    pos = ", ".join(parts_of_speech)
    fields = {"bare": query, "kind": pos}
    for i, sense in enumerate(senses):
        if i >= 2:
            print(f"Too many definitions ({len(senses)}); taking first 2")
            break
        fields[f"definition{i+1}"] = sense["definition"]
        examples = sense["examples"]
        random.shuffle(examples)
        if len(examples) > 3:
            examples = examples[3:]
        fields[
            f"examples{
                i+1}"
        ] = "\n".join(map(lambda x: f"<li>{x}</li>", examples))

    return fields, parts_of_speech


def list_as_note(
    queries: list[str],
    *,
    ask_ambiguity: Callable[[str, dict], str] = ask_ambiguity_default,
) -> tuple[list[tuple[dict, list[str]]], list[str]]:
    notes = []
    not_found = []
    for query in queries:
        note = as_note(query, ask_ambiguity=ask_ambiguity)
        if note is None:
            not_found.append(query)
        else:
            notes.append(note)
    return notes, not_found
