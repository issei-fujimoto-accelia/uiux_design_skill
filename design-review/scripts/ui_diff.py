#!/usr/bin/env python3
"""モックと実装を data-ui で照合し、差分を報告する（読み取り専用）。

使い方:
    python3 ui_diff.py [--root .] [--impl http://localhost:3000] [--vp ios,desktop] [--screens SCR-1] [--out <path>]

設定（docs/skills.config.json の design.conformance）:
    impl_base_url : 実装の URL（--impl で上書き）
    routes        : {"SCR-1": "/", "SCR-2": "/orders/demo"}
    state_param   : 実装で状態を切り替えるクエリ名（null なら default だけ照合）

検出すること:
    不足     : モックにあり実装にない data-ui
    未設計   : 実装にありモックにない data-ui（SCR / CMP の形式のもの）
    個数     : 同じ data-ui の個数の違い
    スタイル : 対応する要素（各 ID の最初の要素）の computed style の違い
例外：docs/work/design/waivers.md の表の先頭列に書いた ID は「例外」として分けて報告する。

前提：Python の playwright。終了コード：不足か未設計があれば 1。
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design_docs import load_config, mock_dir, read_manifest, serve, split_row  # noqa: E402

PROPS = ["color", "background-color", "font-family", "font-size", "font-weight", "line-height",
         "padding-top", "padding-right", "padding-bottom", "padding-left", "border-top-left-radius",
         "border-top-width", "border-top-color", "gap", "box-shadow"]

COLLECT_JS = """
(props) => {
  const out = {};
  for (const el of document.querySelectorAll('[data-ui]')) {
    if (el.closest('[hidden]') || (el.checkVisibility && !el.checkVisibility())) continue;
    const id = el.getAttribute('data-ui');
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const entry = out[id] || (out[id] = {count: 0, first: null});
    entry.count++;
    if (!entry.first) entry.first = {tag: el.tagName.toLowerCase(), w: Math.round(r.width), h: Math.round(r.height),
      style: Object.fromEntries(props.map(p => [p, cs.getPropertyValue(p)]))};
  }
  return out;
}
"""
UI_ID_RE = re.compile(r"^(SCR|CMP)-\d+(/[\w-]+)?$")


def norm(prop, v):
    v = (v or "").strip()
    if prop == "font-family":
        return v.split(",")[0].strip().strip("\"'").lower()
    return v


def px_close(a, b, tol=1.0):
    pa, pb = re.fullmatch(r"(-?[\d.]+)px", a), re.fullmatch(r"(-?[\d.]+)px", b)
    if pa and pb:
        return abs(float(pa.group(1)) - float(pb.group(1))) <= tol
    return a == b


def load_waivers(root, cfg):
    p = os.path.join(root, cfg["paths"]["design_work"], "waivers.md")
    ids = set()
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.lstrip().startswith("|"):
                first = split_row(line)[0].strip("` ")
                if UI_ID_RE.match(first):
                    ids.add(first)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--impl")
    ap.add_argument("--vp")
    ap.add_argument("--screens")
    ap.add_argument("--out")
    args = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("ERROR: playwright がありません。pip install playwright && python -m playwright install chromium")

    cfg, _ = load_config(args.root)
    conf = cfg["design"]["conformance"]
    impl = (args.impl or conf.get("impl_base_url") or "").rstrip("/")
    if not impl:
        sys.exit("ERROR: 実装の URL がありません（--impl か design.conformance.impl_base_url）")
    routes = conf.get("routes") or {}
    if not routes:
        sys.exit("ERROR: design.conformance.routes に SCR-N → 実装のパスを書いてください")
    manifest = read_manifest(args.root, cfg)
    if manifest is None:
        sys.exit("ERROR: manifest.js がありません。先に mock_index.py を実行してください。")
    mscreens = {s["id"]: s for s in manifest["screens"]}
    vps = cfg["design"]["viewports"]
    names = args.vp.split(",") if args.vp else list(vps)
    only = set(args.screens.split(",")) if args.screens else None
    sp = conf.get("state_param")
    waivers = load_waivers(args.root, cfg)

    rows = []  # (kind, scr, state, vp, id, detail)
    server, base = serve(mock_dir(args.root, cfg))
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for vp in names:
                w, h = vps[vp]
                ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
                page = ctx.new_page()
                for scr, route in routes.items():
                    if only and scr not in only:
                        continue
                    if scr not in mscreens:
                        rows.append(("不足", scr, "-", vp, scr, "モックに画面がない"))
                        continue
                    states = mscreens[scr]["states"] if sp else ["default"]
                    for st in states:
                        mq = "" if st == "default" else f"?state={st}"
                        page.goto(base + mscreens[scr]["file"] + mq, wait_until="networkidle")
                        m = page.evaluate(COLLECT_JS, PROPS)
                        sep = "&" if "?" in route else "?"
                        iq = "" if st == "default" else f"{sep}{sp}={st}"
                        try:
                            page.goto(impl + route + iq, wait_until="networkidle")
                            i = page.evaluate(COLLECT_JS, PROPS)
                        except Exception as e:  # noqa: BLE001
                            rows.append(("取得失敗", scr, st, vp, scr, str(e).splitlines()[0]))
                            continue
                        for id_ in sorted(set(m) - set(i)):
                            rows.append(("不足", scr, st, vp, id_, "モックにあり実装にない"))
                        for id_ in sorted(set(i) - set(m)):
                            if UI_ID_RE.match(id_):
                                rows.append(("未設計", scr, st, vp, id_, "実装にありモックにない"))
                        for id_ in sorted(set(m) & set(i)):
                            a, b = m[id_], i[id_]
                            if a["count"] != b["count"]:
                                rows.append(("個数", scr, st, vp, id_, f"モック {a['count']} / 実装 {b['count']}"))
                            diffs = []
                            for p in PROPS:
                                va, vb = norm(p, a["first"]["style"][p]), norm(p, b["first"]["style"][p])
                                if not px_close(va, vb):
                                    diffs.append(f"{p}: {va} → {vb}")
                            if diffs:
                                rows.append(("スタイル", scr, st, vp, id_, "<br>".join(diffs)))
                ctx.close()
            browser.close()
    finally:
        server.shutdown()

    def waived(r):
        return r[4] in waivers or r[4].split("/")[0] in waivers
    main_rows = [r for r in rows if not waived(r)]
    w_rows = [r for r in rows if waived(r)]
    kinds = ["不足", "未設計", "個数", "スタイル", "取得失敗"]
    summary = " / ".join(f"{k}: {sum(1 for r in main_rows if r[0] == k)}" for k in kinds)
    lines = [f"# モックと実装の照合 {dt.date.today().isoformat()}", "", f"実装：{impl}", "", summary,
             f"例外（waivers.md）：{len(w_rows)}", "",
             "| 種類 | 画面 | 状態 | ビューポート | data-ui | 内容 |", "|---|---|---|---|---|---|"]
    lines += [f"| {' | '.join(r)} |" for r in sorted(main_rows, key=lambda r: kinds.index(r[0]))]
    if w_rows:
        lines += ["", "## 例外", "", "| 種類 | 画面 | 状態 | ビューポート | data-ui | 内容 |", "|---|---|---|---|---|---|"]
        lines += [f"| {' | '.join(r)} |" for r in w_rows]
    text = "\n".join(lines) + "\n"
    out = args.out or os.path.join(args.root, cfg["paths"]["design_work"], "conformance", f"{dt.date.today().isoformat()}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(text)
    print(f"wrote {out}\n{summary}")
    sys.exit(1 if any(r[0] in ("不足", "未設計") for r in main_rows) else 0)


if __name__ == "__main__":
    main()
