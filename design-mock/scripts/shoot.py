#!/usr/bin/env python3
"""モックの全画面・全状態・各ビューポートのスクリーンショットを撮り、簡単な機械チェックを行う。

使い方:
    python3 shoot.py [--root .] [--vp ios,desktop] [--theme light|dark] [--screens SCR-1,SCR-3] [--out <dir>]
    python3 shoot.py --target impl [...]   # 実装を撮る（design.conformance の impl_base_url と routes を使う）
    python3 shoot.py --out <後> --compare <前>   # 前の撮影と比べ、<後>/compare.html を作る

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


def compare(before: str, after: str):
    """同じ名前の画像をバイト単位で比べ、変化のあったものを先頭にした compare.html を作る。"""
    import hashlib
    import html as h

    def digest(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    b = {n for n in os.listdir(before) if n.endswith(".png")} if os.path.isdir(before) else set()
    a = {n for n in os.listdir(after) if n.endswith(".png")}
    rows = []
    for n in sorted(a | b):
        if n not in b:
            rows.append((n, "追加"))
        elif n not in a:
            rows.append((n, "削除"))
        else:
            rows.append((n, "変化なし" if digest(os.path.join(before, n)) == digest(os.path.join(after, n)) else "変化あり"))
    order = {"変化あり": 0, "追加": 1, "削除": 2, "変化なし": 3}
    rows.sort(key=lambda r: (order[r[1]], r[0]))
    rel_b = os.path.relpath(before, after).replace(os.sep, "/")
    cards = []
    for n, r in rows:
        left = f'<img src="{h.escape(rel_b)}/{h.escape(n)}" loading="lazy">' if r != "追加" else "<p>（なし）</p>"
        right = f'<img src="{h.escape(n)}" loading="lazy">' if r != "削除" else "<p>（なし）</p>"
        cards.append(f'<section data-result="{r}"><h2>{h.escape(n)} <span>{r}</span></h2>'
                     f'<div class="pair"><figure><figcaption>前</figcaption>{left}</figure>'
                     f'<figure><figcaption>後</figcaption>{right}</figure></div></section>')
    page = f"""<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>前後の比較</title><style>
body{{font:14px/1.5 system-ui,sans-serif;margin:0;padding:16px;background:#f3f4f6;color:#16181d}}
label{{margin-right:12px}} section{{background:#fff;border-radius:8px;padding:12px;margin:12px 0}}
h2{{font-size:14px;margin:0 0 8px}} h2 span{{font-weight:400;padding:1px 6px;border-radius:4px;background:#eee}}
section[data-result="変化あり"] h2 span{{background:#ffe08a}} section[data-result="追加"] h2 span{{background:#b7f0c0}}
section[data-result="削除"] h2 span{{background:#ffc2c2}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} figure{{margin:0}} img{{max-width:100%;border:1px solid #ddd}}
body.hide-same section[data-result="変化なし"]{{display:none}}
</style><body class="hide-same"><h1>前後の比較</h1>
<p>変化あり {sum(1 for _, r in rows if r == "変化あり")} / 追加 {sum(1 for _, r in rows if r == "追加")} /
削除 {sum(1 for _, r in rows if r == "削除")} / 変化なし {sum(1 for _, r in rows if r == "変化なし")}</p>
<label><input type="checkbox" onchange="document.body.classList.toggle('hide-same',!this.checked)"> 変化のない画像も表示</label>
{''.join(cards)}</body></html>"""
    with open(os.path.join(after, "compare.html"), "w", encoding="utf-8") as f:
        f.write(page)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--vp", help="ビューポート名をカンマ区切りで（既定：設定のすべて）")
    ap.add_argument("--theme", choices=["light", "dark"])
    ap.add_argument("--screens", help="SCR-N をカンマ区切りで（既定：すべて）")
    ap.add_argument("--out")
    ap.add_argument("--target", choices=["mock", "impl"], default="mock")
    ap.add_argument("--compare", help="前の撮影のディレクトリ。同じ名前の画像と比べ、compare.html を作る")
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
    if args.compare:
        changes = compare(args.compare, out)
        lines += ["", "## 前の撮影との比較", "", f"前：`{args.compare}` / 比較のページ：`compare.html`", "",
                  "| 画像 | 結果 |", "|---|---|"]
        lines += [f"| {n} | {r} |" for n, r in changes if r != "変化なし"]
        lines.append(f"\n変化なし：{sum(1 for _, r in changes if r == '変化なし')} 枚")
    with open(os.path.join(out, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out}/index.md  shots={len(shots)} errors={len(errors)} small_targets={len(small)}")
    sys.exit(1 if any("warning:" not in m for _, m in errors) else 0)


if __name__ == "__main__":
    main()
