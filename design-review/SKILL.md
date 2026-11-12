---
name: design-review
description: デザインの品質と一貫性を検査する。self-check はモックか実装を採点基準と独立採点で評価して改善を繰り返す。conformance は承認済みモックと実装の差（不足、未設計、スタイルのずれ）を data-ui で検出する。check は ID とモックの網羅を機械的に検査する。モックの作成後、画面の実装後、デザインの変更後に使う。
argument-hint: "[check|self-check|conformance]"
---

引数で検査の種類を受け取る（`$ARGUMENTS`）。指定がない場合は `check` とする。

## 共通

1. 設定ファイルを確認する（`../design-foundation/references/config.md`）。
2. `docs/work/` の記録は照合の基準にしない。基準は `docs/D2/` の文書、トークン、モックである。
3. 指摘には、根拠（ファイルと行、画面と状態）と、直す側の候補（文書／モック／実装）を書く。どれを直すかはユーザーに委ねる。

## check

ID、詳細設計、モックの網羅を機械的に検査する。読み取り専用。

| 検査 | 内容 |
|---|---|
| ids | ID の重複、所有文書外の定義、由来と理由の欠落、未定義の参照、参照されない ID |
| details | 画面と部品の詳細設計の有無、必須の節、領域・状態・受け取る値・状態と変種の必須の列、残った「未決」 |
| mock | 画面ファイルと状態、領域の `data-ui`、部品の定義と要素名、受け取る値の使用、カタログの `data-example`、トークン外の値 |

```
python3 scripts/design_check.py all --root <プロジェクト>
python3 ../design-visual/scripts/tokens.py contrast --root <プロジェクト>
```

会話には ERROR と WARN の件数と、直すべき項目だけを返す。

## self-check

[references/self-check.md](references/self-check.md) の手順で、ラウンドを重ねて改善する。

- 対象は、モック（既定）または実装（引数で `self-check impl`）。実装の場合は、`design.conformance.impl_base_url` の画面を撮影する。
- 独立採点は毎ラウンド必須。作成した文脈を持たないサブエージェント（または新しいセッション）に任せる。
- 改善でモックや文書を直す場合は、design-mock の「指摘の反映」の順に従う。
- 記録は `docs/work/design/rounds/NN/review.md`。

## conformance

[references/conformance.md](references/conformance.md) の手順で、承認済みモックと実装を照合する。読み取り専用。

```
python3 scripts/ui_diff.py --root <プロジェクト>
```

- 実行前に、実装が起動していること、`design.conformance.routes` が UX_STRUCTURE.md の実装ルートと一致していることを確認する。
- レポート（`docs/work/design/conformance/YYYY-MM-DD.md`）の件数と、Issue 化を推奨する差の一覧を会話に返す。

## 完了条件

- check：ERROR と NG が0件、または残りの各件に理由と対応方針がある
- self-check：合格条件を満たした、または上限に達して未達の軸と次の打ち手を記録した
- conformance：すべての差に、直す側の候補か、例外としての理由がある
