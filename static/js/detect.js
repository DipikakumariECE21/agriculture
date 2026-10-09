/* Scanner page: file / drag-drop / sample input -> POST /api/analyze -> render result. */
(() => {
  const root = document.querySelector("[data-scanner]");
  if (!root) return;

  const endpoint = root.dataset.endpoint;
  const drop = root.querySelector("[data-drop]");
  const fileInput = root.querySelector("[data-file]");
  const samples = [...root.querySelectorAll("[data-sample]")];
  const states = Object.fromEntries([...root.querySelectorAll("[data-state]")].map((el) => [el.dataset.state, el]));
  const preview = root.querySelector("[data-preview]");
  const steps = [...root.querySelectorAll("[data-steps] li")];
  const $ = (sel) => root.querySelector(sel);

  const MAX_BYTES = 10 * 1024 * 1024;
  const OK_TYPES = ["image/jpeg", "image/png", "image/webp"];
  let busy = false;
  let stepTimer = null;

  function show(name) {
    for (const [key, el] of Object.entries(states)) el.classList.toggle("is-visible", key === name);
  }

  function setBusy(on) {
    busy = on;
    drop.classList.toggle("is-busy", on);
    samples.forEach((b) => (b.disabled = on));
  }

  function runSteps() {
    let i = 0;
    steps.forEach((s) => s.classList.remove("is-on", "is-done"));
    steps[0].classList.add("is-on");
    stepTimer = setInterval(() => {
      if (i < steps.length - 1) {
        steps[i].classList.replace("is-on", "is-done");
        i++;
        steps[i].classList.add("is-on");
      }
    }, 260);
  }

  function finishSteps() {
    clearInterval(stepTimer);
    steps.forEach((s) => { s.classList.remove("is-on"); s.classList.add("is-done"); });
  }

  function fail(message) {
    clearInterval(stepTimer);
    $("[data-error]").textContent = message;
    show("error");
    setBusy(false);
  }

  async function analyse(file, name) {
    if (busy) return;
    if (!OK_TYPES.includes(file.type)) return fail("Use a JPG, PNG or WebP photo of a leaf.");
    if (file.size > MAX_BYTES) return fail("That photo is larger than 10 MB. Resize it and try again.");

    setBusy(true);
    const url = URL.createObjectURL(file);
    preview.src = url;
    show("loading");
    runSteps();
    root.scrollIntoView({ behavior: "smooth", block: "start" });

    const body = new FormData();
    body.append("image", file, name || file.name || "leaf.jpg");
    const started = performance.now();
    try {
      const res = await fetch(endpoint, { method: "POST", body });
      const data = await res.json().catch(() => ({ error: "The server returned an unreadable response." }));
      // let the step animation complete so the pipeline is legible
      const wait = Math.max(0, 1400 - (performance.now() - started));
      await new Promise((r) => setTimeout(r, wait));
      if (!res.ok || data.error) return fail(data.error || `Analysis failed (HTTP ${res.status}).`);
      finishSteps();
      render(data);
    } catch {
      fail("Couldn't reach the analysis server. Check that app.py is running and try again.");
    } finally {
      URL.revokeObjectURL(url);
      setBusy(false);
    }
  }

  const FEATURE_LABELS = [
    ["leaf_coverage", "Leaf in frame", "%"],
    ["lesion_area", "Lesion area", "%"],
    ["spot_count", "Spots counted", ""],
    ["largest_spot", "Largest spot", "%"],
    ["brown_ratio", "Brown / necrotic", "%"],
    ["yellow_ratio", "Chlorotic (yellow)", "%"],
    ["sharpness", "Sharpness", ""],
    ["brightness", "Brightness", "/255"],
    ["resolution", "Analysed at", "px"],
  ];

  function render(d) {
    const card = states.result;
    card.classList.toggle("is-healthy", d.slug === "healthy");
    card.classList.toggle("is-unsupported", d.status !== "ok");

    const orig = $("[data-r-original]");
    const over = $("[data-r-overlay]");
    orig.src = d.original;
    over.src = d.overlay;
    orig.onload = () => $("[data-compare]").style.setProperty("--ar", `${orig.naturalWidth} / ${orig.naturalHeight}`);
    setCompare(55);

    $("[data-r-label]").textContent = d.label;
    $("[data-r-type]").textContent = d.advice ? `${d.advice.type} · Result` : "Result";
    $("[data-r-pathogen]").textContent = d.advice ? d.advice.pathogen : "";
    countUp($("[data-r-conf]"), d.confidence);
    $(".verdict__conf .mono").textContent = d.adjusted ? "confidence · lowered for photo quality" : "confidence";

    const sevWrap = $("[data-r-sev-wrap]");
    sevWrap.hidden = d.status !== "ok";
    $("[data-r-sev]").textContent = d.severity.toFixed(1);
    $("[data-r-sev-band]").textContent = d.severity_band;
    // severity scale is non-linear: 0–1.5 none, 1.5–6 low, 6–18 moderate, 18+ high
    const sevPos = d.severity <= 6 ? (d.severity / 6) * 18 : d.severity <= 18 ? 18 + ((d.severity - 6) / 12) * 40 : Math.min(100, 58 + (d.severity - 18) * 1.2);
    const sevBar = $("[data-r-sev-bar]");
    sevBar.style.transform = "scaleX(1)";
    const remaining = 1 - Math.max(sevPos, 1.5) / 100;
    requestAnimationFrame(() => requestAnimationFrame(() => (sevBar.style.transform = `scaleX(${remaining})`)));

    const warn = $("[data-r-warnings]");
    warn.replaceChildren(...d.warnings.map((w) => Object.assign(document.createElement("p"), { className: "warning", textContent: w })));
    warn.hidden = d.warnings.length === 0;

    const probs = $("[data-r-probs]");
    probs.replaceChildren(...d.probabilities.map((p) => {
      const li = document.createElement("li");
      li.innerHTML = `<span></span><span>${p.p.toFixed(1)}%</span><span class="bar"><b></b></span>`;
      li.firstChild.textContent = p.label;
      return li;
    }));
    requestAnimationFrame(() => requestAnimationFrame(() => {
      probs.querySelectorAll(".bar b").forEach((b, i) => (b.style.transform = `scaleX(${d.probabilities[i].p / 100})`));
    }));
    probs.closest("section").hidden = d.probabilities.length === 0;

    const feats = $("[data-r-feats]");
    feats.replaceChildren(...FEATURE_LABELS.flatMap(([key, label, unit]) => {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = `${d.features[key]}${unit}`;
      return [dt, dd];
    }));

    const advice = $("[data-r-advice]");
    if (d.advice) {
      $("[data-r-summary]").textContent = d.advice.summary;
      $("[data-r-steps]").replaceChildren(...d.advice.steps.map((s) => Object.assign(document.createElement("li"), { textContent: s })));
      $("[data-r-link]").href = d.advice.url;
      advice.hidden = false;
    } else {
      advice.hidden = true;
    }

    $("[data-r-id]").textContent = `Scan #${String(d.scan_id).padStart(4, "0")} · saved to log`;
    show("result");
  }

  function countUp(el, value) {
    const start = performance.now();
    const dur = 900;
    const step = (now) => {
      const t = Math.min(1, (now - start) / dur);
      el.textContent = Math.round(value * (1 - Math.pow(1 - t, 3)));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // ---- before / after compare
  const compare = $("[data-compare]");
  const range = $("[data-compare-range]");
  function setCompare(v) {
    range.value = v;
    compare.style.setProperty("--pos", `${v}%`);
  }
  range.addEventListener("input", () => setCompare(range.value));

  // ---- inputs
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) analyse(file);
    fileInput.value = "";
  });

  ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("is-over"); }));
  ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("is-over"); }));
  drop.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) analyse(file);
  });
  drop.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
  });
  drop.tabIndex = 0;

  samples.forEach((btn) => btn.addEventListener("click", async () => {
    if (busy) return;
    try {
      const res = await fetch(btn.dataset.sample);
      const blob = await res.blob();
      analyse(new File([blob], btn.dataset.name, { type: blob.type || "image/jpeg" }), btn.dataset.name);
    } catch {
      fail("Couldn't load the sample image.");
    }
  }));

  root.querySelectorAll("[data-reset]").forEach((b) => b.addEventListener("click", () => {
    show("idle");
    drop.focus();
  }));

  // paste an image from the clipboard
  window.addEventListener("paste", (e) => {
    const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
    if (item) analyse(item.getAsFile(), "pasted-leaf.png");
  });
})();
