# デザイントークン

値の元データは `docs/D2/design-tokens.json` の1つだけにする。モックと実装は、ここから生成した CSS だけを使う。
例：[../assets/design-tokens.example.json](../assets/design-tokens.example.json)

## 形式

W3C Design Tokens（DTCG）の形に合わせる。`$value` を持つ節がトークンになる。子を持つ節にも `$value` を置ける。

| キー | 内容 |
|---|---|
| `$value` | 値。書体は配列 |
| `$type` | `color`、`dimension`、`fontFamily`、`shadow`、`cubicBezier`、`duration` |
| `$extensions.modes.<モード>` | モードごとの値（例：`dark`） |
| `$extensions.lineHeight` | `text` の行の高さ |
| `$description` | 用途（任意） |
| `$contrast`（最上位） | コントラストを検査する組み合わせ。`fg`、`bg`、`min`、`note` |

## グループと生成される CSS

| グループ | CSS 変数 | Tailwind の例 |
|---|---|---|
| `color` | `--color-*` | `bg-surface`、`text-ink-muted`、`border-line` |
| `font` | `--font-*` | `font-sans` |
| `text` | `--text-*`（`--text-*--line-height`） | `text-base` |
| `weight` | `--font-weight-*` | `font-bold` |
| `leading` / `tracking` | `--leading-*` / `--tracking-*` | `leading-tight` |
| `spacing` | `--spacing`（基準値）、`--spacing-*` | `p-4`（基準値×4） |
| `radius` / `shadow` | `--radius-*` / `--shadow-*` | `rounded-md`、`shadow-raised` |
| `ease` | `--ease-*` | `ease-out` |
| `breakpoint` / `container` | `--breakpoint-*` / `--container-*` | `md:` |
| `duration` / `z` | `--duration-*` / `--z-*`（Tailwind の名前空間外） | `duration-(--duration-fast)` |

- `color`、`font`、`text`、`radius`、`shadow`、`ease` などを定義すると、Tailwind の既定値を消す（`--color-*: initial`）。トークン外の色（`bg-red-500`）は使えなくなる。
- 色は役割で命名する。ユーティリティとして読める名前にする（`surface`、`ink`、`line`、`primary`、`on-primary`、`danger`）。色相の名前（`blue-500`）を使わない。

## コマンド

```
python3 <skills>/design-visual/scripts/tokens.py contrast --root .   # コントラストの検査
python3 <skills>/design-visual/scripts/tokens.py css --root .        # docs/D2/mock/assets/theme.css を生成
python3 <skills>/design-visual/scripts/tokens.py css-vars --root . --out <path>  # Tailwind を使わない実装向け
```

## 実装への引き継ぎ

- Tailwind v4 を使う実装：`css` の出力をそのまま読み込む。
- それ以外：`css-vars` の出力を読み込み、各フレームワークのテーマから CSS 変数を参照する。
- 実装側で値を書き写さない。トークンを変えるときは、JSON を変えて両方を生成し直す。
