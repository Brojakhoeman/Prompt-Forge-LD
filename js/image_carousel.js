/**
 * Coverflow image carousel — wheel scroll, center card scales up.
 */
const SLOTS = [-2, -1, 0, 1, 2];
// Slightly larger base cards + tuned spread so the coverflow uses wider space better
// (the res+carousel row now allocates more breathing room on the carousel side).
const BASE_W = 132;
const BASE_H = 178;
const WHEEL_MS = 140;

const NO_IMAGE_NAME = "__NO_IMAGE__";

export function buildImageCarousel(opts) {
  const o = opts || {};
  const mount = o.mount;
  if (!mount) throw new Error("buildImageCarousel: mount required");

  const onSelect = typeof o.onSelect === "function" ? o.onSelect : () => {};
  const onPickImage = o.onPickImage;
  const onOpenFolder = o.onOpenFolder;
  const onDropFile = o.onDropFile;
  const viewUrl = o.viewUrl || ((n) => n);

  let images = [];
  let focus = 0;
  let wheelLock = false;
  let _destroyed = false;
  let customImageUrls = {};  // for manually selected images not in the gallery list

  const wrap = document.createElement("div");
  wrap.className = "gpl-carousel-zone";

  const upload = document.createElement("div");
  upload.className = "gpl-upload-card";
  upload.title = "Click to browse · folder icon for folder";
  upload.innerHTML = `
    <span class="gpl-upload-plus">+</span>
    <span class="gpl-upload-lbl">Browse</span>
    <button type="button" class="gpl-upload-folder" title="Set image folder">📁</button>`;
  upload.addEventListener("click", (e) => {
    if (e.target.closest(".gpl-upload-folder")) return;
    onPickImage?.();
  });
  upload.querySelector(".gpl-upload-folder")?.addEventListener("click", (e) => {
    e.stopPropagation();
    onOpenFolder?.();
  });

  const viewport = document.createElement("div");
  viewport.className = "gpl-carousel-viewport";
  const track = document.createElement("div");
  track.className = "gpl-carousel-track";
  const empty = document.createElement("div");
  empty.className = "gpl-carousel-empty";
  empty.textContent = "Scroll wheel · pick a card";
  viewport.appendChild(track);
  viewport.appendChild(empty);
  wrap.appendChild(upload);
  wrap.appendChild(viewport);
  mount.appendChild(wrap);

  const cardEls = new Map();

  function bindDrop(el) {
    el.ondragover = (e) => e.preventDefault();
    el.ondrop = (e) => {
      e.preventDefault();
      const f = e.dataTransfer?.files?.[0];
      if (f?.type?.startsWith("image/") && onDropFile) onDropFile(f);
    };
  }
  bindDrop(upload);
  bindDrop(viewport);

  function ensureCard(name) {
    const isNoImage = name === NO_IMAGE_NAME;
    let el = isNoImage ? null : cardEls.get(name);
    if (el) return el;

    el = document.createElement("div");
    el.className = "gpl-carousel-card";
    el.dataset.name = name;

    if (isNoImage) {
      el.classList.add("no-image");
      const placeholder = document.createElement("div");
      placeholder.style.cssText = "width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0a0612;border:2px dashed #444;color:#888;font:600 9px 'JetBrains Mono',monospace;text-align:center;line-height:1.2;";
      placeholder.innerHTML = `No image<br><span style="font-size:7px;opacity:.7;">(black frame)</span>`;
      el.appendChild(placeholder);
    } else {
      const im = document.createElement("img");
      im.src = customImageUrls[name] || viewUrl(name);
      im.alt = name;
      im.loading = "lazy";
      el.appendChild(im);
    }

    el.addEventListener("click", () => {
      if (isNoImage) {
        onSelect(NO_IMAGE_NAME);
      } else {
        focusTo(images.indexOf(name), true);
      }
    });
    track.appendChild(el);
    if (!isNoImage) cardEls.set(name, el);
    return el;
  }

  function pruneCards() {
    for (const [name, el] of cardEls) {
      if (name === NO_IMAGE_NAME) continue;
      if (!images.includes(name)) {
        el.remove();
        cardEls.delete(name);
      }
    }
  }

  function cardScale() {
    const vh = viewport.clientHeight || 200;
    return Math.max(1, Math.min(1.5, vh / 200));
  }

  function layout() {
    if (_destroyed) return;

    // clean stale no-image cards (to support duplicates at start + end)
    track.querySelectorAll(`.gpl-carousel-card[data-name="${NO_IMAGE_NAME}"]`).forEach(e => e.remove());

    const vw = viewport.clientWidth || 280;
    const vh = viewport.clientHeight || 200;
    const cx = vw / 2;
    const cy = vh / 2;
    const mul = cardScale();
    empty.style.display = images.length ? "none" : "flex";

    const visible = new Set();
    for (const slot of SLOTS) {
      const idx = focus + slot;
      if (idx < 0 || idx >= images.length) continue;
      visible.add(images[idx]);
    }

    for (const [name, el] of cardEls) {
      if (!visible.has(name)) {
        el.style.opacity = "0";
        el.style.pointerEvents = "none";
        el.style.visibility = "hidden";
      }
    }

    for (const slot of SLOTS) {
      const idx = focus + slot;
      if (idx < 0 || idx >= images.length) continue;
      const name = images[idx];
      const el = ensureCard(name);
      const d = slot;
      const scale = Math.max(0.52, 1 - Math.abs(d) * 0.19);
      const w = BASE_W * scale * mul;
      const h = BASE_H * scale * mul;
      // Slightly gentler side spread on wider viewports for visual evenness around center card
      const spread = (BASE_W * 0.66 + Math.abs(d) * 11) * mul;
      const x = cx + d * spread - w / 2;
      const y = cy - h / 2;
      const z = 10 - Math.abs(d);
      el.style.width = `${Math.round(w)}px`;
      el.style.height = `${Math.round(h)}px`;
      el.style.left = `${Math.round(x)}px`;
      el.style.top = `${Math.round(y)}px`;
      el.style.zIndex = String(z);
      el.style.opacity = String(Math.max(0.35, 1 - Math.abs(d) * 0.22));
      el.style.transform = `perspective(600px) rotateY(${d * -14}deg) scale(1)`;
      el.style.pointerEvents = "auto";
      el.style.visibility = "visible";
      el.classList.toggle("center", d === 0);
    }
  }

  function focusTo(idx, fireSelect) {
    if (!images.length) return;
    focus = Math.max(0, Math.min(images.length - 1, idx));
    layout();
    if (fireSelect) onSelect(images[focus]);
  }

  function step(dir) {
    if (!images.length) return;
    focusTo(focus + dir, true);
  }

  viewport.addEventListener("wheel", (e) => {
    e.preventDefault();
    if (wheelLock || !images.length) return;
    wheelLock = true;
    setTimeout(() => { wheelLock = false; }, WHEEL_MS);
    step(e.deltaY > 0 ? 1 : -1);
  }, { passive: false });

  let _ro = null;
  if (typeof ResizeObserver !== "undefined") {
    _ro = new ResizeObserver(() => layout());
    _ro.observe(viewport);
  }

  function setImages(list, selectedName) {
    const currentCustom = customImageUrls[selectedName] || (focus < images.length && customImageUrls[images[focus]] ? customImageUrls[images[focus]] : null);
    images = Array.isArray(list) ? list.slice() : [];

    // clean previous no-image cards (to support dups at start+end)
    track.querySelectorAll(`.gpl-carousel-card[data-name="${NO_IMAGE_NAME}"]`).forEach(e => e.remove());

    pruneCards();
    customImageUrls = {};
    if (selectedName && currentCustom) {
      customImageUrls[selectedName] = currentCustom;
      if (!images.includes(selectedName)) {
        const insertPos = Math.max(0, Math.min(images.length, focus + 1));
        images.splice(insertPos, 0, selectedName);
      }
    }

    // Prefer "No image" if no selection (especially for T2V default)
    if (selectedName && images.includes(selectedName)) {
      focus = images.indexOf(selectedName);
    } else if (images.includes(NO_IMAGE_NAME)) {
      focus = images.indexOf(NO_IMAGE_NAME);
    } else if (focus >= images.length || focus < 0) {
      focus = Math.max(0, images.length - 1);
    }
    layout();
  }

  function setFocus(name, fireSelect = false) {
    if (!name) return;
    if (name === NO_IMAGE_NAME) {
      const idx = images.indexOf(NO_IMAGE_NAME);
      if (idx >= 0) {
        focusTo(idx, fireSelect);
        return;
      }
    }
    if (customImageUrls[name]) {
      if (!images.includes(name)) images.push(name);
      focusTo(images.indexOf(name), fireSelect);
      return;
    }
    if (!images.includes(name)) return;
    focusTo(images.indexOf(name), fireSelect);
  }

  function setCustomImage(name, dataUrl) {
    if (!name || !dataUrl || name === NO_IMAGE_NAME) return;
    customImageUrls[name] = dataUrl;
    if (!images.includes(name)) {
      // Insert near current focus so it becomes the middle card
      const insertPos = Math.max(0, Math.min(images.length, focus + 1));
      images.splice(insertPos, 0, name);
    }
    focusTo(images.indexOf(name), false);
  }

  function resync() { layout(); }

  function destroy() {
    _destroyed = true;
    _ro?.disconnect();
    wrap.remove();
    cardEls.clear();
  }

  layout();
  return { setImages, setFocus, setCustomImage, resync, destroy, el: wrap };
}