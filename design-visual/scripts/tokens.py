#!/usr/bin/env python3
"""design-tokens.json を検査・変換する。

使い方:
    python3 tokens.py css      [--root .] [--out docs/D2/mock/assets/theme.css]
    python3 tokens.py css-vars [--root .] [--out <path>]     # Tailwind を使わない実装向け
    python3 tokens.py contrast [--root .]

- css      : Tailwind CSS v4 の @theme と、ダークモードの上書きを含む CSS を出力する
- css-vars : 素の CSS 変数（:root）だけを出力する
- contrast : `$contrast` に列挙した組み合わせのコントラスト比を、モードごとに検査する

終了コード: contrast で基準を満たさない組み合わせがあれば 1。
標準ライブラリのみを使う。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_TOKENS = "docs/D2/design-tokens.json"
DEFAULT_THEME = "docs/D2/mock/assets/theme.css"

# トークンの最上位グループ → Tailwind v4 のテーマ変数の名前空間
THEME_NS = {
    "color": "color",
    "font": "font",
    "text": "text",
    "weight": "font-weight",
    "leading": "leading",
    "tracking": "tracking",
    "radius": "radius",
    "shadow": "shadow",
    "ease": "ease",
    "breakpoint": "breakpoint",
    "container": "container",
    "spacing": "spacing",
}
# Tailwind の名前空間を持たないグループ（素の CSS 変数として出す）
PLAIN_NS = {"duration": "duration", "z": "z"}


def load_config_path(root: str, key: str, default: str) -> str:
    cfg = os.path.join(root, "docs/skills.config.json")
    if os.path.exists(cfg):
        try:
            with open(cfg, encoding="utf-8") as f:
                return json.load(f).get("paths", {}).get(key, default)
        except (OSError, json.JSONDecodeError):
            pass
    return default


def load_tokens(root: str) -> dict:
    path = os.path.join(root, load_config_path(root, "tokens", DEFAULT_TOKENS))
    if not os.path.exists(path):
        sys.exit(f"ERROR: トークンのファイルがありません: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def walk(node: dict, path: list[str]):
    """($value を持つ)トークンを (path, token) で列挙する。"""
    if isinstance(node, dict) and "$value" in node:
        yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            if k.startswith("$"):
                continue
            if isinstance(v, dict):
                yield from walk(v, path + [k])


def fmt_value(group: str, value) -> str:
    if isinstance(value, list):
        parts = []
        for v in value:
            v = str(v)
            parts.append(f'"{v}"' if (" " in v and not v.startswith('"')) else v)
        return ", ".join(parts)
    return str(value)


def var_name(ns: str, rest: list[str]) -> str:
    if not rest:
        return f"--{ns}"
    return f"--{ns}-" + "-".join(rest)


def collect(tokens: dict):
    """(theme_lines, plain_lines, mode_overrides{mode: [lines]}, groups_with_children) を返す。"""
    theme, plain, modes = [], [], {}
    reset = []
    for group, node in tokens.items():
        if group.startswith("$") or not isinstance(node, dict):
            continue
        if group in THEME_NS:
            ns, target = THEME_NS[group], theme
        elif group in PLAIN_NS:
            ns, target = PLAIN_NS[group], plain
        else:
            print(f"WARN: 未知のグループ '{group}' は素の CSS 変数として出力します", file=sys.stderr)
            ns, target = group, plain
        has_child = False
        for path, tok in walk(node, []):
            name = var_name(ns, path)
            if path:
                has_child = True
            target.append(f"  {name}: {fmt_value(group, tok['$value'])};")
            ext = tok.get("$extensions", {})
            if group == "text" and "lineHeight" in ext:
                target.append(f"  {name}--line-height: {ext['lineHeight']};")
            for mode, mval in ext.get("modes", {}).items():
                modes.setdefault(mode, []).append(f"  {name}: {fmt_value(group, mval)};")
        if group in THEME_NS and has_child and group != "spacing":
            reset.append(f"  --{ns}-*: initial;")
    return reset + theme, plain, modes


def cmd_css(args, tailwind: bool = True):
    tokens = load_tokens(args.root)
    theme, plain, modes = collect(tokens)
    out = ["/* 自動生成：design-tokens.json から tokens.py で生成。直接編集しない。 */"]
    if tailwind:
        out += ["@theme static {", *theme, "}"]
        if plain:
            out += [":root {", *plain, "}"]
    else:
        out += [":root {", *[l for l in theme if not l.strip().endswith("initial;")], *plain, "}"]
    for mode, lines in modes.items():
        out += [f':root[data-theme="{mode}"] {{', *lines, "}"]
        if mode == "dark":
            out += ["@media (prefers-color-scheme: dark) {", '  :root:not([data-theme="light"]) {',
                    *["  " + l for l in lines], "  }", "}"]
    text = "\n".join(out) + "\n"
    default_out = load_config_path(args.root, "mock", "docs/D2/mock/").rstrip("/") + "/assets/theme.css"
    dest = args.out or (os.path.join(args.root, default_out) if tailwind else None)
    if dest:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {dest}")
    else:
        sys.stdout.write(text)


# ---- contrast ----
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def hex_to_rgb(h: str):
    m = HEX_RE.match(h.strip())
    if not m:
        return None
    s = m.group(1)
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(rgb) -> float:
    def ch(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def resolve(tokens: dict, dotted: str):
    node = tokens
    for k in dotted.split("."):
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node if isinstance(node, dict) and "$value" in node else None


def cmd_contrast(args):
    tokens = load_tokens(args.root)
    pairs = tokens.get("$contrast", [])
    if not pairs:
        print("WARN: `$contrast` に組み合わせがありません。文字色と背景色の組み合わせを列挙してください。")
        return 0
    modes = {"light"}
    for _, tok in walk(tokens, []):
        modes.update(tok.get("$extensions", {}).get("modes", {}).keys())
    fails = 0
    print("| モード | 文字・前景 | 背景 | 比 | 基準 | 判定 | 用途 |")
    print("|---|---|---|---|---|---|---|")
    for mode in sorted(modes):
        for p in pairs:
            fg, bg = resolve(tokens, p["fg"]), resolve(tokens, p["bg"])
            if fg is None or bg is None:
                print(f"| {mode} | {p['fg']} | {p['bg']} | - | - | ERROR: 未定義のトークン | |")
                fails += 1
                continue

            def val(t):
                if mode != "light":
                    return t.get("$extensions", {}).get("modes", {}).get(mode, t["$value"])
                return t["$value"]
            a, b = hex_to_rgb(str(val(fg))), hex_to_rgb(str(val(bg)))
            if a is None or b is None:
                print(f"| {mode} | {p['fg']} | {p['bg']} | - | - | SKIP: #hex 以外は未対応 | |")
                continue
            r = ratio(a, b)
            need = float(p.get("min", 4.5))
            ok = r >= need
            fails += 0 if ok else 1
            print(f"| {mode} | {p['fg']} | {p['bg']} | {r:.2f} | {need} | {'OK' if ok else 'NG'} | {p.get('note', '')} |")
    print(f"\nNG: {fails}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["css", "css-vars", "contrast"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.cmd == "css":
        cmd_css(args, tailwind=True)
    elif args.cmd == "css-vars":
        cmd_css(args, tailwind=False)
    else:
        sys.exit(cmd_contrast(args))


if __name__ == "__main__":
    main()
