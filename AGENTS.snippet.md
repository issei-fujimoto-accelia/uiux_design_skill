<!-- uiux_design_skill を使うプロジェクトの AGENTS.md に、人がコピーして追記する節。
     デザインのスキルが動いていない作業（画面の実装など）でも守らせたい規則だけを置く。
     <skills> はスキルのインストール先（例：.claude/skills）に置き換える。
     CLAUDE.md を使う場合は、CLAUDE.md に `@AGENTS.md` と書いて AGENTS.md を取り込む。 -->

## デザイン

- デザインの正は `docs/D2/` の `UI_GUIDELINES.md`、`UX_STRUCTURE.md`、`screens/`、`components/`、`design-tokens.json`、`mock/`（承認後）。`docs/work/design/` は記録であり、根拠にしない。
- デザインを変えるときは、文書 → トークン → モック → 実装の順に直す。モックや実装だけを直さない。
- 画面を実装するときは、モックと同じ要素に `data-ui`（`SCR-N`、`SCR-N/<領域>`、`CMP-N`）を付け、`screens/SCR-N.md` の各状態を固定データで表示できるようにする。
- 部品は `components/CMP-N.md` の受け取る値、状態と変種、アクセシビリティを満たす。
- 色、文字、余白、角丸、影、動きは、`design-tokens.json` から生成した CSS だけを使う。モックと意図的に違えるときは `docs/work/design/waivers.md` に ID、理由、承認者を書く。
- `docs/D2/mock/assets/` の生成物（`theme.css`、`manifest.js`、`annotations.js`、`mock.css`）を直接編集しない。
- 詳細は `<skills>/design-foundation/references/GUIDE.md` を読む。
