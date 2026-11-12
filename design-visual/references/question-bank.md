# 判断の観点（design-visual）

見た目の判断は、質問より先に推奨案を作り、まとめて確認する。各案に理由（`PSN-N`、コンセプト、`principles.md`）を添える。

## 色

- 役割の一覧：surface、ink、line、primary、on-primary、danger。必要なら success、warning、focus
- primary の色相と、コンセプトの「与えたい印象」との対応
- ダークモードの要否。要るなら、すべての色にダークの値を持たせる
- ブランドの既存の色に従う強さ。コントラストが足りない場合の扱い（文字用に暗い色を別に持つ）

## 文字

- 書体（Web フォントか system-ui か）と、日本語・英数字の組み合わせ
- 文字サイズの段階（4〜6段）と、本文の最小サイズ
- 行の高さ、1行の最大文字数（日本語の本文は35〜45字程度が目安）

## 余白と形

- 余白の基準値（4px か 8px）と、関係する要素・しない要素の差（principles#gestalt）
- 角丸の大きさと、印象との対応
- 影の使い方（浮いて見せる要素を限定するか）

## 動き

- 動かす対象と目的（principles#motion-purpose）
- 時間と緩急の値（principles#motion-duration）
- reduced-motion のときの代替

## 予算

- Web フォントの数と容量、CSS と JS の容量、外部リクエスト
