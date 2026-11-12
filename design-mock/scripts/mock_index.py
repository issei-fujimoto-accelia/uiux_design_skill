#!/usr/bin/env python3
"""モックの一覧（manifest.js）と注釈（annotations.js）を生成する。

使い方:
    python3 mock_index.py [--root .]

- manifest.js    : screens/*.html（_ で始まるものを除く）の ID、題名、状態、プラットフォームと、ビューポート
- annotations.js : 文書で定義された PSN / UI / CMP / SCR / FLW の表の内容と、画面の詳細設計の「領域」、
                   部品の詳細設計の「構成」の行（注釈の表示に使う）

file:// で開けるように、JSON ではなく window へ代入する JS として出力する。標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../design-review/scripts"))
from design_docs import (  # noqa: E402
    definition_files, design_prefixes, find_definitions, load_config, mock_dir, read_sections,
)


def scr_key(path: str):
    m = re.search(r"SCR-(\d+)", os.path.basename(path))
    return (0, int(m.group(1))) if m else (1, os.path.basename(path))


def screens(mdir: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(mdir, "screens/*.html")), key=scr_key):
        if os.path.basename(p).startswith("_"):
            continue
        text = open(p, encoding="utf-8").read()
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        body = re.search(r"<body([^>]*)>", text)
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', body.group(1))) if body else {}
        platforms = sorted({p for v in re.findall(r'data-platform="([^"]*)"', text) for p in v.split()}) or ["web"]
        title_text = html.unescape(title.group(1).strip()) if title else os.path.basename(p)
        id_ = attrs.get("data-ui") or os.path.splitext(os.path.basename(p))[0]
        out.append({
            "id": id_,
            "title": re.sub(rf"^{re.escape(id_)}\s*", "", title_text),
            "file": "screens/" + os.path.basename(p),
            "states": (attrs.get("data-states") or "default").split(),
            "platforms": platforms,
        })
    return out


def strip_md(s: str) -> str:
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)
    return html.escape(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    cfg, notes = load_config(args.root)
    for n in notes:
        print("NOTE:", n, file=sys.stderr)
    mdir = mock_dir(args.root, cfg)
    os.makedirs(os.path.join(mdir, "assets"), exist_ok=True)

    manifest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "viewports": cfg["design"]["viewports"],
        "screens": screens(mdir),
        "components": "components.html",
    }
    prefixes = set(design_prefixes(cfg)) | {"UI"}
    notes_map = {}
    for d in find_definitions(args.root, definition_files(args.root, cfg), prefixes):
        cells = {k: strip_md(v) for k, v in d.cells.items() if v and k}
        notes_map[d.id] = {"source": os.path.basename(d.file), "cells": cells}
    # 詳細設計の領域（SCR-N/<名前>）と部位（CMP-N/<部位>）
    for key, section in (("screens", "領域"), ("components", "構成")):
        d = os.path.join(args.root, cfg["paths"][key])
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not re.fullmatch(r"(SCR|CMP)-\d+\.md", name):
                continue
            _, secs = read_sections(os.path.join(d, name))
            for row in secs[section].rows() if section in secs else []:
                ui = row.get("data-ui", "").strip("` ")
                if "/" in ui:
                    notes_map[ui] = {"source": name, "cells": {k: strip_md(v) for k, v in row.items() if v and k}}

    with open(os.path.join(mdir, "assets/manifest.js"), "w", encoding="utf-8") as f:
        f.write("// 自動生成（mock_index.py）。直接編集しない。\nwindow.MOCK_MANIFEST = "
                + json.dumps(manifest, ensure_ascii=False, indent=1) + ";\n")
    with open(os.path.join(mdir, "assets/annotations.js"), "w", encoding="utf-8") as f:
        f.write("// 自動生成（mock_index.py）。直接編集しない。\nwindow.MOCK_ANNOTATIONS = "
                + json.dumps(notes_map, ensure_ascii=False, indent=1) + ";\n")
    print(f"screens: {len(manifest['screens'])}, annotations: {len(notes_map)}")


if __name__ == "__main__":
    main()
