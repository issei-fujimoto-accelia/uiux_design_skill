# モックと実装の照合

承認済みのモックを正として、実装との差を機械的に検出する。規則の全体は `../../design-foundation/references/CONTRACT.md` の4〜5章。

## 実装側に必要なこと

| 必要なこと | 理由 |
|---|---|
| モックと同じ要素に `data-ui="SCR-N"`、`data-ui="CMP-N"`、`data-ui="SCR-N/<名前>"` を付ける | 要素の対応を取るため |
| 各 `SCR-N` の状態を、固定データで表示できる（例：`?state=empty`） | 状態ごとに照合するため |
| トークンから生成した CSS だけを使う（`tokens.py css` または `css-vars`） | 値のずれを防ぐため |

## 設定

`docs/skills.config.json` の `design.conformance` に書く。

```json
"conformance": {
  "impl_base_url": "http://localhost:3000",
  "state_param": "state",
  "routes": {"SCR-1": "/", "SCR-2": "/reservations/demo"}
}
```

- `routes` の値は、UX_STRUCTURE.md の「実装ルート」と一致させる。動的なパスは、固定データの ID を入れる。
- 実装が状態の切り替えを持たない場合は `state_param` を `null` にする。default の状態だけを照合する。

## 実行

```
python3 scripts/ui_diff.py --root <プロジェクト> [--vp ios,desktop] [--screens SCR-1]
```

レポートは `docs/work/design/conformance/YYYY-MM-DD.md` に出る。

## 結果の扱い

| 種類 | 意味 | 直す側の候補 |
|---|---|---|
| 不足 | モックにあり実装にない | 実装に追加する。モックが過剰なら、文書とモックから外す |
| 未設計 | 実装にありモックにない | 文書とモックに追加して承認を得る。不要なら実装から外す |
| 個数 | 同じ要素の数が違う | 固定データの違いか確認する。違いでなければ実装を直す |
| スタイル | 色、文字、余白、角丸、影の違い | トークンを使っていない実装を直す。意図的なら例外にする |
| 取得失敗 | 実装の画面を開けない | ルート、サーバーの起動、固定データを確認する |

- どちらを直すかはユーザーが決める。レポートには候補だけを書く。
- 直すべき差は Issue にする（base を併用している場合は base の Issue の手順に従う）。
- 意図的な差は `docs/work/design/waivers.md` に表で書く。先頭列の `data-ui` の ID は、照合で「例外」として分けて報告される。

```markdown
| ID | 差 | 理由 | 承認者 | 日付 |
|---|---|---|---|---|
| CMP-4 | 実装では OS 標準の日付選択を使う | ネイティブの操作性を優先（principles#jakob） | 藤本 | 2026-11-10 |
```
