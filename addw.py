#! /usr/sbin/python
import argparse

import api.anki as anki
import api.dict.cz as cz
import api.rofi as rofi


def ask_ambiguity_rofi(query: str, word: dict) -> str:
    print(word)
    options = [
        f"<b>{key}:</b> {"; ".join(sense["definition"]
                                   for sense in word[key])}"
        for key in word
    ]
    options.append("<i><b>merge:</b> join all parts of speech into unified entry</i>")
    idx = rofi.ask(
        "definition",
        options,
        mesg=f"Found several parts of speech for word '{query}'. Choose which to keep:",
        lines=len(options),
    )
    # If the user chooses None, this will crash, so the operation will be stopped :)
    which = "merge"
    keys = list(word.keys())
    if idx < len(keys):
        which = list(keys)[idx]
    return which


def add_words(lang, words: list[str], use_rofi: bool):
    new_words = [
        word for word in words if not anki.note_exists(lang.deck, word)]
    skipped = len(words) - len(new_words)
    notes_raw, not_found = lang.list_as_note(
        new_words,
        ask_ambiguity=(
            ask_ambiguity_rofi if use_rofi else cz.ask_ambiguity_default),
    )
    output = ""
    if len(not_found) > 0:
        not_found_list = ", ".join(map(lambda x: f"'{x}'", not_found))
        output += f"Did not find {len(not_found)} word(s): {not_found_list}\n"
    if skipped > 0:
        output += f"Skipped {skipped} existing word(s).\n"
    if len(notes_raw) > 0:
        notes = []
        for fields, tags in notes_raw:
            notes.append(
                {"deck": lang.deck, "model": lang.model,
                    "fields": fields, "tags": tags}
            )
        note_ids = anki.add_notes(notes)
        output += f"Added {len(note_ids)} note(s) successfully!\n"
    if use_rofi:
        rofi.msg(output.strip())
    else:
        print(output)


# FIXME: as of rn, words must be of correct case which cannot be guaranteed if selecting. need an option to tell this thing to try.
supported_languages = ["cz", "de", "ru"]
parser = argparse.ArgumentParser(
    prog="addw",
    description="Takes in words, looks them up in a dictionary and adds them to Anki",
)
parser.add_argument(
    "-l",
    "--lang",
    nargs=1,
    type=str,
    choices=supported_languages,
    required=True,
    help="language for the word(s) and destination deck",
)
parser.add_argument(
    "-r",
    "--rofi",
    action="store_true",
    required=False,
    help="prompt through rofi instead of stdout",
)
parser.add_argument(
    "word", action="extend", nargs="+", type=str, help="words to add to the deck"
)
args = parser.parse_args()

lang = args.lang[0]
words = args.word
use_rofi = args.rofi

if lang == "cz":
    add_words(cz, words, use_rofi)
else:
    print(f"Language {lang} is not supported yet!")
