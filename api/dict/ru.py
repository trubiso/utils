import json

import requests

deck = "RU"
model = "Russian2026"


# FIXME: this terminal implementation does not work, since accented russian words are impossible to type :P
def ask_ambiguity_default(query: str, word: dict) -> str:
    prompt = f"Found several parts of speech for '{query}': {", ".join(
        [f"'{x}'" for x in word.keys()])}. Choose or merge with 'merge': "
    which = input(prompt)
    while which != "merge" and which not in word:
        print("Invalid input.")
        which = input(prompt)
    return which


def actual_accent(ru: str):
    return ru.replace("'", "́")


def process_word_sense(word: dict) -> dict:
    del word["contributions"]
    del word["externalLinks"]
    del word["relateds"]

    bare = word["bare"]
    accented = actual_accent(word["accented"])

    print(f"Processing sense '{accented}'...")

    translations = []
    for translation in word["translations"]:
        for tl in translation["tls"]:
            translations.append(tl)
    translation_main = (
        translations if isinstance(translations, str) else (translations[0] if len(translations) > 0 else "")
    )
    translation_extra = (
        ", ".join(translations[1:]) if not isinstance(translations, str) and len(translations) > 1 else ""
    )

    sample_sentences = []
    for sentence in word["sentences"][:2]:
        start = 0
        end = 0
        for link in sentence["links"]:
            if link["word"]["word"] == query:
                start = link["start"]
                end = link["length"] + start

        ru: str = sentence["ru"]
        unstressed = ru.replace("'", "")
        audio = f"https://api.openrussian.org/read/ru/{unstressed}"
        ru = ru[:start] + "<b>" + ru[start:end] + "</b>" + ru[end:]
        sample_sentences.append(
            {
                "ru": actual_accent(ru),
                "en": sentence["tl"],
                "audio": audio,
            }
        )

    audio = f"https://api.openrussian.org/read/ru/{bare}"

    kind = ""

    if "verb" in word:
        verb = word["verb"]
        kind = f"verb, {verb['aspect']}"
        for partner in verb["partners"]:
            print(f"Suggested word: '{actual_accent(partner)}'")

    if "noun" in word:
        noun = word["noun"]
        gender = noun["gender"]
        animacy = "animate" if noun["animate"] else "inanimate"
        kind = f"noun, {gender}, {animacy}"

    if "adjective" in word:
        adjective = word["adjective"]
        kind = "adjective"
        for adverb in adjective["adverbs"]:
            if isinstance(adverb, dict):
                print(f"Suggested word: '{adverb["bare"]}'")
            else:  # this one doesn't exist in the dictionary
                print(f"Suggested word: '{actual_accent(adverb)}' (not in dictionary)")

    if "adverb" in word:
        adverb = word["adverb"]
        kind = "adverb"
        if not (adverb["adjective"] is None):
            print(f"Suggested word: '{adverb["adjective"]["bare"]}'")

    if kind == "":
        kind = "other"

    tags = kind.split(", ")
    if translation_main == "":
        tags.append("human_review_required")

    return {
        "bare": bare,
        "accented": accented,
        "kind": kind,
        "tags": tags,
        "translation_main": translation_main,
        "translation_extra": translation_extra,
        "audio": audio,
        "sample_sentences": sample_sentences,
    }


def make_note(word: dict) -> tuple[dict, list[str]]:
    bare = word["bare"]
    ssq = len(word["sample_sentences"])
    audio_stuff = [{"url": word["audio"], "filename": f"ru_{bare}.mp3", "fields": ["accented"]}]
    if ssq > 0:
        audio_stuff.append(
            {"url": word["sample_sentences"][0]["audio"], "filename": f"ru_{bare}_ss1.mp3", "fields": ["ss1_ru"]}
        )
    if ssq > 1:
        audio_stuff.append(
            {"url": word["sample_sentences"][1]["audio"], "filename": f"ru_{bare}_ss2.mp3", "fields": ["ss2_ru"]}
        )
    return {
        "bare": bare,
        "accented": word["accented"],
        "kind": word["kind"],
        "translation_main": word["translation_main"],
        "translation_extra": word["translation_extra"],
        "ss1_ru": word["sample_sentences"][0]["ru"] if ssq > 0 else "",
        "ss1_en": word["sample_sentences"][0]["en"] if ssq > 0 else "",
        "ss2_ru": word["sample_sentences"][1]["ru"] if ssq > 1 else "",
        "ss2_en": word["sample_sentences"][1]["en"] if ssq > 1 else "",
    }, word["tags"]


def as_note(
    query: str, *, ask_ambiguity: Callable[[str, dict], str] = ask_ambiguity_default
) -> list[tuple[dict, list[str]]] | None:
    print(f"Fetching '{query}'...", end="")
    if query == "-":
        print(" [skipped]")
        return None
    data = requests.get(f"https://api.openrussian.org/api/words?bare={query}&lang=en")
    json = data.json()

    words = []
    for idx in range(len(json["result"]["words"])):
        word = json["result"]["words"][idx]
        words.append(make_note(process_word_sense(word)))

    if len(words) == 0:
        print(f" Error: Not found")
        return None
    else:
        print()

    which_word = None
    if len(words) > 1:
        word = {}
        which_is_which = {}
        for i, w in enumerate(words):
            # FIXME: this is clunky and ugly
            word[w[0]["accented"]] = [{"definition": w[0]["translation_main"]}]
            which_is_which[w[0]["accented"]] = i
        which = ask_ambiguity(query, word)
        if which == "merge":
            print("Error: merge not supported")
            return None
        else:
            which_word = words[which_is_which[which]]

    return which_word


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
