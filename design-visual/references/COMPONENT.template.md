# CMP-N 詳細設計：<部品名>

<!-- 共通部品の詳細設計の雛形。docs/D2/components/CMP-N.md として作る。
     - CMP-N の定義（ID、名前、用途、使う画面、理由、由来）は UI_GUIDELINES.md の7節にある。ここでは再定義しない。
     - 必須の節は消さない。当てはまらない場合は表の代わりに「該当なし」と書く。
     - 実装の型やフレームワークの書き方ではなく、どの実装でも同じになる仕様を書く。
     - 値（px、色コード）ではなく、トークン名（bg-primary、min-h-12、duration-fast）を書く。 -->

## 基本

| 項目 | 内容 |
|---|---|
| 用途 | 画面の主要操作を1つ示す |
| 使わない場面 | 補助の操作（代わりに CMP-3 テキストリンク）。破壊的な操作（代わりに CMP-5） |
| 使う画面 | SCR-1, SCR-2 |
| カスタム要素名（モック） | ui-button |

## 構成

部位ごとの `data-ui` は任意。実装と照合したい部位にだけ付ける。

| 部位 | data-ui | 内容 | 必須 |
|---|---|---|---|
| label | CMP-N/label | ボタンの文字 | ○ |
| icon | ― | 文字の前のアイコン | ― |

## 受け取る値

名前はモックのカスタム要素の属性名（ケバブケース）にする。実装では各フレームワークの書き方に読み替える。

| 名前 | 必須 | 既定値 | 選べる値 | 内容 |
|---|---|---|---|---|
| variant | ― | primary | primary, secondary | 見た目の強さ |
| disabled | ― | なし | 真偽 | 押せない |
| busy | ― | なし | 真偽 | 処理中 |

## 状態と変種

名前は、部品カタログ（components.html）の例の `data-example` の値にする。

| 種類 | 名前 | 見た目の違い（トークン名） | きっかけ |
|---|---|---|---|
| 変種 | primary | bg-primary、text-on-primary | 既定 |
| 変種 | secondary | bg-surface、text-ink、border-line | variant="secondary" |
| 状態 | pressed | scale-98 | 押している間 |
| 状態 | focus | outline（primary、2px） | キーボードでフォーカス |
| 状態 | disabled | opacity-50 | disabled |
| 状態 | busy | ラベルの前にスピナー。幅は変えない | busy |

## 大きさと伸び縮み

| 項目 | 内容 |
|---|---|
| 最小の大きさ | min-h-12、min-w-30（principles#target-size） |
| 幅 | 文字に合わせる。画面下部の固定領域では親の幅に合わせる |
| 長い内容 | 1行。収まらなければ2行まで折り返す |

## 動き（任意）

| きっかけ | 変化 | トークン | reduced-motion のとき |
|---|---|---|---|
| 押下 | 縮小 | duration-fast、ease-out | 色だけ変える |

## アクセシビリティ

| 項目 | 内容 |
|---|---|
| role | button |
| 名前 | ラベルの文字。アイコンだけの場合は aria-label |
| キー操作 | Enter、Space で押す |
| 読み上げ | busy のとき aria-busy="true"。ラベルは変えない |

## 規則と理由

| 規則 | 理由 |
|---|---|
| UI-2 | 主要操作は画面下部に固定する |
