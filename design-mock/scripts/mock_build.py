#!/usr/bin/env python3
"""モックの配置とビルド。

使い方:
    python3 mock_build.py setup [--root .]   # 雛形を docs/D2/mock/ に配置する
    python3 mock_build.py build [--root .]   # トークン → CSS、一覧と注釈の生成、Tailwind のビルド

setup:
    - 毎回上書きする（スキル側の部品）：index.html、assets/mock-kit.js、assets/input.css
    - 無いときだけ置く（プロジェクトで編集する）：components.html、assets/components.js、screens/_template.html
build:
    1. tokens.py css（design-tokens.json → assets/theme.css）
    2. mock_index.py（assets/manifest.js、assets/annotations.js）
    3. npx @tailwindcss/cli（assets/input.css → assets/mock.css）
       プロジェクトに tailwindcss と @tailwindcss/cli（v4）が必要：npm i -D tailwindcss@4 @tailwindcss/cli@4
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.normpath(os.path.join(HERE, "../.."))
sys.path.insert(0, os.path.join(SKILLS, "design-review/scripts"))
from design_docs import load_config, mock_dir  # noqa: E402

SRC = os.path.join(HERE, "../assets/mock")
KIT = ["index.html", "assets/mock-kit.js", "assets/input.css"]
SEED = ["components.html", "assets/components.js", "screens/_template.html"]


def setup(root, cfg):
    dst = mock_dir(root, cfg)
    for rel in KIT + SEED:
        d = os.path.join(dst, rel)
        if rel in SEED and os.path.exists(d):
            print(f"keep   {os.path.relpath(d, root)}")
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(os.path.join(SRC, rel), d)
        print(f"write  {os.path.relpath(d, root)}")
    if not os.path.exists(os.path.join(root, "node_modules/@tailwindcss/cli")):
        print("NOTE: Tailwind が未導入です。npm i -D tailwindcss@4 @tailwindcss/cli@4 を実行してください。")


def run(cmd, cwd):
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode:
        sys.exit(r.returncode)


def build(root, cfg):
    py = sys.executable
    run([py, os.path.join(SKILLS, "design-visual/scripts/tokens.py"), "css", "--root", root], root)
    run([py, os.path.join(HERE, "mock_index.py"), "--root", root], root)
    m = os.path.relpath(mock_dir(root, cfg), root)
    run(["npx", "--no-install", "@tailwindcss/cli", "-i", f"{m}/assets/input.css", "-o", f"{m}/assets/mock.css"], root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["setup", "build"])
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    cfg, notes = load_config(root)
    for n in notes:
        print("NOTE:", n)
    setup(root, cfg) if args.cmd == "setup" else build(root, cfg)


if __name__ == "__main__":
    main()
