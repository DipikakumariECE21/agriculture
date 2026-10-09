/* Site-wide behaviour: mobile menu, reveal-on-scroll, library filtering, confirm forms. */
(() => {
  // ---- mobile menu
  const toggle = document.querySelector("[data-menu-toggle]");
  const menu = document.querySelector("[data-menu]");
  const nav = document.querySelector("[data-nav]");
  if (toggle && menu) {
    const setOpen = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      menu.classList.toggle("is-open", open);
      nav.classList.toggle("menu-open", open);
    };
    toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
    menu.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
  }

  // ---- reveal on scroll
  const revealTargets = document.querySelectorAll(
    ".section__head, .figure, .rail__step, .spec li, .row, .dcard, .method li, .roadmap li, .deploy > div, .flow li, .mgmt__col, .numbered li"
  );
  if ("IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const el = entry.target;
          el.classList.add("is-in");
          io.unobserve(el);
          // hand transform/transition back to the component's own hover states
          setTimeout(() => { el.removeAttribute("data-reveal"); el.classList.remove("is-in"); }, 1400);
        }
      }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealTargets.forEach((el) => {
      const siblings = [...el.parentElement.children];
      el.style.setProperty("--i", String(Math.min(siblings.indexOf(el), 6)));
      el.setAttribute("data-reveal", "");
      io.observe(el);
    });
  }

  // ---- disease library filter + search
  const library = document.querySelector("[data-library]");
  if (library) {
    const chips = [...library.querySelectorAll("[data-filter]")];
    const cards = [...library.querySelectorAll(".dcard")];
    const search = library.querySelector("[data-search]");
    const empty = library.querySelector("[data-empty]");
    let filter = "all";
    const apply = () => {
      const q = (search.value || "").trim().toLowerCase();
      let shown = 0;
      for (const card of cards) {
        const okType = filter === "all" || card.dataset.type === filter;
        const okText = !q || card.dataset.text.includes(q);
        const visible = okType && okText;
        card.classList.toggle("is-hidden", !visible);
        if (visible) shown++;
      }
      empty.hidden = shown > 0;
    };
    chips.forEach((chip) => chip.addEventListener("click", () => {
      filter = chip.dataset.filter;
      chips.forEach((c) => {
        const on = c === chip;
        c.classList.toggle("is-on", on);
        c.setAttribute("aria-pressed", String(on));
      });
      apply();
    }));
    search.addEventListener("input", apply);
  }

  // ---- confirm destructive forms
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
})();
