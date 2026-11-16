// 共通部品（CMP）の定義。UI_GUIDELINES.md の7節と1対1で対応させる。
// - render は HTML 文字列を返すだけにする。データ取得、検証、業務ロジックを書かない。
// - クラス名は完全な文字列で書く（`bg-${x}` のように組み立てない）。Tailwind が検出できないため。
// - 色、文字、余白はトークン由来のクラスだけを使う。任意値（bg-[#123456]、p-[13px]）を使わない。
// - 画面をまたいで同じ見た目のもの（ボタン、カード、ヘッダー、タブバー、画面の枠）は、必ずここで定義し、
//   画面では要素（<ui-xxx>）だけを書く。画面に同じ HTML を手書きしない。
const { defineComponent } = window.MockKit;

// 例：CMP-1 主要ボタン。プロジェクトの CMP に置き換える。
const BUTTON_VARIANTS = {
  primary: "bg-primary text-on-primary",
  secondary: "bg-surface text-ink border border-line",
};

defineComponent("ui-button", {
  id: "CMP-1",
  rules: [],
  render: (a, content) => `
    <button type="button"
      class="inline-flex min-h-12 min-w-30 items-center justify-center gap-2 rounded-md px-5 text-base font-semibold
             transition-transform duration-(--duration-fast) ease-out active:scale-98 disabled:opacity-50
             ${BUTTON_VARIANTS[a.variant || "primary"]}"
      ${"disabled" in a ? "disabled" : ""} ${"busy" in a ? 'aria-busy="true"' : ""}>
      ${content}
    </button>`,
});

// 例：CMP-N レイアウト部品（画面の枠）。差し込み口（slots）で、画面ごとの中身を受け取る。
// 画面側の書き方：
//   <ui-app-shell back="SCR-1.html" back-label="予約一覧">
//     <h1 slot="title">予約詳細</h1>
//     <section>本文</section>
//     <ui-button slot="actions">日時を変更する</ui-button>
//   </ui-app-shell>
//
// defineComponent("ui-app-shell", {
//   id: "CMP-N",
//   slots: ["title", "actions"],
//   render: (a, content, s) => `
//     <div class="min-h-dvh bg-surface text-ink">
//       <header data-ui="CMP-N/header" class="flex items-center gap-2 px-4 pt-4">
//         ${a.back ? `<a href="${a.back}" class="text-primary">← ${a.backLabel || "戻る"}</a>` : ""}
//       </header>
//       <main class="mx-auto max-w-xl px-4 pt-2 pb-28">${s.title || ""}${content}</main>
//       ${s.actions ? `<div data-ui="CMP-N/actions" class="fixed inset-x-0 bottom-0 bg-surface p-4">${s.actions}</div>` : ""}
//     </div>`,
// });
