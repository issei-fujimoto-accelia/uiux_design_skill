// mock-kit.js：モックの実行時の補助（design-mock が配置する。直接編集しない）。
// 状態の切り替え、部品の定義、注釈の表示、テーマとプラットフォームの切り替えだけを行う。
// データ取得、検証、業務ロジックは書かない。
(function () {
  "use strict";
  const params = new URLSearchParams(location.search);
  const state = params.get("state") || "default";
  const platform = params.get("platform") || "web";
  const theme = params.get("theme");
  const annotate = params.get("annotate") === "1";
  const root = document.documentElement;
  if (theme) root.dataset.theme = theme;
  root.dataset.platform = platform;
  root.dataset.state = state;

  // ---- 共通部品（CMP） ----
  const registry = new Map();
  const toCamel = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

  /**
   * 共通部品を定義する。
   * @param {string} tag カスタム要素名（例：ui-button）
   * @param {{id: string, rules?: string[], render: (attrs: object, content: string) => string}} def
   *   id は CMP-N。render は HTML 文字列を返す。ルートの要素は1つにする。
   *   カスタム要素は描画後にルートの要素で置き換わる（実装と同じ DOM になり、親の space-y や gap が効く）。
   *   カスタム要素に書いた class、id、data-state、data-platform、data-rules、data-example、aria-* はルートに引き継ぐ。
   */
  const PASS = /^(class|id|data-state|data-platform|data-rules|data-example|aria-.+|role)$/;
  function defineComponent(tag, def) {
    if (!/^CMP-\d+$/.test(def.id)) console.warn(`[mock] ${tag}: id は CMP-N の形式にする`, def.id);
    registry.set(tag, def);
    customElements.define(
      tag,
      class extends HTMLElement {
        connectedCallback() {
          const attrs = {};
          for (const a of this.attributes) attrs[toCamel(a.name)] = a.value;
          const tpl = document.createElement("template");
          tpl.innerHTML = def.render(attrs, this.innerHTML).trim();
          const el = tpl.content.firstElementChild;
          if (!el || tpl.content.children.length > 1) {
            console.warn(`[mock] ${tag}: render はルートの要素を1つだけ返す`);
            if (!el) return;
          }
          for (const a of this.attributes) {
            if (!PASS.test(a.name)) continue;
            if (a.name === "class") el.className = `${el.className} ${a.value}`.trim();
            else if (a.name === "data-rules") continue;
            else el.setAttribute(a.name, a.value);
          }
          el.setAttribute("data-ui", def.id);
          const rules = [el.getAttribute("data-rules"), this.getAttribute("data-rules"), ...(def.rules || [])].filter(Boolean);
          if (rules.length) el.setAttribute("data-rules", [...new Set(rules.join(" ").split(/\s+/))].join(" "));
          this.replaceWith(el);
        }
      }
    );
  }

  // ---- 状態とプラットフォーム ----
  function applyVisibility() {
    document.querySelectorAll("[data-state]").forEach((el) => {
      if (el === document.body) return;
      el.hidden = !el.dataset.state.split(/\s+/).includes(state);
    });
    document.querySelectorAll("[data-platform]").forEach((el) => {
      if (el === root) return;
      el.hidden = el.hidden || !el.dataset.platform.split(/\s+/).includes(platform);
    });
  }

  // 画面間のリンクで、テーマ、プラットフォーム、注釈の指定を引き継ぐ（状態は引き継がない）
  function keepParams() {
    const keep = ["theme", "platform", "annotate"].filter((k) => params.has(k));
    if (!keep.length) return;
    document.querySelectorAll("a[href]").forEach((a) => {
      const href = a.getAttribute("href");
      if (!href || /^(https?:|mailto:|#)/.test(href)) return;
      const i = href.indexOf("#");
      const hash = i >= 0 ? href.slice(i) : "";
      const [path, query = ""] = (i >= 0 ? href.slice(0, i) : href).split("?");
      const sp = new URLSearchParams(query);
      keep.forEach((k) => sp.has(k) || sp.set(k, params.get(k)));
      a.setAttribute("href", `${path}?${sp}${hash}`);
    });
  }

  // ---- 注釈（?annotate=1） ----
  function annotateLayer() {
    const notes = window.MOCK_ANNOTATIONS || {};
    const style = document.createElement("style");
    style.textContent = `
      .mk-ann{position:absolute;z-index:2147483646;pointer-events:none;outline:1.5px dashed #e5484d;outline-offset:-1px}
      .mk-tag{position:absolute;z-index:2147483647;font:600 11px/1.2 system-ui,sans-serif;background:#e5484d;color:#fff;
        padding:2px 5px;border-radius:4px;cursor:pointer;white-space:nowrap}
      .mk-tag[data-kind="rule"]{background:#3e63dd}
      .mk-pop{position:fixed;z-index:2147483647;right:12px;bottom:12px;max-width:min(420px,calc(100vw - 24px));max-height:60vh;overflow:auto;
        background:#fff;color:#111;border:1px solid #ccc;border-radius:8px;padding:12px;font:13px/1.6 system-ui,sans-serif;box-shadow:0 8px 24px rgb(0 0 0/.2)}
      .mk-pop h4{margin:0 0 4px;font-size:13px}.mk-pop dl{margin:0 0 8px}.mk-pop dt{font-weight:600;color:#555}.mk-pop dd{margin:0 0 4px}`;
    document.head.appendChild(style);
    const layer = document.createElement("div");
    document.body.appendChild(layer);
    const pop = document.createElement("div");
    pop.className = "mk-pop";
    pop.hidden = true;
    document.body.appendChild(pop);

    const describe = (id) => {
      const n = notes[id];
      if (!n) return `<h4>${id}</h4><p>定義が見つかりません（文書を確認）</p>`;
      const rows = Object.entries(n.cells).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
      return `<h4>${id}（${n.source}）</h4><dl>${rows}</dl>`;
    };
    const show = (ids) => {
      pop.innerHTML = ids.map(describe).join("") + '<button type="button">閉じる</button>';
      pop.querySelector("button").onclick = () => (pop.hidden = true);
      pop.hidden = false;
    };
    let placed = [];
    const draw = () => {
      layer.innerHTML = "";
      placed = [];
      document.querySelectorAll("[data-ui],[data-rules]").forEach((el) => {
        if (el === document.body || el.closest("[hidden]")) return;
        const r = el.getBoundingClientRect();
        if (!r.width && !r.height) return;
        const x = r.left + scrollX, y = r.top + scrollY;
        const box = document.createElement("div");
        box.className = "mk-ann";
        Object.assign(box.style, { left: x + "px", top: y + "px", width: r.width + "px", height: r.height + "px" });
        layer.appendChild(box);
        const ui = el.getAttribute("data-ui");
        const rules = (el.getAttribute("data-rules") || "").split(/\s+/).filter(Boolean);
        let tx = x, ty = y;
        [ui, ...rules].filter(Boolean).forEach((id) => {
          const tag = document.createElement("span");
          tag.className = "mk-tag";
          tag.dataset.kind = id.startsWith("UI-") ? "rule" : "ui";
          tag.textContent = id;
          tag.title = "クリックで定義を表示";
          layer.appendChild(tag);
          const w = tag.offsetWidth + 4, h = tag.offsetHeight + 2;
          // 他のタグと重なる場合は下にずらす
          while (placed.some((p) => tx < p.x + p.w && tx + w > p.x && ty < p.y + p.h && ty + h > p.y)) ty += h;
          Object.assign(tag.style, { left: tx + "px", top: ty + "px" });
          placed.push({ x: tx, y: ty, w, h });
          tag.onclick = () => show(notes[id] || !id.includes("/") ? [id] : [id, id.split("/")[0]]);
          tx += w;
        });
      });
    };
    draw();
    addEventListener("resize", draw);
  }

  window.MockKit = { defineComponent, registry, state, platform };

  document.addEventListener("DOMContentLoaded", () => {
    applyVisibility();
    keepParams();
    if (annotate) requestAnimationFrame(annotateLayer);
    const declared = (document.body.dataset.states || "default").split(/\s+/);
    if (!declared.includes(state)) console.warn(`[mock] この画面は状態 "${state}" を宣言していません`, declared);
  });
})();
