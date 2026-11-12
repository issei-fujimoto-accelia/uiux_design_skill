# GUIDE：uiux_design_skill の使い方

design の各スキルが最初に読む文書。スキル群の全体像、プロジェクト側の配置、守る規則、工程、コマンドをまとめる。
画面のデザインは、理由の付いた文書とモックで決めてから実装する。

| 文書 | 内容 |
|---|---|
| [CONTRACT.md](CONTRACT.md) | base_skill など他のスキル群との取り決め（設定ファイル、配置、ID、`data-ui`、実装側の義務） |
| [config.md](config.md) | 設定ファイル（`docs/skills.config.json`）の確認と初期化の手順 |
| [id-rules.md](id-rules.md)、[writing.md](writing.md) | ID の規則、書き方 |
| [principles.md](principles.md)、[platforms.md](platforms.md) | 判断の根拠となる原則、プラットフォームの慣習 |

## 配置

| 場所 | 位置づけ | 内容 | ID |
|---|---|---|---|
| `docs/D2/UI_GUIDELINES.md` | 正 | 品質方針、ペルソナ、コンセプト、全体の規則、共通部品の一覧、トークンの方針 | `PSN` / `UI` / `CMP` |
| `docs/D2/UX_STRUCTURE.md` | 正 | 操作シナリオ、画面一覧、遷移、画面をまたぐ配置の規則 | `FLW` / `SCR` / `UI` |
| `docs/D2/screens/SCR-N.md` | 正 | 画面の詳細設計（領域、状態、操作、文言） | 参照のみ |
| `docs/D2/components/CMP-N.md` | 正 | 部品の詳細設計（構成、受け取る値、状態と変種、大きさ、アクセシビリティ） | 参照のみ |
| `docs/D2/design-tokens.json` | 正 | 色、文字、余白、角丸、影、動きの値 | ― |
| `docs/D2/mock/` | 正（承認後） | HTML モック | `data-ui` で参照 |
| `docs/work/design/` | 記録 | 下表 | 参照のみ |

`docs/work/design/` のサブディレクトリとファイル：

| 場所 | 内容 |
|---|---|
| `planning/<スキル名>-state.md` | インタビューの作業状態 |
| `approvals.md` | 人の確認の記録（日付、工程、対象、結果、承認者） |
| `revisions/R-NN.md`、`revisions/R-NN/` | モックの修正ラウンドの記録（指摘、種類、対応、影響範囲）と、前後のスクリーンショット |
| `proposals/<工程>.md` | UI 文書を別のスキル群が作る場合の提案 |
| `shots/YYYY-MM-DD/` | スクリーンショットと機械チェックの結果 |
| `rounds/NN/review.md` | セルフチェックの採点 |
| `conformance/YYYY-MM-DD.md` | モックと実装の照合結果 |
| `waivers.md` | モックと実装の意図的な差（ID、理由、承認者） |

## デザインの規則

- 配置、色、動き、文言などの判断には、ID と理由を書く。理由にはペルソナ（`PSN`）、利用状況、原則名のいずれかを使う。
- 画面と部品の詳細設計は、雛形の節と列を変えない。当てはまらない節は「該当なし」と書く。
- 値（px、色コード）を文書に書かない。トークン名を書き、値は `design-tokens.json` にだけ置く。
- デザインを変えるときは、文書 → トークン → モック → 実装の順に直す。モックや実装だけを直さない。
- モックにロジック（データ取得、検証、業務ルール）を書かない。トークン外の値（`bg-[#123456]`、`p-[13px]`、`style` 属性の色）を使わない。
- 生成物（`mock/assets/theme.css`、`manifest.js`、`annotations.js`、`mock.css`）を直接編集しない。

## 画面を実装するときの規則

`docs/D2/mock/` があるプロジェクトでは、画面の実装は次を守る。

- モックと同じ要素に `data-ui`（`SCR-N`、`SCR-N/<領域>`、`CMP-N`）を付ける。
- `screens/SCR-N.md` の各状態を、固定データで表示できるようにする（例：`?state=empty`）。
- 部品は `components/CMP-N.md` の受け取る値、状態と変種、アクセシビリティを満たす。
- 色、文字、余白、角丸、影、動きは、`design-tokens.json` から生成した CSS だけを使う。
- モックと意図的に違えるときは、`docs/work/design/waivers.md` に ID、理由、承認者を書く。

## 工程と確認のタイミング

| タイミング | 使うスキル | 人の確認 |
|---|---|---|
| 要件がそろったとき | design-foundation（ペルソナ、コンセプト） | ① |
| 上の承認後 | design-structure（導線、画面の詳細設計） | ② |
| 上の承認後 | design-visual（トークン、部品の詳細設計） | ― |
| 上の完了後 | design-mock（モックの初版） | ― |
| 初版の後、完成まで繰り返す | design-revise（指摘を種類ごとに直す1ラウンド） | ③（完成時） |
| モックの承認後 | design-review self-check | ― |
| 画面を実装したとき | design-review conformance | ― |
| 文書やモックを変えたとき | design-review check | ― |

照合や検査で見つかった差は、記録に残すだけで終えない。直す側（文書、モック、実装）を決め、プロジェクトの手順で作業にする。

## コマンド

| 用途 | コマンド |
|---|---|
| ID、詳細設計、モックの検査 | `python3 <skills>/design-review/scripts/design_check.py all --root .` |
| コントラストの検査 | `python3 <skills>/design-visual/scripts/tokens.py contrast --root .` |
| モックのビルド | `python3 <skills>/design-mock/scripts/mock_build.py build --root .` |
| モックの撮影 | `python3 <skills>/design-mock/scripts/shoot.py --root .` |
| モックと実装の照合 | `python3 <skills>/design-review/scripts/ui_diff.py --root .` |
| モックを開く | `python3 -m http.server -d docs/D2/mock 8000` |

`<skills>` はスキルのインストール先（例：`.claude/skills`）。

## プロジェクトの AGENTS.md

AGENTS.md と CLAUDE.md はプロジェクトが管理する。スキルは書き換えない。
「画面を実装するときの規則」のように、デザインのスキルが動いていない作業でも守らせたい規則は、プロジェクトの AGENTS.md に書かれている必要がある。
design-foundation の初期化のとき、AGENTS.md に design の節がなければ、この文書の「画面を実装するときの規則」と変更の順序を示して、ユーザーに追記を提案する（雛形は uiux_design_skill リポジトリ直下の `AGENTS.snippet.md`）。
