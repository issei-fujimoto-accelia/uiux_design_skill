#!/usr/bin/env python3
"""モックの全画面・全状態・各ビューポートのスクリーンショットを撮り、簡単な機械チェックを行う。

使い方:
    python3 shoot.py [--root .] [--vp ios,desktop] [--theme light|dark] [--screens SCR-1,SCR-3] [--out <dir>]
    python3 shoot.py --target impl [...]   # 実装を撮る（design.conformance の impl_base_url と routes を使う）

- モックのディレクトリを自前で配信する（別にサーバーを立てなくてよい）
- prefers-reduced-motion: reduce で撮る（動きによる揺れを避けるため）
- 出力：<out>/<SCR>__<state>__<vp>.png と <out>/index.md（コンソールのエラー、小さすぎるタップ領域）
- 既定の出力先：docs/work/design/shots/YYYY-MM-DD/

前提：Python の playwright（pip install playwright && python -m playwright install chromium）
終了コード：ページのエラーがあれば 1。
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../design-review/scripts"))
from design_docs import load_config, mock_dir, read_manifest, serve  # noqa: E402

TARGET_JS = """
() => {
  const sel = 'a[href],button,input,select,textarea,[role=button],[role=link],[tabindex]:not([tabindex="-1"])';
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    if (el.closest('[hidden]') || (el.checkVisibility && !el.checkVisibility())) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.width < 24 || r.height < 24) {
      out.push({tag: el.tagName.toLowerCase(), ui: el.closest('[data-ui]')?.getAttribute('data-ui') || '',
                text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 20),
                w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  return out;
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--vp", help="ビューポート名をカンマ区切りで（既定：設定のすべて）")
    ap.add_argument("--theme", choices=["light", "dark"])
    ap.add_argument("--screens", help="SCR-N をカンマ区切りで（既定：すべて）")
    ap.add_argument("--out")
    ap.add_argument("--target", choices=["mock", "impl"], default="mock")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("ERROR: playwright がありません。pip install playwright && python -m playwright install chromium")

    cfg, _ = load_config(args.root)
    manifest = read_manifest(args.root, cfg)
    if manifest is None:
        sys.exit("ERROR: manifest.js がありません。先に mock_index.py を実行してください。")
    vps = cfg["design"]["viewports"]
    names = args.vp.split(",") if args.vp else list(vps)
    only = set(args.screens.split(",")) if args.screens else None
    out = args.out or os.path.join(args.root, cfg["paths"]["design_work"], "shots", dt.date.today().isoformat())
    os.makedirs(out, exist_ok=True)

    states_of = {s["id"]: s["states"] for s in manifest["screens"]}
    conf = cfg["design"]["conformance"]
    if args.target == "impl":
        if not conf.get("impl_base_url") or not conf.get("routes"):
            sys.exit("ERROR: design.conformance の impl_base_url と routes を設定してください")
        sp = conf.get("state_param")
        targets = [(scr, route.lstrip("/"), states_of.get(scr, ["default"]) if sp else ["default"])
                   for scr, route in conf["routes"].items() if not only or scr in only]
        server, base = None, conf["impl_base_url"].rstrip("/") + "/"
    else:
        sp = "state"
        targets = [(s["id"], s["file"], s["states"]) for s in manifest["screens"] if not only or s["id"] in only]
        if not only:
            targets.append(("CMP", manifest.get("components", "components.html"), ["default"]))
        server, base = serve(mock_dir(args.root, cfg))
    errors, small, shots = [], [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for vp in names:
                w, h = vps[vp]
                ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce",
                                          color_scheme=args.theme or "light")
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append((page.url, f"error: {e}")))
                page.on("console", lambda m: m.type in ("error", "warning") and errors.append((page.url, f"{m.type}: {m.text}")))
                for id_, file, states in targets:
                    for st in states:
                        q = [] if st == "default" else [f"{sp}={st}"]
                        if args.theme and args.target == "mock":
                            q.append(f"theme={args.theme}")
                        url = base + file + (("&" if "?" in file else "?") + "&".join(q) if q else "")
                        page.goto(url, wait_until="networkidle")
                        name = f"{id_}__{st}__{vp}.png"
                        page.screenshot(path=os.path.join(out, name), full_page=True)
                        shots.append((id_, st, vp, name))
                        for s in page.evaluate(TARGET_JS):
                            small.append((id_, st, vp, s))
                ctx.close()
            browser.close()
    finally:
        if server:
            server.shutdown()

    lines = [f"# スクリーンショット {dt.date.today().isoformat()}", "",
             f"撮影数：{len(shots)} / ページのエラー：{len(errors)} / 24px 未満のタップ領域：{len(small)}", "",
             "| 画面 | 状態 | ビューポート | ファイル |", "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in shots]
    if errors:
        lines += ["", "## ページのエラーと警告", "", "| URL | 内容 |", "|---|---|"]
        lines += [f"| {u.replace(base, '')} | {m} |" for u, m in errors]
    if small:
        lines += ["", "## 24px 未満のタップ領域（principles#target-size）", "",
                  "| 画面 | 状態 | ビューポート | 要素 | data-ui | 文字 | 大きさ |", "|---|---|---|---|---|---|---|"]
        lines += [f"| {a} | {b} | {c} | {s['tag']} | {s['ui']} | {s['text']} | {s['w']}×{s['h']} |" for a, b, c, s in small]
    with open(os.path.join(out, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out}/index.md  shots={len(shots)} errors={len(errors)} small_targets={len(small)}")
    sys.exit(1 if any("warning:" not in m for _, m in errors) else 0)


if __name__ == "__main__":
    main()
