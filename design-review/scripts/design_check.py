#!/usr/bin/env python3
"""design の ID とモックの網羅を機械的に検査する。

使い方:
    python3 design_check.py ids     [--root .] [--out <path>]
    python3 design_check.py details [--root .] [--out <path>]
    python3 design_check.py mock    [--root .] [--out <path>]
    python3 design_check.py all     [--root .] [--out <path>]

ids     : design が所有する ID（PSN / UI / CMP / SCR / FLW）の重複定義、所有文書外での定義、
          由来・理由の欠落、未定義の ID への参照、一度も参照されない ID
details : 画面と部品の詳細設計（screens/SCR-N.md、components/CMP-N.md）の有無、必須の節と列、残った「未決」
mock    : 詳細設計とモックの一致（画面と状態、領域の data-ui、部品の要素名と受け取る値、
          カタログの data-example）、トークン外の値（任意値）

終了コード: ERROR があれば 1。標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design_docs import (  # noqa: E402
    ANY_ID_RE, SPECIAL_UPSTREAM_RE, definition_files, design_prefixes, find_definitions, find_references,
    load_config, mock_dir, prefix_of, read_sections, ref_files,
)

REASON_REQUIRED = {"UI", "SCR", "CMP"}


class Report:
    def __init__(self):
        self.items = []  # (level, check, message, where)

    def add(self, level, check, msg, where=""):
        self.items.append((level, check, msg, where))

    def count(self, level):
        return sum(1 for i in self.items if i[0] == level)

    def render(self, title, notes):
        out = [f"# {title}", ""]
        out += [f"> {n}" for n in notes]
        if notes:
            out.append("")
        out.append(f"ERROR: {self.count('ERROR')} / WARN: {self.count('WARN')} / INFO: {self.count('INFO')}")
        out.append("")
        if self.items:
            out += ["| 重大度 | 検査 | 内容 | 場所 |", "|---|---|---|---|"]
            order = {"ERROR": 0, "WARN": 1, "INFO": 2}
            for lv, ck, msg, where in sorted(self.items, key=lambda x: order[x[0]]):
                out.append(f"| {lv} | {ck} | {msg} | {where} |")
        return "\n".join(out) + "\n"


def load_defs(root, cfg):
    by_id = {}
    for d in find_definitions(root, definition_files(root, cfg), set(design_prefixes(cfg))):
        by_id.setdefault(d.id, []).append(d)
    return by_id


def active(by_id, prefix):
    return sorted((i for i, ds in by_id.items() if prefix_of(i) == prefix and not ds[0].retired),
                  key=lambda x: int(x.split("-")[1]))


# ---- 詳細設計 ----
SCREEN_SECTIONS = ["基本", "入口と出口", "領域", "状態", "操作", "文言"]
COMPONENT_SECTIONS = ["基本", "構成", "受け取る値", "状態と変種", "大きさと伸び縮み", "アクセシビリティ", "規則と理由"]
REQUIRED_COLUMNS = {
    ("SCR", "領域"): ["data-ui", "名前", "優先度", "理由"],
    ("SCR", "状態"): ["状態", "きっかけ（固定データの条件）", "表示の違い"],
    ("SCR", "操作"): ["操作", "対象", "反応", "遷移先"],
    ("CMP", "受け取る値"): ["名前", "必須", "既定値", "選べる値"],
    ("CMP", "状態と変種"): ["種類", "名前", "見た目の違い（トークン名）"],
    ("CMP", "構成"): ["部位", "data-ui"],
}
NONE_RE = re.compile(r"該当なし")
PENDING_RE = re.compile(r"未決（design-[a-z]+）")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def detail_path(cfg, kind):
    return cfg["paths"]["screens" if kind == "SCR" else "components"].rstrip("/")


def load_details(root, cfg):
    """{ID: (相対パス, 題名, 節)}。ファイル名が SCR-N.md / CMP-N.md のもの。"""
    out = {}
    for kind in ("SCR", "CMP"):
        d = os.path.join(root, detail_path(cfg, kind))
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            m = re.fullmatch(rf"({kind}-\d+)\.md", name)
            if m:
                rel = f"{detail_path(cfg, kind)}/{name}"
                title, secs = read_sections(os.path.join(root, rel))
                out[m.group(1)] = (rel, title, secs)
    return out


def check_details(root, cfg, rep: Report, by_id=None):
    by_id = by_id if by_id is not None else load_defs(root, cfg)
    details = load_details(root, cfg)
    for kind, required in (("SCR", SCREEN_SECTIONS), ("CMP", COMPONENT_SECTIONS)):
        for id_ in active(by_id, kind):
            if id_ not in details:
                rep.add("ERROR", "詳細設計なし", f"{id_} の詳細設計がない", f"{detail_path(cfg, kind)}/{id_}.md")
        for id_, (rel, title, secs) in details.items():
            if prefix_of(id_) != kind:
                continue
            if id_ not in by_id:
                rep.add("ERROR", "定義のない詳細設計", f"{id_} が一覧で定義されていない", rel)
                continue
            if id_ not in title:
                rep.add("WARN", "題名", f"題名に {id_} がない", rel)
            for name in required:
                sec = secs.get(name)
                if sec is None:
                    rep.add("ERROR", "節なし", f"{id_}：必須の節「{name}」がない", rel)
                    continue
                if not sec.rows() and not NONE_RE.search(sec.text()):
                    rep.add("ERROR", "節が空", f"{id_}：「{name}」が空（当てはまらなければ「該当なし」と書く）", f"{rel}:{sec.line}")
                    continue
                cols = REQUIRED_COLUMNS.get((kind, name))
                if cols and sec.tables:
                    have = set(sec.tables[0][0].keys()) if sec.tables[0] else set()
                    for c in cols:
                        if have and c not in have:
                            rep.add("ERROR", "列なし", f"{id_}：「{name}」に列「{c}」がない", f"{rel}:{sec.line}")
            for sec in secs.values():
                if PENDING_RE.search("\n".join(sec.body)):
                    rep.add("WARN", "未決", f"{id_}：「{sec.title}」に未決が残っている", f"{rel}:{sec.line}")
            if kind == "SCR":
                _check_screen_detail(id_, rel, secs, rep)
            else:
                _check_component_detail(id_, rel, secs, rep)
    return details


def _check_screen_detail(id_, rel, secs, rep):
    seen = set()
    region_rows = secs["領域"].rows() if "領域" in secs else []
    if region_rows and "data-ui" not in region_rows[0]:
        region_rows = []  # 列の不足は check_details で報告済み
    for r in region_rows:
        ui = r.get("data-ui", "").strip("` ")
        if not re.fullmatch(rf"{id_}/[a-z][a-z0-9-]*", ui):
            rep.add("ERROR", "領域の data-ui", f"{id_}：`{ui}` は {id_}/<英小文字とハイフン> にする", rel)
        if ui in seen:
            rep.add("ERROR", "領域の重複", f"{id_}：`{ui}` が重複", rel)
        seen.add(ui)
        if r.get("優先度", "").strip()[:2] not in ("P1", "P2", "P3"):
            rep.add("WARN", "優先度", f"{id_}：`{ui}` の優先度は P1 / P2 / P3", rel)
        if not r.get("理由", "").strip():
            rep.add("WARN", "理由なし", f"{id_}：`{ui}` の理由が空", rel)
    states = [r.get("状態", "").strip("` ") for r in secs["状態"].rows()] if "状態" in secs else []
    if states and "default" not in states:
        rep.add("ERROR", "状態", f"{id_}：状態に default がない", rel)
    for st in states:
        if not NAME_RE.match(st):
            rep.add("ERROR", "状態の名前", f"{id_}：状態 `{st}` は英小文字とハイフンにする（?state= に使う）", rel)
    if "基本" in secs and not any("実装ルート" in r.get("項目", "") for r in secs["基本"].rows()):
        rep.add("WARN", "実装ルート", f"{id_}：「基本」に実装ルートがない", rel)


def _check_component_detail(id_, rel, secs, rep):
    if "基本" in secs:
        tag = next((r.get("内容", "") for r in secs["基本"].rows() if "カスタム要素名" in r.get("項目", "")), "")
        if not re.fullmatch(r"`?[a-z]+-[a-z0-9-]+`?", tag.strip()):
            rep.add("WARN", "カスタム要素名", f"{id_}：「基本」のカスタム要素名（ui-xxx）がない", rel)
    for r in secs["受け取る値"].rows() if "受け取る値" in secs else []:
        n = r.get("名前", "").strip("` ")
        if n and not NAME_RE.match(n):
            rep.add("WARN", "値の名前", f"{id_}：受け取る値 `{n}` はケバブケースにする", rel)
    for r in secs["構成"].rows() if "構成" in secs else []:
        ui = r.get("data-ui", "").strip("` ")
        if ui and ui not in ("―", "-") and not re.fullmatch(rf"{id_}/[a-z][a-z0-9-]*", ui):
            rep.add("ERROR", "部位の data-ui", f"{id_}：`{ui}` は {id_}/<部位> か ― にする", rel)


def detail_rows(details, id_, section, col):
    if id_ not in details or section not in details[id_][2]:
        return []
    return [r.get(col, "").strip("` ") for r in details[id_][2][section].rows() if r.get(col, "").strip("` ")]


def check_ids(root, cfg, rep: Report):
    prefixes = design_prefixes(cfg)
    by_id = load_defs(root, cfg)

    for id_, ds in by_id.items():
        if len(ds) > 1:
            rep.add("ERROR", "重複定義", id_, ", ".join(f"{d.file}:{d.line}" for d in ds))
        for d in ds:
            owners = prefixes[prefix_of(id_)]["owner"]
            if d.file not in owners:
                rep.add("ERROR", "所有文書外の定義", f"{id_} は {', '.join(owners)} で定義する", f"{d.file}:{d.line}")
            if d.retired:
                continue
            up = set(prefixes[prefix_of(id_)]["upstream"])
            found = {prefix_of(m.group(1)) for m in ANY_ID_RE.finditer(d.text) if m.group(1) != id_}
            if not (found & up) and not SPECIAL_UPSTREAM_RE.search(d.text):
                rep.add("WARN", "由来なし", f"{id_}：上流（{', '.join(sorted(up))}、外部:、追加：）がない", f"{d.file}:{d.line}")
            if prefix_of(id_) in REASON_REQUIRED and d.kind == "table":
                reason = next((v for k, v in d.cells.items() if "理由" in k), None)
                if reason is None:
                    rep.add("WARN", "理由の列なし", f"{id_}：表に「理由」列がない", f"{d.file}:{d.line}")
                elif not reason.strip():
                    rep.add("WARN", "理由なし", f"{id_}：理由が空", f"{d.file}:{d.line}")

    refs = find_references(root, ref_files(root, cfg))
    for id_, places in refs.items():
        if prefix_of(id_) not in prefixes or id_ in by_id:
            continue
        rep.add("ERROR", "未定義の参照", id_, ", ".join(f"{f}:{l}" for f, l in places[:5]))

    for id_, ds in by_id.items():
        if ds[0].retired:
            continue
        own = {(d.file, d.line) for d in ds}
        used = [p for p in refs.get(id_, []) if p not in own]
        if not used:
            rep.add("WARN", "参照なし", f"{id_} はどこからも参照されていない", f"{ds[0].file}:{ds[0].line}")
    return by_id


ARBITRARY_RE = re.compile(r"""(?<![\w-])(?:[a-z0-9-]+:)*[a-z][a-z0-9-]*-\[[^\]\s"'`]+\]""")
STYLE_COLOR_RE = re.compile(r'style="[^"]*(#[0-9a-fA-F]{3,8}|rgb\(|hsl\()')


