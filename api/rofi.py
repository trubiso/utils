import subprocess


def msg(message: str):
    # TODO: align to center
    subprocess.call(
        f'rofi -theme-str "error-message{{}}" -e "{message}"', shell=True)


def ask(
    prompt: str,
    options: list[str] = [],
    *,
    mesg: str | None = None,
    lines: int = 30,
    urgent_rows: list[int] = [],
) -> str | int | None:
    """Shows the prompt on screen with the provided options. Returns which
    option (index) was selected, or if no options were supplied, what was
    typed. Use the `mesg` parameter to specify a submessage. Returns `None` if
    the user quit instead of choosing."""
    mesg = f'-mesg "{mesg}"' if mesg is not None else ""
    theme = '"window{width:1494px;}listview{scrollbar:false;}"'
    urg = ("-u " + ",".join([str(x)
           for x in urgent_rows])) if len(urgent_rows) else ""
    rofi = f"rofi -i -theme-str {theme} -markup-rows {urg} -l {lines}"
    cmd = f'echo -e "{"\n".join(options)
                      }" | {rofi} -dmenu -p "{prompt}" {mesg}'
    try:
        out = subprocess.check_output(cmd, shell=True, text=True)[:-1]
        if len(options):
            return options.index(out)
        else:
            return out
    except Exception:
        return None
