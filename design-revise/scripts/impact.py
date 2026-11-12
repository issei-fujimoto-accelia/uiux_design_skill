#!/usr/bin/env python3
"""変更の影響範囲（影響する画面と部品）を列挙する。

使い方:
    python3 impact.py [--root .] --id CMP-2 [--id SCR-3 ...] [--token color.primary ...]
    python3 impact.py [--root .] --git        # git の作業中の差分（docs/D2/）から変更対象を求める

対象ごとの考え方:
    CMP-N  : 詳細設計の領域でその部品を使う画面、モックでその部品の要素を使う画面、
             その部品を中に含む部品（とそれを使う画面）、部品カタログ
    SCR-N  : その画面、遷移でつながる画面（詳細設計の入口と出口・操作、モックのリンク）、経由する FLW
    UI-N   : その規則を適用した画面と部品（モックの data-rules、部品の rules、詳細設計の「規則」列、部品の由来）
    FLW-N  : そのシナリオが経由する画面（FLW の定義、詳細設計の「関わるシナリオ」）
    トークン : モックでそのトークンのクラスや CSS 変数を使う画面と部品（部品なら、それを使う画面も）

出力：影響範囲の表（Markdown）と、shoot.py の --screens に渡せる画面の一覧。標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../design-review/scripts"))
from design_check import (  # noqa: E402
    SCR_RE, active, component_blocks, load_defs, load_details, read_mock, usage_map,
)
from design_docs import load_config, prefix_of  # noqa: E402

# トークンのグループ → ユーティリティの接頭辞（tokens.py の対応と合わせる）
UTIL = {
    "color": r"(?:bg|text|border|outline|ring|fill|stroke|from|to|via|divide|placeholder|caret|accent|decoration|shadow)",
    "font": r"font", "text": r"text", "weight": r"font", "leading": r"leading", "tracking": r"tracking",
    "radius": r"rounded(?:-[trbl]{1,2})?", "shadow": r"shadow", "ease": r"ease", "breakpoint": None,
}
VAR_NS = {"weight": "font-weight"}


class Impact:
    def __init__(self):
        self.items: dict[str, list[str]] = {}

    def add(self, target, reason):
        lst = self.items.setdefault(target, [])
        if reason not in lst:
            lst.append(reason)


def token_patterns(path: str):
    parts = path.split(".")
    group, rest = parts[0], "-".join(parts[1:])
    var = f"--{VAR_NS.get(group, group)}" + (f"-{rest}" if rest else "")
    pats = [re.compile(rf"\(\s*{re.escape(var)}\s*\)|var\(\s*{re.escape(var)}\s*\)")]
    if group == "spacing" and not rest:
        return None  # 余白の基準値は全体に効く
    if group == "breakpoint" and rest:
        pats.append(re.compile(rf"(?<![\w-]){re.escape(rest)}:"))
    elif UTIL.get(group) and rest:
        pats.append(re.compile(rf"(?<![\w-])(?:[a-z0-9-]+:)*{UTIL[group]}-{re.escape(rest)}(?![\w-])"))
    return pats


def top_level_consts(js: str) -> dict:
    """行頭の `const NAME = …;` を、括弧の対応を見て文ごとに切り出す。"""
    out = {}
    for m in re.finditer(r"(?m)^const\s+(\w+)\s*=", js):
        depth, i = 0, m.end()
        while i < len(js):
            c = js[i]
            if c in "{[(":
                depth += 1
            elif c in "}])":
                depth -= 1
            elif c == ";" and depth == 0:
                break
            i += 1
        out[m.group(1)] = js[m.start():i + 1]
    return out


def git_targets(root: str, cfg: dict):
    """作業中の差分から (ID の集合, トークンのパスの集合) を求める。"""
    def git(*a):
        return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True)
    if git("rev-parse", "--is-inside-work-tree").returncode:
        sys.exit("ERROR: git のリポジトリではありません。--id か --token で指定してください。")
    files = set(git("diff", "--name-only", "HEAD", "--", "docs/D2").stdout.split())
    files |= set(git("ls-files", "--others", "--exclude-standard", "docs/D2").stdout.split())
    ids, tokens = set(), set()
    for f in sorted(files):
        m = re.search(r"(SCR-\d+|CMP-\d+)\.(md|html)$", f)
        if m:
            ids.add(m.group(1))
        elif f.endswith("components.js"):
            old = git("show", f"HEAD:{f}").stdout
            new = open(os.path.join(root, f), encoding="utf-8").read() if os.path.exists(os.path.join(root, f)) else ""
            a, b = component_blocks(old), component_blocks(new)
            ids |= {c for c in set(a) | set(b) if a.get(c) != b.get(c)}
        elif f.endswith("design-tokens.json"):
            def flat(d, p=""):
                out = {}
                for k, v in (d or {}).items():
                    if k.startswith("$"):
                        continue
                    if isinstance(v, dict):
                        q = f"{p}.{k}" if p else k
                        if "$value" in v:
                            out[q] = json.dumps({kk: vv for kk, vv in v.items() if kk.startswith("$")}, sort_keys=True)
                        out.update(flat(v, q))
                return out
            old = git("show", f"HEAD:{f}").stdout
            a = flat(json.loads(old)) if old.strip() else {}
            b = flat(json.load(open(os.path.join(root, f), encoding="utf-8")))
            tokens |= {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        elif f.endswith((".md",)):
            diff = git("diff", "-U0", "HEAD", "--", f).stdout
            for line in diff.splitlines():
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                    ids |= set(re.findall(r"(?<![\w-])((?:SCR|CMP|UI|FLW)-\d+)(?![\d-])", line))
    return ids, tokens, sorted(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--id", action="append", default=[])
    ap.add_argument("--token", action="append", default=[])
    ap.add_argument("--git", action="store_true")
    args = ap.parse_args()
    cfg, _ = load_config(args.root)
    by_id = load_defs(args.root, cfg)
    details = load_details(args.root, cfg)
    mock = read_mock(args.root, cfg)
    screens, js, _ = mock
    um = usage_map(args.root, cfg, by_id, details, mock)
    blocks = component_blocks(js)
    # 定義の外にある定数（変種の対応表など）を、それを参照する部品の本文に含める
    consts = top_level_consts(js)
    blocks = {cid: (tag, body + "".join(t for n, t in consts.items() if re.search(rf"\b{n}\b", body)))
              for cid, (tag, body) in blocks.items()}
    imp = Impact()

    ids, tokens = set(args.id), set(args.token)
    changed_files = []
    if args.git:
        gi, gt, changed_files = git_targets(args.root, cfg)
        ids |= gi
        tokens |= gt
    if not ids and not tokens:
        sys.exit("対象がありません。--id、--token、--git のいずれかを指定してください。")

    def add_component(cid, reason):
        imp.add(cid, reason)
        imp.add("部品カタログ", f"{cid} を含む")
        u = um.get(cid, {"regions": set(), "mock": set()})
        for sid in sorted(u["regions"]):
            imp.add(sid, f"{cid} を領域で使う")
        for sid in sorted(u["mock"] - u["regions"]):
            imp.add(sid, f"{cid} をモックで使う")
        tag = blocks.get(cid, ("", ""))[0]
        for other, (_, body) in blocks.items():
            if other != cid and tag and re.search(rf"<{re.escape(tag)}[\s>]", body) and other not in imp.items:
                add_component(other, f"{cid} を中に含む")

    for id_ in sorted(ids):
        if prefix_of(id_) == "CMP":
            add_component(id_, "変更対象")
        elif prefix_of(id_) == "SCR":
            imp.add(id_, "変更対象")
            for sid in active(by_id, "SCR"):
                if sid == id_:
                    continue
                linked = re.search(rf'href="[^"]*{id_}\.html', screens.get(sid, ""))
                in_doc = sid in details and any(
                    id_ in " ".join(r.values()) for n in ("入口と出口", "操作")
                    for r in (details[sid][2][n].rows() if n in details[sid][2] else []))
                if linked or in_doc:
                    imp.add(sid, f"{id_} と遷移でつながる")
            for fid, ds in by_id.items():
                if prefix_of(fid) == "FLW" and id_ in SCR_RE.findall(ds[0].text):
                    imp.add(fid, f"{id_} を経由する")

    for id_ in sorted(i for i in ids if prefix_of(i) == "UI"):
        imp.add(id_, "変更対象")
        pat = re.compile(rf"(?<![\w-]){re.escape(id_)}(?![\d-])")
        for sid, html in screens.items():
            if any(pat.search(v) for v in re.findall(r'data-rules="([^"]*)"', html)):
                imp.add(sid, f"{id_} を適用（モック）")
        for cid, (_, body) in blocks.items():
            if re.search(rf"""rules:\s*\[[^\]]*["']{re.escape(id_)}["']""", body) or \
               any(pat.search(v) for v in re.findall(r'data-rules="([^"]*)"', body)):
                add_component(cid, f"{id_} を適用（モック）")
        for did, (rel, _, secs) in details.items():
            hit = False
            if prefix_of(did) == "SCR" and "領域" in secs:
                hit = any(pat.search(r.get("規則", "")) for r in secs["領域"].rows())
            elif prefix_of(did) == "CMP" and "規則と理由" in secs:
                hit = any(pat.search(" ".join(r.values())) for r in secs["規則と理由"].rows())
            if hit:
                if prefix_of(did) == "CMP":
                    add_component(did, f"{id_} を適用（詳細設計）")
                else:
                    imp.add(did, f"{id_} を適用（詳細設計）")
        for cid, ds in by_id.items():
            if prefix_of(cid) == "CMP" and not ds[0].retired and pat.search(ds[0].text):
                add_component(cid, f"{id_} に由来")

    for id_ in sorted(i for i in ids if prefix_of(i) == "FLW"):
        imp.add(id_, "変更対象")
        if id_ in by_id:
            for sid in sorted(set(SCR_RE.findall(by_id[id_][0].text))):
                imp.add(sid, f"{id_} が経由する")
        for did, (rel, _, secs) in details.items():
            if prefix_of(did) == "SCR" and "基本" in secs and \
               any(id_ in r.get("内容", "") for r in secs["基本"].rows() if "シナリオ" in r.get("項目", "")):
                imp.add(did, f"{id_} に関わる")

    for tok in sorted(tokens):
        pats = token_patterns(tok)
        if pats is None:
            for sid in active(by_id, "SCR"):
                imp.add(sid, f"{tok}（全体に効く）")
            continue
        hit = False
        for sid, html in screens.items():
            if any(p.search(html) for p in pats):
                imp.add(sid, f"{tok} を使う")
                hit = True
        for cid, (_, body) in blocks.items():
            if any(p.search(body) for p in pats):
                add_component(cid, f"{tok} を使う")
                hit = True
        if not hit:
            imp.add(tok, "モックで使っている箇所がない（未使用のトークンか、名前の誤り）")

    def key(k):
        m = re.match(r"(SCR|CMP|FLW|UI)-(\d+)", k)
        return ({"SCR": 0, "CMP": 1, "FLW": 2, "UI": 3}[m.group(1)], int(m.group(2))) if m else (4, k)

    out = ["## 影響範囲", ""]
    if changed_files:
        out += ["変更されたファイル：" + "、".join(f"`{f}`" for f in changed_files), ""]
    out += ["| 画面・部品 | 理由 |", "|---|---|"]
    out += [f"| {k} | {'、'.join(v)} |" for k, v in sorted(imp.items.items(), key=lambda kv: key(kv[0]))]
    scr = [k for k in sorted(imp.items, key=key) if k.startswith("SCR-")]
    out += ["", f"撮影対象（shoot.py --screens）：{','.join(scr) if scr else 'なし'}"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
