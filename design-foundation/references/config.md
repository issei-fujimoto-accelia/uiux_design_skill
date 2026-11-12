# 設定ファイルの確認と初期化

design の各スキルは、作業の最初にこの手順を行う。規則の全体は [CONTRACT.md](CONTRACT.md) にある。

## 手順

1. `docs/skills.config.json` を読む。
2. ファイルがない場合は、design-foundation の `assets/skills.config.json` を `docs/skills.config.json` にコピーする。
3. ファイルがある場合は、次を確認・更新する。
   - `contract` が `1` でなければ、作業を止めてユーザーに報告する。
   - `packages` に `"design"` がなければ追加する。
   - `providers.ui_guidelines` がなければ `"design"` にする。`"base"` なら、下の「provider が base のとき」に従う。
   - `ids` に `PSN`、`CMP`、`SCR`、`FLW` がなければ雛形から追加する。`UI` は provider が design のときだけ追加・更新する。
   - `design` がなければ雛形から追加する。
   - 他のスキル群のキーは消さない、書き換えない。
4. `docs/D2/`、`docs/work/design/` がなければ作る。
5. design-foundation のときだけ：プロジェクトの AGENTS.md に design の節（目安：`data-ui` や「文書 → トークン → モック → 実装」の規則）があるかを確認する。なければ、GUIDE.md の「画面を実装するときの規則」と「デザインの規則」のうち変更の順序を示し、ユーザーに AGENTS.md への追記を提案する（雛形は uiux_design_skill リポジトリ直下の `AGENTS.snippet.md`）。AGENTS.md と CLAUDE.md は自分で書き換えない。

## base が導入されているかの判断

`packages` に `"base"` があるかだけで判断する。スキルのディレクトリを探さない。

| 状態 | 入力 | 由来に書く ID |
|---|---|---|
| base あり | `spec/`、`docs/D1/PROJECT_OVERVIEW.md`、`docs/D2/REQUIREMENTS.md`、`docs/D2/GLOSSARY.md` | `FR`、`NFR`、`OV`、`C` |
| base なし | ユーザーが指定した要件・概要の文書。`spec/`、`docs/D1/` があれば読む | ID があればそれ。なければ `外部:<パス>#<見出し>` |

## provider が base のとき

- `UI_GUIDELINES.md` は base が作る。design は `UI-N` を定義せず、参照だけ行う。
- design の成果のうち、`PSN`、`CMP` と UI の規則に当たるものは、`docs/work/design/proposals/` に提案として書き、ユーザーに base 側の文書への反映を依頼する。
- ユーザーが design に切り替えると決めた場合は、`providers.ui_guidelines` を `"design"` に変える。

## スクリプトのパス

各 SKILL.md のスクリプトのパス（`scripts/…`、`../design-review/scripts/…`）は、そのスキルのディレクトリからの相対パスである。
実行するときは、スキルのインストール先（例：`.claude/skills/`）に読み替え、`--root` にプロジェクトのルートを渡す。
