---
name: design-structure
description: 画面を持つプロダクトの情報構造、操作シナリオ、画面遷移、ナビゲーション、配置、操作方法をインタビューで決め、UX_STRUCTURE.md と画面ごとの詳細設計（screens/SCR-N.md）を作る。design-foundation の後、見た目やモックを作る前に使う。画面の構成や導線を見直すときにも使う。
---

「どの画面に、何を、どの順で、どこに置き、どう操作させるか」を決める。
見た目（色、書体、部品の形）はここでは決めない。

## 手順

1. 設定ファイルを確認する（`../design-foundation/references/config.md`）。
2. 入力を読む。
   - base の有無に応じた入力（config.md の表）。要件の画面一覧と機能を特に見る。
   - `docs/D2/UI_GUIDELINES.md`（ペルソナ `PSN-N`、全体の規則 `UI-N`）。未作成なら design-foundation を先に実行するよう提案して終える。
   - 既存の `docs/D2/UX_STRUCTURE.md`。
3. 次を読む。
   - `../design-foundation/references/interview.md`、`principles.md`、`platforms.md`、`id-rules.md`、`writing.md`
   - [references/question-bank.md](references/question-bank.md)
   - [references/UX_STRUCTURE.template.md](references/UX_STRUCTURE.template.md)、[references/SCREEN.template.md](references/SCREEN.template.md)
4. 要件から操作シナリオと画面の候補を洗い出し、作業状態（`docs/work/design/planning/design-structure-state.md`）に入れる。
5. 不足を一問ずつ確認する。順序の目安は、操作シナリオ → 画面一覧と主タスク → ナビゲーション → 画面ごとの情報の優先度 → 配置と操作方法 → 遷移。
6. 書く。
   - `docs/D2/UX_STRUCTURE.md`：操作シナリオ、画面一覧、遷移、画面をまたぐ規則
   - `docs/D2/screens/SCR-N.md`：画面ごとの詳細設計。すべての `SCR-N` に作る。雛形の節と列を変えない。「部品」「動き」の列は「未決（design-visual）」としてよい
7. 人の確認②：操作シナリオ、画面遷移、各画面の領域と状態（詳細設計のワイヤー）を示し、承認を得る。承認を `docs/work/design/approvals.md` に記録する。
8. 検査を実行し、ERROR を0件にする。

   ```
   python3 ../design-review/scripts/design_check.py ids --root <プロジェクト>
   python3 ../design-review/scripts/design_check.py details --root <プロジェクト>
   ```

9. 次の工程として design-visual を提案する。

## 判断の規則

- 各画面の主タスクは1つにする。2つ以上になる場合は、分割するか、片方を P2 に下げる案を示す。
- 配置と操作の判断には、理由として `PSN-N` か `principles.md` の原則名を書く。
- 慣習（`platforms.md`）から外れる判断は、`UI-N` として理由を書く。
- 操作シナリオの手数が目標を超えたら、画面の統合、既定値、入力の削減の案を示す。

## 制約

- provider が base のときは、`UI-N` を定義しない。配置と操作の規則は `docs/work/design/proposals/structure.md` に提案として書く。
- 要件にない画面や機能を追加した場合は、由来に `追加：<理由>` と書き、文書末尾の「上流への反映」節に列挙してユーザーに報告する。

## 完了条件

- 主要な操作シナリオが `FLW-N` で定義され、手順と手数がある
- 要件の画面がすべて `SCR-N` で定義され、主タスクと主なペルソナがある
- すべての `SCR-N` に詳細設計（`docs/D2/screens/SCR-N.md`）があり、必須の節（基本、入口と出口、領域、状態、操作、文言）が埋まっている
- 各画面の領域に `data-ui`、優先度、理由があり、状態に `default` を含む
- 画面遷移が図と表で示され、各画面の「入口と出口」と一致している
- ナビゲーションと配置の規則が `UI-N` で定義され、理由と由来がある
- 人の確認②が記録されている
