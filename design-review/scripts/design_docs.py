"""design の文書と設定を読む共通処理（design_check.py、mock_index.py、ui_diff.py が使う）。標準ライブラリのみ。"""
from __future__ import annotations

import copy
import glob
import json
import os
import re
from dataclasses import dataclass, field

CONFIG_PATH = "docs/skills.config.json"

DEFAULT_CONFIG = {
    "contract": 1,
    "packages": ["design"],
    "providers": {"ui_guidelines": "design"},
    "paths": {
        "ui_guidelines": "docs/D2/UI_GUIDELINES.md",
        "ux_structure": "docs/D2/UX_STRUCTURE.md",
        "tokens": "docs/D2/design-tokens.json",
        "mock": "docs/D2/mock/",
        "design_work": "docs/work/design/",
    },
    "ids": {
        "PSN": {"owner": ["docs/D2/UI_GUIDELINES.md"], "upstream": ["OV", "C"], "package": "design"},
        "UI": {"owner": ["docs/D2/UI_GUIDELINES.md", "docs/D2/UX_STRUCTURE.md"],
               "upstream": ["FR", "NFR", "OV", "C", "PSN"], "package": "design"},
        "CMP": {"owner": ["docs/D2/UI_GUIDELINES.md"], "upstream": ["UI", "FR", "SCR"], "package": "design"},
        "SCR": {"owner": ["docs/D2/UX_STRUCTURE.md"], "upstream": ["FR", "OV", "C", "FLW"], "package": "design"},
        "FLW": {"owner": ["docs/D2/UX_STRUCTURE.md"], "upstream": ["FR", "OV", "C", "PSN"], "package": "design"},
    },
    "design": {
        "viewports": {"ios": [390, 844], "android": [412, 915], "desktop": [1440, 900]},
        "conformance": {"impl_base_url": None, "state_param": "state", "routes": {}},
    },
}
SUPPORTED_CONTRACT = {1}

# 既定値は design-foundation の雛形から読む（雛形とスクリプトの既定値をずらさないため）
_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../design-foundation/assets/skills.config.json")
if os.path.exists(_TEMPLATE):
    with open(_TEMPLATE, encoding="utf-8") as _f:
        DEFAULT_CONFIG = json.load(_f)

# 接頭辞-（領域-）番号。base の FR-T-7 も拾う。
ANY_ID_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Z]{1,4}(?:-[A-Z]{1,6})?-\d+)(?![0-9A-Za-z-])")
SPECIAL_UPSTREAM_RE = re.compile(r"(外部:|追加[：:])")
RETIRED = "（廃止）"


def load_config(root: str) -> tuple[dict, list[str]]:
    """設定を既定値とマージして返す。警告の一覧も返す。"""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    warns = []
    path = os.path.join(root, CONFIG_PATH)
    if not os.path.exists(path):
        warns.append(f"{CONFIG_PATH} がないため既定値で検査します（design 単独）")
        return cfg, warns
    with open(path, encoding="utf-8") as f:
        user = json.load(f)
    if user.get("contract") not in SUPPORTED_CONTRACT:
        warns.append(f"contract={user.get('contract')} は対応範囲外です（対応：{sorted(SUPPORTED_CONTRACT)}）")
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            for kk, vv in v.items():
                if isinstance(vv, dict) and isinstance(cfg[k].get(kk), dict):
                    cfg[k][kk].update(vv)
                else:
                    cfg[k][kk] = vv
        else:
            cfg[k] = v
    return cfg, warns


def design_prefixes(cfg: dict) -> dict:
    """design が検査対象にする接頭辞 → 設定。provider が base なら UI を除く。"""
    ids = {k: v for k, v in cfg["ids"].items() if v.get("package", "design") == "design"}
    if cfg["providers"].get("ui_guidelines") != "design":
        ids.pop("UI", None)
    return ids


def prefix_of(id_: str) -> str:
    return id_.split("-")[0]


def doc_files(root: str) -> list[str]:
    """正の文書（spec/、docs/ のうち docs/work/ 以外）の Markdown。"""
    out = []
    for pat in ("spec/**/*.md", "docs/**/*.md"):
        for p in glob.glob(os.path.join(root, pat), recursive=True):
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if rel.startswith("docs/work/"):
                continue
            out.append(rel)
    return sorted(set(out))


def detail_dirs(cfg: dict) -> list[str]:
    """詳細設計のディレクトリ（ID を定義しない。参照だけ）。"""
    p = cfg["paths"]
    return [p.get("screens", "docs/D2/screens/").rstrip("/") + "/",
            p.get("components", "docs/D2/components/").rstrip("/") + "/"]


def definition_files(root: str, cfg: dict) -> list[str]:
    """ID を定義してよい文書：正の文書から詳細設計を除いたもの。"""
    dd = detail_dirs(cfg)
    return [f for f in doc_files(root) if not any(f.startswith(d) for d in dd)]


@dataclass
class Section:
    title: str
    line: int
    body: list[str] = field(default_factory=list)
    tables: list[list[dict]] = field(default_factory=list)  # 表ごとに、見出し → セルの辞書の行

    def text(self) -> str:
        return "\n".join(l for l in self.body if not l.strip().startswith("<!--")).strip()

    def rows(self) -> list[dict]:
        return [r for t in self.tables for r in t]


