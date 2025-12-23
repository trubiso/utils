# utils

contains several utils i have bound to certain keys in my linux setup, related
to language learning and task management.

the APIs are in the `api/` folder, the utilities are in the root folder.

in order to use these utilities, a `.env` file must be created with a
`TODOIST_TOKEN` entry.

## addw

`addw` adds the specified word(s) in the specified language to the
corresponding [Anki][anki] deck.

* to specify the language of the word(s) and corresponding Anki deck, use the
`-l`/`--lang` parameter with its corresponding name (`cz`, `de` or `ru`; only
`cz` is implemented as of right now)

* to output through [rofi][rofi] instead of stdout, use the `-r`/`--rofi` flag.

finally, specify a list of space-separated words (use quotes for words which
contain spaces). the words will all be fetched from the dictionary first and
then added in bulk to Anki.

the currently supported dictionary APIs are the following:

* [FreeDictionaryAPI](https://freedictionaryapi.com/), which gives access to a
powerful enough subset of Wiktionary, currently used for `cz`.

## tasks

`tasks` manages [Todoist][todoist] tasks through [rofi][rofi]. it supports
three modes:

* the `get` mode, which comes with an additional `-w`/`--when` parameter
(either `today` or `future`, defaults to `today` if not specified). shows all
the tasks in the specified time frame. if any of them is selected, it is
completed.

* the `add` mode, which asks for text input and adds the task to Todoist.

* the `quest` mode, which fetches tasks from the quest board, and if any task
is selected, sets its due date to today.


[anki]: https://apps.ankiweb.net/
[rofi]: https://github.com/davatorium/rofi
[todoist]: https://www.todoist.com/
