// 共通部品（CMP）の定義。UI_GUIDELINES.md の7節と1対1で対応させる。
// - render は HTML 文字列を返すだけにする。データ取得、検証、業務ロジックを書かない。
// - クラス名は完全な文字列で書く（`bg-${x}` のように組み立てない）。Tailwind が検出できないため。
// - 色、文字、余白はトークン由来のクラスだけを使う。任意値（bg-[#123456]、p-[13px]）を使わない。
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
