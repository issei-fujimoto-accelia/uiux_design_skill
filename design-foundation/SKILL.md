---
name: design-foundation
description: 画面を持つプロダクト（Web、iOS、Android）のデザインの土台として、品質方針の解釈、ペルソナ、利用状況、コンセプト、全体の規則をインタビューで決め、UI_GUIDELINES.md の基礎の節を作る。デザイン作業の最初、または対象ユーザーやコンセプトを見直すときに使う。
---

デザインの判断の「理由」の源になる、ペルソナとコンセプトを決める。
後続の design-structure、design-visual、design-mock は、ここで決めた `PSN-N` と `UI-N` を理由として参照する。

## 手順

1. 設定ファイルを確認・初期化する（[references/config.md](references/config.md)）。
2. 入力を読む。base の有無で入力が変わる（config.md の表）。既存の `docs/D2/UI_GUIDELINES.md` があれば読む。
3. 次を読む。
   - [references/interview.md](references/interview.md)：インタビューの進め方
   - [references/question-bank.md](references/question-bank.md)：質問の観点
   - [references/principles.md](references/principles.md)：判断の根拠
   - [references/platforms.md](references/platforms.md)：プラットフォームの慣習
   - [references/id-rules.md](references/id-rules.md)、[references/writing.md](references/writing.md)
4. 入力から分かることを作業状態（`docs/work/design/planning/design-foundation-state.md`）の Known に入れ、不足を Decision Areas に整理する。
5. 不足を一問ずつ確認する。
6. 完了条件を満たしたら、`docs/D2/UI_GUIDELINES.md` の0〜5節を書く（雛形：[references/UI_GUIDELINES.template.md](references/UI_GUIDELINES.template.md)）。6節以降は「未作成（design-visual）」と残す。
7. 人の確認①：1〜4節を示し、承認を得る。承認を `docs/work/design/approvals.md` に記録する。
8. 検査を実行し、ERROR を0件にする。

   ```
   python3 ../design-review/scripts/design_check.py ids --root <プロジェクト>
   ```

9. 次の工程として design-structure を提案する。

## 制約

- provider が base のときは、UI_GUIDELINES.md を書かない。成果を `docs/work/design/proposals/foundation.md` に書き、反映をユーザーに依頼する（config.md）。
- ペルソナの属性を推測で埋めない。不明な属性は「未決」と書く。
- 上流の文書（要件、概要、一次ドキュメント）と矛盾する決定をした場合や、上流の未決事項を決めた場合は、文書末尾の「上流への反映」節に列挙し、ユーザーに報告する。上流の文書は承認なしに編集しない。

## 完了条件

- 品質方針の解釈と、使わない表現が書かれている
- ペルソナが `PSN-N` で定義され、それぞれに利用状況と「デザインへの含意」がある
- 判断が割れたときに優先するペルソナが決まっている
- コンセプト、与えたい印象と与えたくない印象、シグネチャーが書かれている
- 全体の規則が `UI-N` で定義され、各行に理由と由来がある
- 品質基準（合格点、比較対象3つ以上、最大ラウンド数）が決まっている
- 人の確認①が記録されている
