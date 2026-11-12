---
name: design-visual
description: 画面を持つプロダクトの色、文字、余白、角丸、影、動きをデザイントークン（design-tokens.json）として決め、共通部品（CMP）の詳細設計（components/CMP-N.md）を作る。UX_STRUCTURE.md ができた後、モックを作る前に使う。見た目やトークンを見直すときにも使う。
---

ペルソナ、コンセプト、画面の構成から、見た目の規則とトークンを決める。
値は `docs/D2/design-tokens.json` にだけ書き、理由は `UI_GUIDELINES.md` の `UI-N` に書く。

## 手順

1. 設定ファイルを確認する（`../design-foundation/references/config.md`）。
2. 入力を読む：`docs/D2/UI_GUIDELINES.md`、`docs/D2/UX_STRUCTURE.md`、`docs/D2/screens/`、既存の `docs/D2/design-tokens.json` と `docs/D2/components/`。UX_STRUCTURE.md が未作成なら、design-structure を先に実行するよう提案して終える。
3. 次を読む。
   - [references/tokens.md](references/tokens.md)、[references/components.md](references/components.md)、[references/question-bank.md](references/question-bank.md)
   - [references/COMPONENT.template.md](references/COMPONENT.template.md)
   - `../design-foundation/references/principles.md`、`platforms.md`、`id-rules.md`、`writing.md`
4. 色、文字、余白と形、動きの推奨案を作る。各案に理由を添え、観点ごとにまとめてユーザーに確認する。一度に確認するのは1つの観点だけにする。
5. 画面の詳細設計の「領域」から共通部品を洗い出し、`CMP-N` の案を作って確認する（基準は components.md）。
6. 書く。
   - `docs/D2/design-tokens.json`（`$contrast` に、文字と背景の組み合わせをすべて列挙する）
   - `docs/D2/UI_GUIDELINES.md` の6〜9節（7節は部品の一覧だけ）
   - `docs/D2/components/CMP-N.md`：部品ごとの詳細設計。すべての `CMP-N` に作る。雛形の節と列を変えない
   - `docs/D2/screens/SCR-N.md` の「部品」「動き」の列（「未決（design-visual）」を埋める）
7. 検査を実行し、NG と ERROR を0件にする。

   ```
   python3 scripts/tokens.py contrast --root <プロジェクト>
   python3 ../design-review/scripts/design_check.py ids --root <プロジェクト>
   python3 ../design-review/scripts/design_check.py details --root <プロジェクト>
   ```

8. 次の工程として design-mock を提案する。

## 判断の規則

- 色は役割で定義する。1つの役割に1つの値（モードごと）を持たせる。
- 強調の段階は3〜4段に抑える（principles#hierarchy）。
- 動きは目的を1つ持つものだけ定義する。reduced-motion の代替を必ず書く。
- コントラストが基準を満たさない色は使わない。ブランドの色が満たさない場合は、文字用の色を別の役割として持つ案を示す。

## 制約

- provider が base のときは、UI_GUIDELINES.md に書かない。6〜9節の内容を `docs/work/design/proposals/visual.md` に提案として書く。`design-tokens.json` は design が書いてよい。
- トークンの値を文書の本文に書き写さない。文書にはトークン名と理由だけを書く。

## 完了条件

- `design-tokens.json` に色（モードごと）、文字、余白、角丸、影、動きがある
- コントラストの検査が NG 0件
- 6〜9節の規則が `UI-N` で定義され、理由と由来がある
- 共通部品が `CMP-N` で定義され、すべてに詳細設計（`docs/D2/components/CMP-N.md`）がある。必須の節（基本、構成、受け取る値、状態と変種、大きさと伸び縮み、アクセシビリティ、規則と理由）が埋まっている
- 画面の詳細設計に「未決（design-visual）」が残っていない
