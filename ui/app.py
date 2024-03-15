import os
import json
import time
import datetime
from typing import Tuple, List
from pathlib import Path
from subprocess import Popen, PIPE
import re
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from jinja2 import Template
from streamlit_js_eval import streamlit_js_eval

# setup logger
from logging import getLogger  # nopep8
lg = getLogger(__name__)
# print all logs to stderr anyway
import sys  # nopep8
from logging import StreamHandler, DEBUG  # nopep8
lg.setLevel(DEBUG)
sh = StreamHandler(sys.stderr)
sh.setLevel(DEBUG)
lg.addHandler(sh)


def load_defaults() -> dict:
    with open(os.environ.get("YARUKI_UI_CONFIG", "config.json"), "r", encoding="utf-8") as f:
        j = json.load(f)
        lg.info("loaded defaults: %s", j)
        return j


def init_session_state():
    params = load_defaults()
    for k, v in params.items():
        if k not in st.session_state:
            lg.info("init st.session_state[%s]: %s", k, v)
            st.session_state[k] = v
    lg.info("init st.session_state: %s", st.session_state)


def set_title(layout: str = "centered"):
    st.set_page_config(page_title="やる気", page_icon="app/static/favicon.ico", layout=layout)


def render_footer(dg: DeltaGenerator):
    dg.markdown("<center><footer><p>&#169; 2024 ebiiim</p></footer></center>", unsafe_allow_html=True)


def css_apply():
    css = f"""
<style>
{"\n".join([v for k, v in st.session_state.style["__css"].items()])}
</style>
"""
    print("css:", css)
    st.markdown(css, unsafe_allow_html=True)


def css_registerer(css_generate_func):
    def wrapper(*args, **kwargs):
        if "__css" not in st.session_state.style:
            st.session_state.style["__css"] = {}
        key, css = css_generate_func(*args, **kwargs)
        st.session_state.style["__css"][key] = css
    return wrapper


@css_registerer
def css_register_raw(key: str, css: str) -> Tuple[str, str]:
    return key, css


@css_registerer
def css_register_from_file(fp: str) -> Tuple[str, str]:
    with open(fp, "r", encoding="utf-8") as f:
        return f"__from_file_{fp}", f.read()


@css_registerer
def css_register_radio_grid(label: str, grid_x: int, gap_px: int = 5) -> Tuple[str, str]:
    key = f"__radio_grid_{label}"
    css = f""".stRadio [role="radiogroup"][aria-label="{label}"]{{
    display: grid; /* grid layout */
    grid-template-columns: repeat({grid_x}, 1fr); /* 3 columns per row */
    gap: {gap_px}px; /* space between rows */
}}"""
    return key, css


TIME_FORMATS = [
    # https://docs.python.org/3/library/datetime.html#format-codes
    "%a", "%A", "%w", "%d", "%b", "%B", "%m", "%y", "%Y", "%H", "%I", "%p", "%M", "%S", "%f", "%z", "%Z", "%j", "%U", "%W", "%c", "%x", "%X", "%%",
    "%G", "%u", "%V", "%:z",
    "%-d", "%-m", "%-y", "%-H", "%-I", "%-M", "%-S", "%-j"
]


def format_time(s: str, t: datetime.datetime, fmt: str) -> str:
    return s.replace(fmt, t.strftime(fmt))