def read_sections(path: str) -> tuple[str, dict[str, Section]]:
    """Markdown を「## 見出し」ごとに分け、各節の表を読む。(文書の題名, 見出し → 節) を返す。"""
    lines = open(path, encoding="utf-8").read().splitlines()
    title, secs, cur = "", {}, None
    in_code = in_comment = False
    header = None
    for i, line in enumerate(lines):
        st = line.strip()
        if st.startswith("```"):
            in_code = not in_code
        if not in_code:
            if st.startswith("<!--") and "-->" not in st:
                in_comment = True
            if in_comment:
                if "-->" in st:
                    in_comment = False
                continue
            if line.startswith("# ") and not title:
                title = line[2:].strip()
                continue
            if line.startswith("## "):
                name = re.sub(r"[（(].*?[)）]\s*$", "", line[3:].strip()).strip()
                cur = secs.setdefault(name, Section(name, i + 1))
                header = None
                continue
        if cur is None:
            continue
        cur.body.append(line)
        if in_code or not st.startswith("|"):
            header = None
            continue
        cells = split_row(line)
        if SEP_RE.match(line):
            continue
        if i + 1 < len(lines) and SEP_RE.match(lines[i + 1]):
            header = cells
            cur.tables.append([])
            continue
        if header is not None:
            cur.tables[-1].append(dict(zip(header, cells)))
    return title, secs


def ref_files(root: str, cfg: dict) -> list[str]:
    """参照を探すファイル：正の文書、Issue、モックの HTML/JS。"""
    out = doc_files(root)
    out += [os.path.relpath(p, root) for p in glob.glob(os.path.join(root, "issues/**/*.md"), recursive=True)]
    mock = cfg["paths"]["mock"].rstrip("/")
    for ext in ("html", "js"):
        for p in glob.glob(os.path.join(root, mock, f"**/*.{ext}"), recursive=True):
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if os.path.basename(rel).startswith("_") or rel.endswith(("/manifest.js", "/annotations.js", "/mock-kit.js")):
                continue
            out.append(rel)
    return sorted(set(out))


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def clean_id(cell: str) -> str:
    return re.sub(r"[`*_\s]", "", cell)


@dataclass
class Definition:
    id: str
    file: str
    line: int
    text: str                     # 定義の行（見出しの場合は直後の数行も含める）
    cells: dict = field(default_factory=dict)  # 表の場合：見出し → セル
    kind: str = "table"
    retired: bool = False


HEAD_RE = re.compile(r"^#{1,6}\s+([A-Z]{1,4}-\d+)\s*[：:\s]")
BULLET_RE = re.compile(r"^\s*[-*]\s+\**([A-Z]{1,4}-\d+)\**\s*[：:]")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}")


def find_definitions(root: str, files: list[str], prefixes: set[str]) -> list[Definition]:
    defs = []
    for rel in files:
        try:
            lines = open(os.path.join(root, rel), encoding="utf-8").read().splitlines()
        except OSError:
            continue
        header = None
        in_code = False
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or line.strip().startswith("<!--"):
                continue
            if line.lstrip().startswith("|"):
                cells = split_row(line)
                if i + 1 < len(lines) and SEP_RE.match(lines[i + 1]) and not SEP_RE.match(line):
                    header = cells
                    continue
                if SEP_RE.match(line):
                    continue
                first = clean_id(cells[0]) if cells else ""
                if ANY_ID_RE.fullmatch(first) and prefix_of(first) in prefixes:
                    mapped = {}
                    if header:
                        for h, c in zip(header, cells):
                            mapped[h] = c
                    defs.append(Definition(first, rel, i + 1, line, mapped, "table", RETIRED in line))
                continue
            header = None
            m = HEAD_RE.match(line) or BULLET_RE.match(line)
            if m and prefix_of(m.group(1)) in prefixes:
                kind = "heading" if line.startswith("#") else "bullet"
                text = line
                if kind == "heading":
                    text = "\n".join([line] + lines[i + 1:i + 3])
                title = re.sub(r"^#+\s+|^\s*[-*]\s+", "", line)
                defs.append(Definition(m.group(1), rel, i + 1, text, {"見出し": title}, kind, RETIRED in line))
    return defs


def find_references(root: str, files: list[str]) -> dict[str, list[tuple[str, int]]]:
    refs: dict[str, list[tuple[str, int]]] = {}
    for rel in files:
        try:
            lines = open(os.path.join(root, rel), encoding="utf-8").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            for m in ANY_ID_RE.finditer(line):
                refs.setdefault(m.group(1), []).append((rel, i + 1))
    return refs


def mock_dir(root: str, cfg: dict) -> str:
    return os.path.join(root, cfg["paths"]["mock"].rstrip("/"))


def read_manifest(root: str, cfg: dict) -> dict | None:
    p = os.path.join(mock_dir(root, cfg), "assets/manifest.js")
    if not os.path.exists(p):
        return None
    text = open(p, encoding="utf-8").read()
    body = text.split("=", 1)[1].strip().rstrip(";")
    return json.loads(body)


def serve(directory: str):
    """directory を 127.0.0.1 の空きポートで配信する。(server, base_url) を返す。終了時は server.shutdown()。"""
    import functools
    import http.server
    import threading

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Quiet, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"
