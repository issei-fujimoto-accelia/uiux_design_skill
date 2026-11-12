# uiux_design_skill

画面を持つプロダクト（Web、iOS、Android）のデザインを、理由の付いた文書と HTML モックとして作るスキル群。
単独で使えるほか、base_skill（Issue 駆動の開発フロー）と組み合わせても使える。組み合わせ方は [CONTRACT.md](design-foundation/references/CONTRACT.md) に定める。

変更履歴は `release-notes/` を参照（最新：[v0.1.0](release-notes/v0.1.0.md)）。

## install

```shell
npx skills add issei-fujimoto-accelia/uiux_design_skill
# Claude Code の場合
npx skills add issei-fujimoto-accelia/uiux_design_skill -a claude-code
```

<!-- リポジトリの公開先が決まったら、上のパスを確認する -->

## スキル

| スキル | 決めること | 出力 | 人の確認 |
|---|---|---|---|
| design-foundation | 品質方針の解釈、ペルソナ（PSN）、利用状況、コンセプト、全体の規則 | `UI_GUIDELINES.md` 0〜5節 | ① コンセプト |
| design-structure | 操作シナリオ（FLW）、画面（SCR）、遷移、ナビゲーション、配置、操作方法、情報の優先度 | `UX_STRUCTURE.md`、`screens/SCR-N.md` | ② 導線とワイヤー |
| design-visual | 色、文字、余白、角丸、影、動き、共通部品（CMP） | `design-tokens.json`、`UI_GUIDELINES.md` 6〜9節、`components/CMP-N.md` | ― |
| design-mock | HTML モック（Tailwind CSS v4、Web Components） | `docs/D2/mock/` | ③ モック |
| design-review | 機械検査（check）、採点による改善（self-check）、モックと実装の照合（conformance） | `docs/work/design/` | ― |

## 利用フロー

```shell
（要件・概要の文書：base の docs/D2/REQUIREMENTS.md、または任意の要件文書）
    ↓
design-foundation   ペルソナとコンセプトを決める           → 人の確認①
    ↓
design-structure    導線、画面、配置、操作を決める         → 人の確認②
    ↓
design-visual       トークンと共通部品を決める
    ↓
design-mock         モックを作り、指摘を反映する           → 人の確認③（承認後、モックは正）
    ↓
design-review self-check   採点と独立採点で品質を上げる
    ↓
（実装：モックに合わせて data-ui を付けて実装する）
    ↓
design-review conformance  モックと実装の差を検出する
```

すべての判断には ID を振り、理由を書く。モックでは `?annotate=1` で、各要素の ID と理由を確認できる。

## ディレクトリ構成（プロジェクト側）

```shell
docs/skills.config.json     スキル群の設定（雛形：`design-foundation/assets/skills.config.json`）
docs/D2/
  UI_GUIDELINES.md          品質方針、ペルソナ、コンセプト、規則、共通部品（PSN / UI / CMP）
  UX_STRUCTURE.md           操作シナリオ、画面一覧、遷移、画面をまたぐ規則（FLW / SCR / UI）
  screens/SCR-N.md          画面の詳細設計（領域、状態、操作、文言）
  components/CMP-N.md       部品の詳細設計（構成、受け取る値、状態と変種、大きさ、アクセシビリティ）
  design-tokens.json        トークンの元データ（モックと実装が共用）
  mock/                     モック（承認後は正）
docs/work/design/           記録（正ではない）
  planning/                 インタビューの作業状態
  approvals.md              人の確認の記録
  feedback/                 モックへの指摘と対応
  proposals/                provider が base のときの提案
  shots/                    スクリーンショット
  rounds/NN/review.md       self-check の記録
  conformance/              モックと実装の照合結果
  waivers.md                モックと実装の意図的な差
```

## 前提

| ツール | 用途 |
|---|---|
| Python 3.10 以上 | 検査と生成のスクリプト（標準ライブラリのみ） |
| Node.js と `tailwindcss@4`、`@tailwindcss/cli@4` | モックの CSS のビルド（`npm i -D tailwindcss@4 @tailwindcss/cli@4`） |
| Python の `playwright` | スクリーンショットと照合（`pip install playwright && python -m playwright install chromium`） |

## コマンド

`<skills>` はスキルのインストール先（例：`.claude/skills`）。

```shell
python3 <skills>/design-mock/scripts/mock_build.py setup --root .     # モックの雛形を配置
python3 <skills>/design-mock/scripts/mock_build.py build --root .     # トークン → CSS、一覧、Tailwind のビルド
python3 <skills>/design-mock/scripts/shoot.py --root .                # 全画面・全状態の撮影と機械チェック
python3 <skills>/design-review/scripts/design_check.py all --root .   # ID、詳細設計、モックの網羅
python3 <skills>/design-visual/scripts/tokens.py contrast --root .    # コントラスト
python3 <skills>/design-review/scripts/ui_diff.py --root .            # モックと実装の照合
python3 -m http.server -d docs/D2/mock 8000                           # モックを開く
```

## base_skill と組み合わせる

設定ファイルの `packages` に `"base"` と `"design"` を並べ、`providers.ui_guidelines` を `"design"` にする。
design は base のスキルを直接呼ばない。base 側で必要な対応（CONTRACT.md の写し、設定を読む ID 検査、UI 文書の provider の判定、実装時の data-ui の義務）は、base のリリースで行う。

| 状況 | UI_GUIDELINES.md を作るもの | design が読む上流 |
|---|---|---|
| design だけ | design | ユーザーが指定した要件文書（由来は `外部:<パス>#<見出し>`） |
| base だけ | base（簡易版） | ― |
| 両方 | `providers.ui_guidelines` で選ぶ | `REQUIREMENTS.md` の FR / NFR、`PROJECT_OVERVIEW.md` の OV、`spec/` の C |

## 書き方

文書は [design-foundation/references/writing.md](design-foundation/references/writing.md) に従って短く書く。プロジェクトに書き方の規則と用語集があれば、そちらを優先する。