def call_preview(msg: str, basedir: str = "..") -> Tuple[str, str, int]:
    cmd = f"npm run --prefix {basedir}/printer --silent preview -- -"
    p = Popen(cmd.split(' '), stdout=PIPE, stdin=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(input=msg.encode("utf-8"))
    return stdout.decode("utf-8"), stderr.decode("utf-8"), p.returncode


def call_print(msg: str, basedir: str = "..") -> Tuple[str, str, int]:
    cmd = f"npm run --prefix {basedir}/printer --silent print -- -"
    p = Popen(cmd.split(' '), stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True)
    stdout, stderr = p.communicate(input=msg)
    return stdout, stderr, p.returncode


def render_print_form(dg: DeltaGenerator):
    c = dg.container()

    pj = c.radio("###### プロジェクト", st.session_state.projects, index=None, horizontal=True)
    css_register_radio_grid("###### プロジェクト", st.session_state.style["projects_per_row"])

    c11, c12 = c.columns(2)
    title = c11.text_input("###### タイトル", placeholder="○○さんのメールに返信する")

    c12.write("###### 表示設定")
    c121, c122 = c12.columns(2)

    hide_receipt_date = c121.checkbox("受付時刻を隠す", value=False)
    no_placeholder = c122.checkbox("空欄そのまま", value=False)
    placeholder_text = "　" if no_placeholder else "********"
    body_large = c121.checkbox("メモを大きく", value=False)

    prio = c.radio("###### 優先度", st.session_state.priorities, index=None, horizontal=True)
    "###### 優先度", css_register_radio_grid("###### 優先度", st.session_state.style["priorities_per_row"])

    dur = c.radio("###### 所要時間", st.session_state.durations, index=None, horizontal=True)
    "###### 所要時間", css_register_radio_grid("###### 所要時間", st.session_state.style["durations_per_row"])

    tA = datetime.datetime.now()
    tA = tA.replace(second=0, microsecond=0)
    tB = tA + datetime.timedelta(days=1)
    tB = tB.replace(hour=19)

    c21, c22 = c.columns(2)

    dl_display = c22.radio("###### いつまで(2)", [d["display"] for d in st.session_state.deadlines], index=None, horizontal=True, label_visibility="collapsed")
    css_register_radio_grid("###### いつまで(2)", st.session_state.style["deadlines_per_row"])

    dl = None
    dl_date_disabled = False
    if dl_display is not None:
        for _, v in enumerate(st.session_state.deadlines):
            if v["display"] == dl_display:
                dl = v
                break
        # check if the deadline format contains any time format (then activate the date input)
        has_time_format = False
        for fmt in TIME_FORMATS:
            if fmt in dl["print"]:
                has_time_format = True
                break
        dl_date_disabled = not has_time_format
    dl_date = c21.date_input("###### いつまで", value=tB, disabled=dl_date_disabled)

    c31, c32 = c.columns(2)
    body = c31.text_area("###### メモ", height=228, placeholder="資料がどっかにあるはず")
    c32.write("###### プレビュー")

    c41, c42, _, _, _, _ = c.columns(6)
    btn_print = c41.button("プリント", type="primary")
    btn_reset = c42.button("リセット")

    # construct print data
    data = {
        "project": "",
        "priority": "",
        "receipt_date": tA.strftime("%m/%d %H:%M") if not hide_receipt_date else placeholder_text,
        "receipt_date_format": "^^^",
        "receipt_date_index_format": "",
        "deadline": placeholder_text,
        "deadline_format": "^^^",
        "deadline_index_format": "",
        "duration": placeholder_text,
        "duration_format": "^^^",
        "duration_index_format": "",
        "title": "",
        "body": "",
        "body_format": "",
        "body_index_format": "\n",
    }

    if pj is not None:
        data["project"] = pj
    if prio is not None:
        data["priority"] = prio

    if title != "":
        data["title"] = title
    if body != "":
        data["body"] = f"{body.replace("\n", "\\n")}"  # escape newline
    if body_large:
        data["body_format"] = "^^"
        data["body_index_format"] = ""

    if dl is not None:
        dl_str = dl["print"]
        for fmt in TIME_FORMATS:  # replace %m, %d, ...
            dl_str = format_time(dl_str, dl_date, fmt)
        data["deadline"] = dl_str

    if dur is not None:
        data["duration"] = dur

    print("data:", data)

    # render print data
    tmpl_str = ""
    with open(st.session_state.print["template_path"], "r", encoding="utf-8") as f:
        tmpl_str = f.read()

    template = Template(source=tmpl_str)
    rendered = template.render(data)
    print("rendered:|-")
    print(rendered)

    # create preview
    sout, serr, ret = call_preview(rendered)
    if ret != 0:
        print("failed to create preview", "code:", ret, "stderr:", serr)

    svgstr = sout
    # resize SVG to fit the container
    svgstr = re.sub(r'<svg width="(.+px)" height="(.+px)"', r'<svg width="280px" height="100%"', svgstr)
    svgstr = svgstr.replace("*", "\*")  # asterisk must be escaped here
    c52c = c32.container(border=True)
    c52c.write(svgstr, unsafe_allow_html=True)

    is_printable = True
    if data["title"] == "":
        is_printable = False

    c_status = c.empty()
    if btn_print:
        if not is_printable:
            c_status.error("タイトルを入力してください")
            time.sleep(2)
            st.rerun()

        c_status.info("印刷中...")
        sout, serr, ret = call_print(rendered)
        if ret != 0:
            c_status.error(f"""
印刷に失敗しました\n
code: `{ret}`\n
stderr:\n
```
{serr}
```
""")
            time.sleep(600)
            st.rerun()

        # save to file
        outdir = Path(st.session_state.print["output_dir"]).resolve()
        if not outdir.exists():
            outdir.mkdir(parents=True)
        # replace illegal characters https://stackoverflow.com/questions/7406102/create-sane-safe-filename-from-any-unsafe-string
        # save to: print-YYYYMMDD-HHHHSS-SUBSEC-<project>-<title>.[svg,receipt]
        out_svg = outdir / re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "_", f"print-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")}-{"_" if data["project"] == "" else data["project"]}-{data["title"]}.svg")
        with open(out_svg, "w", encoding="utf-8") as f:
            f.write(sout)
        out_receipt = outdir / re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "_", f"print-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")}-{"_" if data["project"] == "" else data["project"]}-{data["title"]}.receipt")
        with open(out_receipt, "w", encoding="utf-8") as f:
            f.write(rendered)

        c_status.success("印刷しました")
        time.sleep(2)
        st.rerun()

    if btn_reset:
        streamlit_js_eval(js_expressions="parent.window.location.reload()")


def render_page():

    # init
    init_session_state()
    set_title()

    # render content
    st.write("### やる気")
    c = st.container(border=True)
    render_print_form(c)
    render_footer(st)

    # apply css
    for fp in st.session_state.style["css_paths"]:
        css_register_from_file(fp)
    css_apply()


render_page()
