# インタビューの進め方

design-foundation と design-structure は、この手順で不足を埋める。目的は質問することではなく、文書を完成させることである。

## 作業状態

`docs/work/design/planning/<スキル名>-state.md` に、次の形で作業状態を置き、回答のたびに更新する。

```markdown
# State: <スキル名>

## Goal / Deliverable / Completion Criteria
- 完了条件（スキルの「完了条件」を写す）: [ ] …

## Decision Areas
### <論点>
Status: unresolved | partial | resolved | deferred
Known: …
Unknown: …

## Decisions（ユーザーが決めたこと）
## Assumptions（仮定したこと。Decision として扱わない）
## Deferred（今回は決めないこと）
```

## 規則

- 質問の前に、入力の文書を読み、書かれていることは Known に入れる。既に決まっていることを質問しない。
- 一度に一問だけ質問する。
- 毎回、推奨案と理由を添える。理由には、ペルソナ、利用状況、`principles.md` の原則名のいずれかを使う。
- 選択肢で答えられる質問は、2〜4個の選択肢を示す。
- 次の質問は、後続の判断に最も影響する未解決の論点から選ぶ（例：ペルソナ → 主タスク → 情報の優先度 → 配置 → 見た目）。
- 曖昧な回答は掘り下げる。「シンプルに」なら「何を減らすか」、「直感的に」なら「誰が、どの操作を、何手で」を聞く。
- ユーザーの指示が目的に対して不利だと考えたら、代替案と理由とトレードオフを短く示す。決めるのはユーザーである。
- 完了条件を満たしたら、聞けることが残っていても終える。残りは Deferred に移す。

## 人の確認

スキルが定める確認点では、文書の該当節（またはモック）を示し、承認を得る。
承認は `docs/work/design/approvals.md` に1行で追記する。

```
| 2026-11-10 | design-foundation | UI_GUIDELINES.md 1〜5節 | 承認 | <承認者> | <メモ> |
```
