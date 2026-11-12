# Contract v1

uiux_design_skill（以下 design）と base_skill（以下 base）を、互いに依存させずに組み合わせるための取り決め。
両リポジトリは同じ内容の本書を持ち（design では `design-foundation/references/CONTRACT.md`）、`contract` の番号で一致を確認する。
スキルは相手のスキル名やパスを参照しない。参照するのは、プロジェクトの設定ファイルと本書の取り決めだけである。

## 1. 設定ファイル

プロジェクトの `docs/skills.config.json` に置く。雛形は `design-foundation/assets/skills.config.json`。

| キー | 型 | 内容 |
|---|---|---|
| `contract` | 整数 | 本書の版。v1 では `1` |
| `packages` | 配列 | 導入済みのスキル群。`"base"`、`"design"` |
| `providers.ui_guidelines` | 文字列 | `UI_GUIDELINES.md` を作るスキル群。`"base"` または `"design"` |
| `paths` | オブジェクト | 2章の配置。v1 では既定値から変えない |
| `ids` | オブジェクト | 接頭辞ごとの所有文書と上流（3章）。検査スクリプトが読む |
| `design` | オブジェクト | design だけが読む設定（ビューポート、実装との照合先） |

- 各スキル群は、初期化のときに自分の担当分だけを追加・更新する。他のスキル群のキーを消さない。
- 設定ファイルがない場合、各スキル群は自分の既定値で単独で動く。
- 読み込んだ `contract` が対応範囲外なら、作業を始める前にユーザーに警告する。

## 2. 配置

パスは固定する。単独で動く場合も、組み合わせた場合も同じパスを使う。

| キー | パス | 位置づけ | 書くスキル群 |
|---|---|---|---|
| `ui_guidelines` | `docs/D2/UI_GUIDELINES.md` | 正 | `providers.ui_guidelines` |
| `ux_structure` | `docs/D2/UX_STRUCTURE.md` | 正 | design |
| `screens` | `docs/D2/screens/`（`SCR-N.md`） | 正 | design |
| `components` | `docs/D2/components/`（`CMP-N.md`） | 正 | design |
| `tokens` | `docs/D2/design-tokens.json` | 正 | design |
| `mock` | `docs/D2/mock/` | 正 | design |
| `design_work` | `docs/work/design/` | 記録（正ではない） | design、base |

## 3. ID

### design が所有する ID

| 接頭辞 | 意味 | 所有文書 | 同じ行に書く由来 |
|---|---|---|---|
| `PSN-N` | ペルソナ | `UI_GUIDELINES.md` | `OV`、`C`、`外部:`、`追加` |
| `UI-N` | UI の規則（判断と理由） | `UI_GUIDELINES.md`、`UX_STRUCTURE.md` | `FR`、`NFR`、`OV`、`C`、`PSN`、`外部:`、`追加` |
| `CMP-N` | 共通部品 | `UI_GUIDELINES.md` | `UI`、`FR`、`SCR` |
| `SCR-N` | 画面 | `UX_STRUCTURE.md` | `FR`、`OV`、`C`、`FLW`、`外部:`、`追加` |
| `FLW-N` | 操作シナリオ | `UX_STRUCTURE.md` | `FR`、`OV`、`C`、`PSN`、`外部:`、`追加` |

- `SCR-N` と `CMP-N` の詳細設計は、ID ごとのファイル（`screens/SCR-N.md`、`components/CMP-N.md`）に書く。詳細設計のファイルは ID を定義しない。ファイル名と見出しで対象の ID を示し、本文では参照だけを行う。
- `UI-N` は `providers.ui_guidelines` が所有する。provider が base のとき、design は `UI-N` を定義しない。
- 定義と参照の書き方、変更時の規則（振り直さない、廃止は `（廃止）` と書いて残す）は、base の ID 規則と同じにする。design 単独のときは `design-foundation/references/id-rules.md` に従う。

### 由来の特別な書き方

| 書き方 | 使う場面 |
|---|---|
| `外部:<パス>#<見出し>` | 上流の文書に ID がないとき（design 単独で、ID のない要件文書を入力にした場合） |
| `追加：<理由>` | 上流のどこにも由来しないとき |

### `ids` の書き方

```json
"SCR": {"owner": ["docs/D2/UX_STRUCTURE.md"], "upstream": ["FR", "OV", "C", "FLW"], "package": "design"}
```

検査スクリプトは、`ids` に登録された接頭辞を検査の対象にする。登録されていない接頭辞は、他のスキル群の ID として参照だけを許す。

## 4. 要素の印（data-ui）

モックと実装の両方で、画面と共通部品の要素に次の属性を付ける。

| 属性 | 付ける要素 | 例 |
|---|---|---|
| `data-ui="SCR-N"` | 画面のルート要素（`body` または最上位のコンテナ） | `<main data-ui="SCR-3">` |
| `data-ui="CMP-N"` | 共通部品のルート要素 | `<button data-ui="CMP-2">` |
| `data-ui="SCR-N/<名前>"` | 画面の領域。`screens/SCR-N.md` の「領域」に書いたもの | `data-ui="SCR-3/summary"` |
| `data-ui="CMP-N/<部位>"` | 部品の部位。`components/CMP-N.md` の「構成」に書いたもの（任意） | `data-ui="CMP-2/label"` |
| `data-rules="UI-N UI-M"` | 規則の適用箇所（モックだけ。任意） | `data-rules="UI-4"` |

## 5. 実装側の義務

`docs/D2/mock/` が存在するプロジェクトで画面を実装するとき、実装は次を守る。

- 4章の `data-ui` を、モックと同じ要素に付ける。本番ビルドで消してもよい。
- `screens/SCR-N.md` の「状態」に書いた各状態を、固定データで表示できる手段を用意する（クエリ、開発用ルート、Storybook のいずれか）。
- 共通部品は、`components/CMP-N.md` の「受け取る値」「状態と変種」「アクセシビリティ」を満たす。
- 色、文字、余白、角丸、影、動きは `design-tokens.json` から生成した値だけを使う。
- モックと意図的に違えるときは、`docs/work/design/waivers.md` に ID、理由、承認者を書く。

base の implement-issue は、設定の `packages` に `"design"` があるときだけ本章を適用する。

## 6. AGENTS.md と CLAUDE.md

- AGENTS.md と CLAUDE.md はプロジェクトが管理する。スキルは書き換えない。
- 各スキル群は、プロジェクトの AGENTS.md に追記してほしい節を雛形として提供する（design はリポジトリ直下の `AGENTS.snippet.md`。スキルには含めない）。追記するかどうかと書き方は、プロジェクトが決める。
- 雛形には、そのスキル群が動いていない作業でも守らせたい規則だけを置く。スキルの使い方はスキル側の文書（design は `design-foundation/references/GUIDE.md`）に置く。

## 7. 互換性

| リポジトリ | 対応する contract |
|---|---|
| uiux_design_skill v0.1.x | 1 |

本書を変えるときは、両リポジトリで同じ変更を行い、互換性のない変更なら `contract` を上げる。
