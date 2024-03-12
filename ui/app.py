import os
import json
import time
import datetime
from typing import Tuple
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
    c.write("###### プロジェクト")
    pjs = []  # selected projects [bool, ...]
    c01, c02, c03, c04 = c.columns(4)
    for idx, pj in enumerate(st.session_state["projects"]):
        if idx % 4 == 0:
            pjs.append(c01.checkbox(pj))
        if idx % 4 == 1:
            pjs.append(c02.checkbox(pj))
        if idx % 4 == 2:
            pjs.append(c03.checkbox(pj))
        if idx % 4 == 3:
            pjs.append(c04.checkbox(pj))

    title = c.text_input("###### タイトル", placeholder="○○さんのメールに返信する")

    c.write("###### 優先度")
    c21, c22, c23, c24, = c.columns(4)
    prios = []  # selected priorities [bool, ...]
    for idx, prio in enumerate(st.session_state["priorities"]):
        if idx % 4 == 0:
            prios.append(c21.checkbox(prio))
        if idx % 4 == 1:
            prios.append(c22.checkbox(prio))
        if idx % 4 == 2:
            prios.append(c23.checkbox(prio))
        if idx % 4 == 3:
            prios.append(c24.checkbox(prio))

    c.write("###### 所要時間")
    c31, c32, c33, c34, c35, c36 = c.columns(6)
    d10 = c31.checkbox("10分")
    d30 = c32.checkbox("30分")
    d120 = c33.checkbox("2時間")
    dhd = c34.checkbox("半日")
    d1d = c35.checkbox("1日")
    d3d = c36.checkbox("3日")

    tA = datetime.datetime.now()
    tA = tA.replace(second=0, microsecond=0)
    tB = tA + datetime.timedelta(days=1)
    tB = tB.replace(hour=19)

    c11, c12, c13, c14 = c.columns(4)
    c12.write("")  # spacer
    c13.write("")  # spacer
    c14.write("")  # spacer
    due_today = c12.checkbox("**本日中**")
    due_tomorrow = c13.checkbox("**明日中**")
    due_week = c14.checkbox("**今週中**")
    due_asa = c12.checkbox("朝イチ")
    due_gogo = c13.checkbox("午後イチ")
    due_teiji = c14.checkbox("定時", value=True)
    due_date_disabled = True if due_today or due_tomorrow or due_week else False
    due_date = c11.date_input("###### 締切日", value=tB, disabled=due_date_disabled)

    c51, c52, _ = c.columns(3)
    body = c51.text_area("###### 本文", height=210, placeholder="資料がどっかにあるはず")

    c41, c42, _, _, _, _ = c.columns(6)
    btn_print = c41.button("印刷", type="primary")
    btn_reset = c42.button("リセット")

    # construct print data
    data = {
        "project": "",
        "priority": "",
        "receipt_date": tA.strftime("%m/%d %H:%M"),
        "due_date": "********",
        "time_required": "********",
        "title": "",
        "body": "",
    }

    if title != "":
        data["title"] = title
    if body != "":
        data["body"] = f"{body}"

    for idx, pj in enumerate(st.session_state["projects"]):
        if pjs[idx]:
            data["project"] = f"{pj}"
    for idx, prio in enumerate(st.session_state["priorities"]):
        if prios[idx]:
            data["priority"] = f"{prio}"

    if due_today:
        data["due_date"] = "`本日中`"
    elif due_tomorrow:
        data["due_date"] = "`明日中`"
    elif due_week:
        data["due_date"] = "`今週中`"
    elif due_asa:
        data["due_date"] = f"`{due_date.strftime("%m/%d")} 朝イチ`"
    elif due_gogo:
        data["due_date"] = f"`{due_date.strftime("%m/%d")} 午後イチ`"
    elif due_teiji:
        data["due_date"] = f"`{due_date.strftime("%m/%d")} 定時`"

    if d10:
        data["time_required"] = "10分"
    elif d30:
        data["time_required"] = "30分"
    elif d120:
        data["time_required"] = "2時間"
    elif dhd:
        data["time_required"] = "半日"
    elif d1d:
        data["time_required"] = "1日"
    elif d3d:
        data["time_required"] = "3日"

    print("current data:", data)

    # render print data
    tmpl_str = ""
    with open(st.session_state.config["template_path"], "r", encoding="utf-8") as f:
        tmpl_str = f.read()

    template = Template(source=tmpl_str)
    rendered = template.render(data)
    print("rendered:|-")
    print(rendered)

    # create preview
    sout, serr, ret = call_preview(rendered)
    if ret != 0:
        print("failed to create preview", "code:", ret, "stderr:", serr)

    c52.write("###### プレビュー")
    svgstr = sout
    # resize SVG to fit the container
    svgstr = re.sub(r'<svg width="(.+px)" height="(.+px)"', r'<svg width="280px" height="100%"', svgstr)
    c52.write(svgstr, unsafe_allow_html=True)

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
            c_status.error(f"印刷に失敗しました code: `{ret}`, stderr: ```{serr}```")
            time.sleep(600)
            st.rerun()

        # save SVG
        outdir = Path(st.session_state.config["print_svg_dir"]).resolve()
        if not outdir.exists():
            outdir.mkdir(parents=True)
        outfile = outdir / f"print_{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}.svg"
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(sout)

        c_status.success("印刷しました")
        time.sleep(2)
        st.rerun()

    if btn_reset:
        streamlit_js_eval(js_expressions="parent.window.location.reload()")


def render_page():

    init_session_state()
    set_title()

    st.write("### やる気")

    c = st.container(border=True)
    render_print_form(c)

    render_footer(st)


render_page()
