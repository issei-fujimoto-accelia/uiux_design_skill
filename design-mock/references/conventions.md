# モックの規約

モックは、デザインの判断を人が見て確かめるためのものである。実装の下書きではない。
HTML、Tailwind CSS v4、Web Components（Light DOM）で作り、ビルド以外の仕組みを持ち込まない。

## 配置

```
docs/D2/mock/
  index.html                ビューア（スキルが配置。編集しない）
  components.html           部品カタログ（CMP-N ごとに section id="CMP-N"）
  screens/SCR-N.html        画面（1画面1ファイル。_template.html をコピーして作る）
  assets/
    components.js           共通部品の定義（CMP-N）
    input.css               Tailwind の入力（スキルが配置。編集しない）
    mock-kit.js             状態・注釈・部品の補助（スキルが配置。編集しない）
    theme.css               生成：トークン → CSS
    manifest.js             生成：画面の一覧
    annotations.js          生成：注釈の内容
    mock.css                生成：Tailwind のビルド結果
```

生成物（theme.css、manifest.js、annotations.js、mock.css）は直接編集しない。

## 書いてよいもの・いけないもの

| 書いてよい | 書いてはいけない |
|---|---|
| 固定の文言とデータ（`screens/SCR-N.md` の文言に合わせる） | データ取得、API 呼び出し、保存 |
| 状態の切り替え（`data-state`） | 入力の検証、計算、業務ルール |
| 画面間のリンク、部品の開閉など見た目の確認に要る最小の操作 | ルーティングの仕組み、状態管理のライブラリ |
| トークン由来の Tailwind クラス | 任意値（`bg-[#123456]`、`p-[13px]`）、`style` 属性での色や大きさ |

## 画面

- 画面は `docs/D2/screens/SCR-N.md`（詳細設計）を写す。詳細設計にない領域、状態、文言を作らない。
- `body` に `data-ui="SCR-N"` と `data-states="<状態をスペース区切り>"` を書く。状態は詳細設計の「状態」の表と一致させる。
- 状態ごとの内容は `data-state="<状態>"` の要素に入れる。複数の状態で共通なら `data-state="default error"`。
- プラットフォームで変わる部分は `data-platform="ios"` のように書く。既定のプラットフォームは `web`。
- 詳細設計の「領域」の各行について、`data-ui="SCR-N/<名前>"` を付けた要素を置き、行の「規則」を `data-rules` に書く。
- 画面間の移動は相対リンク（`<a href="SCR-2.html">`）で書く。遷移の演出は View Transitions（`input.css` で有効）を使う。要素をつなげて見せる場合は、両画面の要素に同じ `view-transition-name` を付ける。
- 画面の上下の安全領域（ノッチ、ホームインジケーター）は、`pt-[env(...)]` ではなく、余白のトークンで近似する。

## 共通部品とレイアウト

共通部品とレイアウト（画面の枠）は、`assets/components.js` に1回だけ定義し、画面からは要素（`<ui-xxx>`）で使う。
部品の定義を直せば、使っているすべての画面に反映される。画面に同じ HTML を手書きすると、修正が一部の画面にだけ反映されるずれが起きる。

| 禁止 | 代わりに | 検査 |
|---|---|---|
| 画面に部品と同じ見た目の HTML を手書きする | 部品の要素を使う。画面独自にする場合は、詳細設計の「画面独自の要素」に書く | 「部品の手書きの疑い」（WARN） |
| 画面に `data-ui="CMP-N"` を直接書く | 部品の要素を使う（`data-ui` は部品が自動で付ける） | 「部品の直書き」（ERROR） |
| 定義していない要素名を書く（綴りの誤りなど） | components.js に定義する | 「未定義の部品要素」（ERROR） |
| ヘッダー、戻るリンク、主要操作の固定領域を画面ごとに書く | レイアウト部品（下記）を使う | 「部品の手書きの疑い」（WARN） |

### 定義の書き方

- `MockKit.defineComponent("ui-<名前>", { id: "CMP-N", rules: ["UI-N"], slots: ["<差し込み口>"], render })` と定義する。
- `render(attrs, content, slots)` は、ルートの要素1つを含む HTML 文字列を返す。部品は描画後にルートの要素に置き換わる。
  - `attrs`：属性。ケバブケースはキャメルケースになる。真偽の属性は `"name" in attrs` で判定する
  - `content`：`slot` 属性のない子の HTML
  - `slots`：`slot` 属性を持つ子の HTML を、差し込み口の名前ごとにまとめたもの
- カスタム要素に書いた `class`、`id`、`data-state`、`data-platform`、`data-rules`、`data-example`、`aria-*` はルートに引き継がれる。
- 状態は属性で受け取る（`<ui-button disabled>`、`<ui-field error="…">`）。
- クラス名は完全な文字列で書き、組み立てない（Tailwind が検出できないため）。変種は文字列の対応表で選ぶ。
- 要素名、属性名、差し込み口は `docs/D2/components/CMP-N.md` の「カスタム要素名」「受け取る値」「構成」の差し込み口と一致させる。

### レイアウト部品

画面の枠（戻るリンク、見出し、本文の幅、主要操作の固定領域、タブバーなど）は、レイアウト部品として定義する。詳細設計の「基本」の種類を「レイアウト」にし、画面の詳細設計の「基本」の「レイアウト」に `CMP-N` を書く。

```html
<body data-ui="SCR-2" data-states="default error">
  <ui-app-shell back="SCR-1.html" back-label="予約一覧">
    <h1 slot="title">予約詳細</h1>
    <section data-ui="SCR-2/summary">…</section>
    <div slot="actions" data-ui="SCR-2/actions"><ui-button>日時を変更する</ui-button></div>
  </ui-app-shell>
</body>
```

画面間のリンクは、`href` だけでなく部品の属性（例：`back="SCR-1.html"`）に書いてもよい。遷移の検査は、`="SCR-N.html"` の形の値をすべてリンクとして扱う。
- 部品カタログ（`components.html`）では、`<section id="CMP-N">` の中に、詳細設計の「状態と変種」の各名前について `data-example="<名前>"` を付けた例を置く（1つの例が複数を兼ねる場合はスペース区切り）。押下、ホバー、フォーカスのように操作でしか出ない状態も、例を置いて操作で確認できるようにする。

## 確認の URL

| クエリ | 内容 |
|---|---|
| `?state=empty` | 状態を切り替える |
| `?theme=dark` | テーマを切り替える（既定は端末の設定） |
| `?platform=ios` | プラットフォームを切り替える |
| `?annotate=1` | `data-ui` と `data-rules` を枠で示し、クリックで定義と理由を表示する |

`theme`、`platform`、`annotate` は画面間のリンクで引き継がれる。

## 配信

View Transitions とリンクの確認には、HTTP で配信して開く（`file://` では遷移の演出が効かない）。

```
python3 -m http.server -d docs/D2/mock 8000   # http://localhost:8000/
```
