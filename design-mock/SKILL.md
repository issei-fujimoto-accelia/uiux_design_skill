---
name: design-mock
description: UI_GUIDELINES.md、UX_STRUCTURE.md、画面と部品の詳細設計（screens/、components/）、design-tokens.json から、画面遷移と状態と簡単な動きを人が確認できる HTML モック（Tailwind CSS v4 と Web Components）を docs/D2/mock/ に作り、レビューの指摘を反映する。design-visual の後、実装の前に使う。デザインの変更をモックに反映するときにも使う。
---

デザインの文書を、人が触って確かめられるモックにする。モックは承認後「正」になり、実装はモックに合わせる。
規約は [references/conventions.md](references/conventions.md) に従う。

## 手順

1. 設定ファイルを確認する（`../design-foundation/references/config.md`）。
2. 入力を読む：`docs/D2/UI_GUIDELINES.md`、`docs/D2/UX_STRUCTURE.md`、`docs/D2/screens/SCR-N.md`、`docs/D2/components/CMP-N.md`、`docs/D2/design-tokens.json`。どれかが未作成か、詳細設計に「未決（design-visual）」が残っているなら、足りない工程（design-structure、design-visual）を提案して終える。
3. [references/conventions.md](references/conventions.md) と `../design-foundation/references/principles.md`、`platforms.md` を読む。
4. 配置する。

   ```
   python3 scripts/mock_build.py setup --root <プロジェクト>
   ```

   Tailwind が未導入なら、`npm i -D tailwindcss@4 @tailwindcss/cli@4` をユーザーに提案する（プロジェクトの devDependencies に入る）。
5. 共通部品を先に作る：`components/CMP-N.md` に従い、`assets/components.js` に `CMP-N` を定義する（要素名はカスタム要素名、属性は受け取る値）。`components.html` に「状態と変種」のすべてを `data-example` 付きで並べる。
6. 画面を作る：`SCR-N` ごとに `screens/SCR-N.html` を作り、`screens/SCR-N.md` をそのまま反映する。
   - 領域：各行の `data-ui` を付けた要素を、優先度と配置のとおりに置く。行の「規則」を `data-rules` に付ける
   - 状態：`data-states` と `data-state` を「状態」の表と一致させる
   - 操作：「入口と出口」「操作」の遷移をリンクで、動きをトークンで再現する
   - 文言：「文言」の表の文字をそのまま使う
7. ビルドする。

   ```
   python3 scripts/mock_build.py build --root <プロジェクト>
   ```

8. 自己確認を行い、問題をなくしてから人に見せる。
   - `python3 scripts/shoot.py --root <プロジェクト>`：全画面・全状態・各ビューポートを撮影する。ページのエラーを0件にする。24px 未満のタップ領域は、直すか、理由を `UI-N` に書く。
   - 撮影した画像を見て、UX_STRUCTURE.md の各画面の P1 が最初の画面内に見えるか、主要操作が1つに見えるかを確かめる。
   - `python3 ../design-review/scripts/design_check.py all --root <プロジェクト>`：ERROR を0件にする。
9. 人の確認③：ビューア（`docs/D2/mock/index.html`。配信方法は conventions.md）を示し、FLW-N の順に操作してもらう。注釈（`?annotate=1`）で各判断の理由を確認できることを伝える。
10. 指摘を反映する（下の「指摘の反映」）。承認を `docs/work/design/approvals.md` に記録する。
11. 次の工程として design-review（self-check）を提案する。

## 指摘の反映

指摘は、文書を先に直し、モックを後に直す。モックだけを直さない。

| 指摘の種類 | 直す順 |
|---|---|
| 配置、導線、情報の優先度、状態、文言 | `screens/SCR-N.md`（画面をまたぐなら UX_STRUCTURE.md の `UI-N`）→ モック |
| 色、文字、余白、動き | design-tokens.json と UI_GUIDELINES.md → `mock_build.py build` |
| 部品の形、受け取る値、状態 | `components/CMP-N.md` → components.js と components.html |
| ペルソナやコンセプトに関わる | design-foundation に戻る |

指摘と対応は `docs/work/design/feedback/YYYY-MM-DD.md` に表で記録する（指摘、対象 ID、直した文書、状態）。
承認後の変更は、base を併用している場合は base の変更フロー（変更 Issue）に従う。

## 制約

- モックにロジック（データ取得、検証、業務ルール）を書かない。
- トークン外の値を使わない。足りない値は design-tokens.json に追加する（理由を `UI-N` に書く）。
- 文書にない画面、部品、状態を作らない。必要なら先に文書へ追加を提案する。

## 完了条件

- すべての `SCR-N` に画面があり、文書の状態をすべて切り替えられる
- すべての `CMP-N` が部品カタログに全状態で並んでいる
- 画面の領域、状態、文言が詳細設計と一致し、部品カタログに「状態と変種」がすべて並んでいる
- `design_check.py all` が ERROR 0件、`shoot.py` がページのエラー0件
- 人の確認③が記録され、指摘がすべて反映済みか、理由付きで見送りになっている