def check_mock(root, cfg, rep: Report, by_id=None, details=None):
    by_id = by_id if by_id is not None else load_defs(root, cfg)
    details = details if details is not None else load_details(root, cfg)
    mdir = mock_dir(root, cfg)
    rel_m = os.path.relpath(mdir, root)
    if not os.path.isdir(mdir):
        rep.add("ERROR", "モックなし", f"{rel_m} がない（design-mock を実行）")
        return

    # 画面：状態と領域を詳細設計と照合する
    for id_ in active(by_id, "SCR"):
        where = f"{rel_m}/screens/{id_}.html"
        f = os.path.join(mdir, "screens", f"{id_}.html")
        if not os.path.exists(f):
            rep.add("ERROR", "画面なし", f"{id_} の画面ファイルがない", where)
            continue
        html = open(f, encoding="utf-8").read()
        if not re.search(rf'data-ui="{id_}"', html):
            rep.add("ERROR", "data-ui なし", f'ルートに data-ui="{id_}" がない', where)
        m = re.search(r'<body[^>]*data-states="([^"]*)"', html)
        declared = set(m.group(1).split()) if m else {"default"}
        want = set(detail_rows(details, id_, "状態", "状態"))
        for st in sorted(want - declared):
            rep.add("ERROR", "状態の不足", f"{id_}：詳細設計の状態 {st} がモックにない", where)
        for st in sorted(declared - want) if want else []:
            rep.add("WARN", "設計にない状態", f"{id_}：状態 {st} が詳細設計にない", where)
        for st in sorted(declared):
            if st != "default" and not re.search(rf'data-state="[^"]*\b{re.escape(st)}\b', html):
                rep.add("WARN", "状態の中身なし", f"{id_}：状態 {st} を宣言しているが data-state の要素がない", where)
        regions = set(detail_rows(details, id_, "領域", "data-ui"))
        used = set(re.findall(rf'data-ui="({id_}/[^"]+)"', html))
        for r in sorted(regions - used):
            rep.add("ERROR", "領域の不足", f'{id_}：data-ui="{r}" がモックにない', where)
        for r in sorted(used - regions):
            rep.add("WARN", "設計にない領域", f'{id_}：data-ui="{r}" が詳細設計にない', where)

    # 部品：要素名、受け取る値、カタログの例を詳細設計と照合する
    comp_js = os.path.join(mdir, "assets/components.js")
    js = open(comp_js, encoding="utf-8").read() if os.path.exists(comp_js) else ""
    catalog = os.path.join(mdir, "components.html")
    cat = open(catalog, encoding="utf-8").read() if os.path.exists(catalog) else ""
    blocks = {}
    for m in re.finditer(r"""defineComponent\(\s*["']([\w-]+)["']\s*,(.*?)(?=defineComponent\(|\Z)""", js, re.S):
        idm = re.search(r"""id:\s*["'](CMP-\d+)["']""", m.group(2))
        if idm:
            blocks[idm.group(1)] = (m.group(1), m.group(2))
    js_rel = f"{rel_m}/assets/components.js"
    for id_ in active(by_id, "CMP"):
        if id_ not in blocks:
            rep.add("ERROR", "部品なし", f"{id_} が components.js で定義されていない", js_rel)
        else:
            tag, body = blocks[id_]
            want_tag = next((r.get("内容", "").strip("` ") for r in (details[id_][2]["基本"].rows()
                             if id_ in details and "基本" in details[id_][2] else []) if "カスタム要素名" in r.get("項目", "")), "")
            if want_tag and want_tag != tag:
                rep.add("WARN", "要素名", f"{id_}：components.js は {tag}、詳細設計は {want_tag}", js_rel)
            for prop in detail_rows(details, id_, "受け取る値", "名前"):
                camel = re.sub(r"-([a-z])", lambda x: x.group(1).upper(), prop)
                pats = [rf"\ba\.{camel}\b", rf"""["']{prop}["']\s+in\s+a\b""", rf"""a\[["']{camel}["']\]"""]
                if not any(re.search(p_, body) for p_ in pats):
                    rep.add("WARN", "値の未使用", f"{id_}：受け取る値 {prop} を render で使っていない", js_rel)
            for part in detail_rows(details, id_, "構成", "data-ui"):
                if part.startswith(id_ + "/") and f'data-ui="{part}"' not in body:
                    rep.add("WARN", "部位なし", f'{id_}：data-ui="{part}" が render にない', js_rel)
        sec = re.search(rf'<section[^>]*\bid="{id_}"[^>]*>(.*?)</section>', cat, re.S)
        if not sec:
            rep.add("WARN", "カタログなし", f'{id_} の節（<section id="{id_}">）が components.html にない', f"{rel_m}/components.html")
            continue
        examples = {e for v in re.findall(r'data-example="([^"]*)"', sec.group(1)) for e in v.split()}
        for name in detail_rows(details, id_, "状態と変種", "名前"):
            if name not in examples:
                rep.add("WARN", "例なし", f'{id_}：状態と変種 {name} の例（data-example）がカタログにない', f"{rel_m}/components.html")
    for id_ in sorted(blocks):
        if id_ not in by_id:
            rep.add("ERROR", "未定義の部品", f"components.js の {id_} が文書で定義されていない", js_rel)

    # トークン外の値
    for dirpath, _, files in os.walk(mdir):
        for name in files:
            if not name.endswith((".html", ".js")) or name in ("mock-kit.js", "manifest.js", "annotations.js") or name.startswith("_"):
                continue
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
                if line.strip().startswith(("//", "<!--", "*", "/*")):
                    continue
                for m in ARBITRARY_RE.finditer(line):
                    if "-[var(" in m.group(0):
                        continue
                    rep.add("WARN", "任意値", f"`{m.group(0)}`：トークン由来のクラスを使う", f"{rel}:{i}")
                if STYLE_COLOR_RE.search(line):
                    rep.add("WARN", "直接指定の色", "style 属性で色を指定している", f"{rel}:{i}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ids", "details", "mock", "all"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    args = ap.parse_args()
    cfg, notes = load_config(args.root)
    rep = Report()
    by_id = details = None
    if args.cmd in ("ids", "all"):
        by_id = check_ids(args.root, cfg, rep)
    if args.cmd in ("details", "all"):
        details = check_details(args.root, cfg, rep, by_id)
    if args.cmd in ("mock", "all"):
        check_mock(args.root, cfg, rep, by_id, details)
    text = rep.render(f"design_check {args.cmd}", notes)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        open(args.out, "w", encoding="utf-8").write(text)
    sys.stdout.write(text)
    sys.exit(1 if rep.count("ERROR") else 0)


if __name__ == "__main__":
    main()
