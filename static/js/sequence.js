/* Scroll-driven frame sequence: maps page scroll inside [data-seq] to one of N frames
   drawn on a canvas with object-fit: cover behaviour. Frames load coarse-to-fine so the
   film is scrubbable within the first few hundred KB. */
(() => {
  const section = document.querySelector("[data-seq]");
  if (!section) return;

  const canvas = section.querySelector("[data-seq-canvas]");
  const ctx = canvas.getContext("2d", { alpha: false });
  const total = Number(section.dataset.frames) || 0;
  const base = section.dataset.src;
  const bar = section.querySelector("[data-seq-bar]");
  const counter = section.querySelector("[data-seq-frame]");
  const loader = section.querySelector("[data-seq-loader]");
  const pct = section.querySelector("[data-seq-pct]");
  const chapters = [...section.querySelectorAll("[data-chapter]")];
  const hudValues = [...section.querySelectorAll("[data-hud]")];
  const nav = document.querySelector("[data-nav]");
  if (!total) return;

  const frames = new Array(total);
  let loaded = 0;
  let target = 0;
  let current = 0;
  let drawn = -1;
  let progress = 0;
  let width = 0;
  let height = 0;

  const src = (i) => `${base}${String(i + 1).padStart(4, "0")}.webp`;

  function loadOrder() {
    const order = [];
    const seen = new Set();
    for (const step of [32, 16, 8, 4, 2, 1]) {
      for (let i = 0; i < total; i += step) {
        if (!seen.has(i)) { seen.add(i); order.push(i); }
      }
    }
    if (!seen.has(total - 1)) order.push(total - 1);
    return order;
  }

  function loadFrames() {
    const queue = loadOrder();
    let inFlight = 0;
    const MAX = 6;
    const pump = () => {
      while (inFlight < MAX && queue.length) {
        const i = queue.shift();
        const img = new Image();
        img.decoding = "async";
        inFlight++;
        img.onload = img.onerror = () => {
          inFlight--;
          if (img.naturalWidth) frames[i] = img;
          loaded++;
          if (pct) pct.textContent = Math.round((loaded / total) * 100);
          if (loaded >= total && loader) loader.classList.add("is-done");
          if (i === 0 || Math.abs(i - Math.round(current)) < 3) drawn = -1;
          pump();
        };
        img.src = src(i);
      }
    };
    pump();
  }

  function nearest(i) {
    if (frames[i]) return frames[i];
    for (let d = 1; d < total; d++) {
      if (frames[i - d]) return frames[i - d];
      if (frames[i + d]) return frames[i + d];
    }
    return null;
  }

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingQuality = "high";
    drawn = -1;
  }

  function draw(index) {
    const img = nearest(index);
    if (!img) return;
    const ir = img.naturalWidth / img.naturalHeight;
    const cr = width / height;
    let w, h;
    if (cr > ir) { w = width; h = width / ir; } else { h = height; w = height * ir; }
    const x = (width - w) / 2;
    const y = (height - h) / 2;
    ctx.drawImage(img, x, y, w, h);
  }

  function readScroll() {
    const rect = section.getBoundingClientRect();
    const span = section.offsetHeight - window.innerHeight;
    progress = Math.min(1, Math.max(0, -rect.top / span));
    target = progress * (total - 1);
    section.classList.toggle("is-past", rect.bottom < window.innerHeight * 1.2);
    if (nav) nav.classList.toggle("is-solid", rect.bottom <= 64);
  }

  function updateChapters() {
    for (const ch of chapters) {
      const from = Number(ch.dataset.from);
      const to = Number(ch.dataset.to);
      ch.classList.toggle("is-active", progress >= from && progress < to);
    }
    // HUD counters ease in across the scan chapter
    const t = Math.min(1, Math.max(0, (progress - 0.7) / 0.12));
    const eased = 1 - Math.pow(1 - t, 3);
    for (const el of hudValues) {
      const v = Number(el.dataset.hud) * eased;
      const isInt = el.hasAttribute("data-int");
      const unit = el.querySelector("span");
      const text = isInt ? String(Math.round(v)) : v.toFixed(1);
      if (unit) el.firstChild.nodeValue = text;
      else el.textContent = text;
    }
  }

  function tick() {
    const diff = target - current;
    current += Math.abs(diff) < 0.05 ? diff : diff * 0.16;
    const idx = Math.max(0, Math.min(total - 1, Math.round(current)));
    if (idx !== drawn) {
      draw(idx);
      drawn = idx;
      if (counter) counter.textContent = String(idx + 1).padStart(3, "0");
    }
    if (bar) bar.style.transform = `scaleX(${progress})`;
    requestAnimationFrame(tick);
  }

  window.addEventListener("scroll", () => { readScroll(); updateChapters(); }, { passive: true });
  window.addEventListener("resize", () => { resize(); readScroll(); });

  resize();
  readScroll();
  updateChapters();
  current = target;
  loadFrames();
  requestAnimationFrame(tick);
})();
