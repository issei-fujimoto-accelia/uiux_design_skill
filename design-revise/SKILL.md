---
name: design-revise
description: 作成済みのモックに対する開発者の指摘を「層（規則、トークン、導線、部品、画面）× 操作（追加、変更、削除、移動）」で分類し、影響範囲を出して文書からモックまで直し、前後を比較して記録する。モックが完成するまで、1ラウンドずつ繰り返し使う。
---

design-mock で作ったモックを、開発者の指摘で直していく。1回の実行を1ラウンド（R-NN）とし、モックが完成するまで繰り返す。
直す順は常に、文書 → トークン → モックである。モックだけを直さない。

## 手順

1. `../design-foundation/references/GUIDE.md` を読み、設定ファイルを確認する（`../design-foundation/references/config.md`）。
2. 次を読む：[references/change-types.md](references/change-types.md)、`../design-mock/references/conventions.md`、`../design-foundation/references/id-rules.md`、`writing.md`。
3. 開始時の状態を撮る（前後の比較の「前」）。ラウンド番号は `docs/work/design/revisions/` の最大値の次にする。

   ```
   python3 ../design-mock/scripts/shoot.py --root <プロジェクト> --out docs/work/design/revisions/R-NN/before
   ```

4. 指摘を集め、`docs/work/design/revisions/R-NN.md`（雛形：[references/ROUND.template.md](references/ROUND.template.md)）の表に書く。各指摘に、対象の `data-ui`、状態、ビューポートを付ける。対象があいまいな指摘は、ユーザーに確認する。
5. 指摘を change-types.md の「層 × 操作」で分類する。対応（反映／見送り／保留／上流へ）と理由を決める。「注意が要る組み合わせ」に当たる判断（共通部品を廃止するか、新しい部品か変種か、上流に関わるか）は、推奨案と理由を添えてユーザーに一問ずつ確認する。
6. 影響範囲を出し、記録に貼る。

   ```
   python3 scripts/impact.py --root <プロジェクト> --id CMP-2 --id SCR-3 --id UI-4 --id FLW-1 --token color.primary
   python3 scripts/impact.py --root <プロジェクト> --git      # 作業中の差分から自動で求める
   ```

7. change-types.md の共通の手順に従って、上の層から、文書 → トークン → モックの順に直す。
8. ビルドし、検査する。ERROR、NG、ページのエラーを0件にする。

   ```
   python3 ../design-mock/scripts/mock_build.py build --root <プロジェクト>
   python3 ../design-review/scripts/design_check.py all --root <プロジェクト>
   python3 ../design-visual/scripts/tokens.py contrast --root <プロジェクト>
   ```

9. 修正後を撮り、前後を比べる。変化のあった画面だけが一覧の先頭に並ぶ。

   ```
   python3 ../design-mock/scripts/shoot.py --root <プロジェクト> --out docs/work/design/revisions/R-NN/after --compare docs/work/design/revisions/R-NN/before
   ```

   影響範囲の外で変化した画面があれば、意図しない変更として原因を調べる。影響範囲の中で変化しない画面があれば、直し漏れを疑う。
10. 記録の「影響範囲」「実装への影響」「確認」「上流への反映」を埋め、比較のページ（`after/compare.html`）と合わせてユーザーに示す。
11. 次のラウンドに進むか、完了かをユーザーに確認する。完了なら、`docs/work/design/approvals.md` にモックの承認（人の確認③）を記録する。

## 制約

- 1ラウンドで扱う指摘は、ユーザーがそのラウンドで出したものに限る。指摘にない改善を混ぜない。気づいた点は記録の末尾に「提案」として書く。
- 文書にない画面、領域、部品、状態をモックに作らない。
- ID を振り直さない。削除は `（廃止）` と書いて残す。
- モックの完成後（承認後）の変更で、base を併用している場合は、base の変更フロー（変更 Issue）に従う。

## 完了条件（1ラウンド）

- すべての指摘に、層、操作、対応、理由がある
- 反映した指摘について、文書とモックの両方が直っている
- `design_check all` が ERROR 0件、コントラストが NG 0件、`shoot.py` がページのエラー0件
- 前後の比較で、変化した画面が影響範囲と一致している（違う場合は理由を記録した）
- 記録（`R-NN.md`）がそろっている
