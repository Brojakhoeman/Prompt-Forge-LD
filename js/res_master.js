/**
 * ResMaster LD — classic row layout or hero (image + bbox overlay).
 */
const MP_UNIT = 1024 * 1024;

function mpOf(w, h) { return (w * h) / MP_UNIT; }
function rGrid(n, g) { return Math.max(g, Math.round(n / g) * g); }

function dimsForMP(aspectWH, targetMP, grid) {
  grid = grid || 32;
  const h = Math.sqrt((targetMP * MP_UNIT) / aspectWH);
  const w = h * aspectWH;
  return [rGrid(w, grid), rGrid(h, grid)];
}

function ratioLabel(w, h) {
  const g = (a, b) => (b ? g(b, a % b) : a);
  const d = g(w, h) || 1;
  let rw = Math.round(w / d), rh = Math.round(h / d);
  if (rw > 32 || rh > 32) {
    const f = w / h;
    const commons = [[1, 1], [4, 3], [3, 2], [16, 9], [9, 16], [2, 3], [3, 4], [4, 5]];
    let best = null, bestErr = 1e9;
    for (const [a, b] of commons) {
      const e = Math.abs(a / b - f);
      if (e < bestErr) { bestErr = e; best = [a, b]; }
    }
    if (bestErr < 0.04) return `${best[0]}:${best[1]}`;
    return `${f.toFixed(2)}:1`;
  }
  return `${rw}:${rh}`;
}

export const LTX_AR_PRESETS = [
  ["1:1", 1, 1, "Square", 768, 768],
  ["4:3", 4, 3, "Landscape", 960, 720],
  ["16:9", 16, 9, "Wide", 1280, 720],
  ["9:16", 9, 16, "Portrait", 720, 1280],
  ["2:3", 2, 3, "Photo", 704, 1056],
  ["4:5", 4, 5, "IG", 864, 1088],
];

export function buildResMaster(opts) {
  const o = opts || {};
  if (o.layout === "hero") return _buildHero(o);
  return _buildClassic(o);
}

function _buildHero(o) {
  const mount = o.mount;
  if (!mount) throw new Error("buildResMaster: mount required");

  let imageW = o.imageW || null;
  let imageH = o.imageH || null;
  let aspectLocked = !!o.aspectLocked || !!imageW;
  let mp = typeof o.mp === "number" ? o.mp : 1.0;
  const snapGrid = o.snapGrid || null;
  const gridUnit = o.gridUnit || 32;
  const onChange = typeof o.onChange === "function" ? o.onChange : () => {};
  let imageUrl = o.imageUrl || null;
  const onPickImage = o.onPickImage;
  const onClearImage = o.onClearImage;
  const onDropFile = o.onDropFile;
  const onOpenFolder = o.onOpenFolder;
  const arPresets = o.arPresets || LTX_AR_PRESETS;
  const lockAspectOnImage = o.lockAspectOnImage !== false;

  let aspectW = imageW || o.aspectW || 9;
  let aspectH = imageH || o.aspectH || 16;
  let snappedDims = null;

  // Support for moving the bbox placement (offset from centered).
  // Stored as pixels *at a reference overlay size*, then applied proportionally
  // so the placement stays put regardless of graph zoom level.
  let boxOffsetX = o.boxOffsetX || 0;
  let boxOffsetY = o.boxOffsetY || 0;
  const MP_MIN = 0.25, MP_MAX = 4.0;
  const VISUAL_MP_FULL = 3.0;

  function nativeMP() { return imageW ? mpOf(imageW, imageH) : null; }
  function currentDims() {
    if (snappedDims) return snappedDims;
    return dimsForMP(aspectW / aspectH, mp, gridUnit);
  }
  function isUpscale() {
    if (!imageW) return false;
    const [w, h] = currentDims();
    return (w * h) > (imageW * imageH) * 1.02;
  }
  function isFreeAspect() {
    if (!imageW) return false;
    return Math.abs(aspectW / aspectH - imageW / imageH) > 0.02;
  }
  function emit() {
    const [w, h] = currentDims();
    onChange({ w, h, mp: mpOf(w, h), aspectW, aspectH, upscale: isUpscale(), freeAspect: isFreeAspect(), hasImage: !!imageW });
  }

  const root = document.createElement("div");
  root.className = "gpl-rm-hero";

  const stage = document.createElement("div");
  stage.className = "gpl-rm-hero-stage";
  const overlay = document.createElement("div");
  overlay.className = "gpl-rm-hero-overlay";
  const boxEl = document.createElement("div");
  boxEl.className = "gpl-rm-box";
  const handleHit = document.createElement("div");
  handleHit.className = "gpl-rm-hit";
  const handle = document.createElement("div");
  handle.className = "gpl-rm-handle";
  handleHit.appendChild(handle);
  boxEl.appendChild(handleHit);
  overlay.appendChild(boxEl);
  stage.appendChild(overlay);

  const ctrl = document.createElement("div");
  ctrl.className = "gpl-rm-hero-ctrl";

  const mpLbl = document.createElement("div");
  mpLbl.className = "gpl-rm-mplbl";
  const mpSlider = document.createElement("input");
  mpSlider.type = "range";
  mpSlider.min = String(MP_MIN);
  mpSlider.max = String(MP_MAX);
  mpSlider.step = "0.05";
  mpSlider.value = String(mp);
  mpSlider.className = "gpl-rm-slider";

  const arRow = document.createElement("div");
  arRow.className = "gpl-rm-ar";
  const arBtns = [];
  arPresets.forEach(([lab, aw, ah, , snapW, snapH]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = lab;
    b.className = "gpl-rm-arbtn";
    b.onclick = () => {
      if (aspectLocked && imageW) return;
      aspectW = aw; aspectH = ah;
      snappedDims = null;
      if (snapGrid?.[`${aw}:${ah}`]) {
        const [cw, ch] = snapGrid[`${aw}:${ah}`];
        snappedDims = [cw, ch];
        mp = mpOf(cw, ch);
        mpSlider.value = String(Math.min(MP_MAX, mp));
      } else if (snapW && snapH) {
        snappedDims = [snapW, snapH];
        mp = mpOf(snapW, snapH);
        mpSlider.value = String(Math.min(MP_MAX, mp));
      }
      syncBox(); emit();
    };
    arBtns.push(b);
    arRow.appendChild(b);
  });

  const snapBtn = document.createElement("button");
  snapBtn.type = "button";
  snapBtn.className = "gpl-rm-snap";
  snapBtn.textContent = "↩ Snap native";
  snapBtn.onclick = () => snapNative();

  const dimsRow = document.createElement("div");
  dimsRow.className = "gpl-rm-dims";
  const dimEl = document.createElement("div");
  dimEl.className = "gpl-rm-read";
  const mpEl = document.createElement("div");
  mpEl.className = "gpl-rm-mpread";
  const arEl = document.createElement("div");
  arEl.className = "gpl-rm-arread";
  dimsRow.appendChild(dimEl);
  dimsRow.appendChild(mpEl);
  dimsRow.appendChild(arEl);
  const flagEl = document.createElement("div");
  flagEl.className = "gpl-rm-flag";

  ctrl.appendChild(mpLbl);
  ctrl.appendChild(mpSlider);
  ctrl.appendChild(snapBtn);
  ctrl.appendChild(arRow);
  ctrl.appendChild(dimsRow);
  ctrl.appendChild(flagEl);

  const nativeLbl = document.createElement("div");
  nativeLbl.className = "gpl-rm-hero-native";
  ctrl.appendChild(nativeLbl);

  root.appendChild(stage);
  root.appendChild(ctrl);
  mount.appendChild(root);

  function paintImage() {
    nativeLbl.textContent = imageW
      ? `${imageW}×${imageH} · ${nativeMP()?.toFixed(2)} MP native`
      : "Scroll cards or + upload";
  }

  stage.ondragover = (e) => e.preventDefault();
  stage.ondrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f?.type?.startsWith("image/") && onDropFile) onDropFile(f);
  };
  // Support click to browse for reference image (useful in T2V)
  if (onPickImage) {
    stage.style.cursor = 'pointer';
    stage.onclick = (e) => {
      if (e.target.closest('.gpl-rm-box')) return; // don't interfere with drag handle
      onPickImage();
    };
  }

  function syncBox() {
    // Use layout size (clientWidth/Height), NOT getBoundingClientRect():
    // the latter returns zoom-SCALED pixels because ComfyUI applies a CSS
    // transform to DOM widgets. Sizing the box from scaled dims caused the
    // box to drift as you zoomed. clientWidth is the pre-transform CSS size,
    // so the box scales exactly once (with its parent) and stays put.
    const SW = overlay.clientWidth || 200;
    const SH = overlay.clientHeight || 280;
    const ar = aspectW / aspectH;
    const pad = 6;
    const availW = Math.max(20, SW - pad * 2);
    const availH = Math.max(20, SH - pad * 2);
    const sizeFrac = Math.max(0.35, Math.min(1, Math.sqrt(mp / VISUAL_MP_FULL)));
    let bw, bh;
    if (availW / availH >= ar) { bh = availH * sizeFrac; bw = bh * ar; }
    else { bw = availW * sizeFrac; bh = bw / ar; }
    if (bw > availW) { bw = availW; bh = bw / ar; }
    if (bh > availH) { bh = availH; bw = bh * ar; }
    boxEl.style.width = `${Math.round(bw)}px`;
    boxEl.style.height = `${Math.round(bh)}px`;
    // Offset is plain CSS px in the stage's own (pre-transform) space, so it is
    // zoom-independent by construction — no scale correction needed.
    boxEl.style.left = `${(SW - bw) / 2 + boxOffsetX}px`;
    boxEl.style.top = `${(SH - bh) / 2 + boxOffsetY}px`;

    const [w, h] = currentDims();
    dimEl.textContent = `LTX ${w}×${h}`;
    mpEl.textContent = `${mpOf(w, h).toFixed(2)} MP`;
    arEl.textContent = ratioLabel(w, h);
    mpLbl.textContent = `Target ${mp.toFixed(2)} MP`;
    arBtns.forEach((b) => { b.style.opacity = (aspectLocked && imageW) ? "0.45" : "1"; });
    snapBtn.style.display = imageW ? "block" : "none";
    if (isFreeAspect()) flagEl.textContent = "⚠ free aspect";
    else if (isUpscale()) flagEl.textContent = "↑ upscale";
    else if (imageW && Math.abs(mp - nativeMP()) < 0.02) flagEl.textContent = "● native";
    else flagEl.textContent = "";
  }

  let dragging = false;
  function stagePos(e) {
    // Mouse in the overlay's LAYOUT space (pre-transform CSS px), so it matches
    // the box sizing in syncBox regardless of zoom. Screen delta / zoom scale.
    const r = overlay.getBoundingClientRect();
    const scale = (window.app?.canvas?.ds?.scale) || 1;
    const p = e.touches ? e.touches[0] : e;
    return { x: (p.clientX - r.left) / scale, y: (p.clientY - r.top) / scale };
  }
  function snapMP(val) {
    const marks = [];
    const nm = nativeMP();
    if (nm) marks.push(nm);
    marks.push(0.5, 1, 1.5, 2, 2.5, 3);
    let best = val, bestD = 0.06;
    for (const m of marks) {
      const d = Math.abs(val - m);
      if (d < bestD) { bestD = d; best = m; }
    }
    return best;
  }
  function onDown(e) { dragging = true; e.preventDefault(); e.stopPropagation(); }
  function onMove(e) {
    if (_destroyed || !dragging) return;
    e.preventDefault();
    const m = stagePos(e);
    // Work entirely in layout space (clientWidth), matching stagePos above.
    const SW = overlay.clientWidth || 200;
    const SH = overlay.clientHeight || 280;
    const cx = SW / 2, cy = SH / 2;
    let bw = Math.max(8, (m.x - cx) * 2);
    let bh = Math.max(8, (m.y - cy) * 2);
    const padClamp = 6;
    const availWClamp = Math.max(20, SW - padClamp * 2);
    const availHClamp = Math.max(20, SH - padClamp * 2);
    if (bw > availWClamp) bw = availWClamp;
    if (bh > availHClamp) bh = availHClamp;
    if (aspectLocked && imageW) {
      const ar = aspectW / aspectH;
      if (bw / ar >= bh) bh = bw / ar; else bw = bh * ar;
    } else {
      aspectW = bw; aspectH = bh;
    }
    snappedDims = null;
    const ar = aspectW / aspectH;
    let fitW, fitH;
    if (availWClamp / availHClamp >= ar) { fitH = availHClamp; fitW = fitH * ar; }
    else { fitW = availWClamp; fitH = fitW / ar; }
    const sizeFrac = Math.max(0.001, Math.min(1, (bh / fitH + bw / fitW) / 2));
    mp = snapMP(Math.max(MP_MIN, Math.min(MP_MAX, sizeFrac * sizeFrac * MP_MAX)));
    mpSlider.value = String(mp);
    syncBox(); emit();
  }
  function onUp() { dragging = false; }

  handleHit.addEventListener("mousedown", onDown);
  handleHit.addEventListener("touchstart", onDown, { passive: false });
  window.addEventListener("mousemove", onMove);
  window.addEventListener("touchmove", onMove, { passive: false });
  window.addEventListener("mouseup", onUp);
  window.addEventListener("touchend", onUp);

  mpSlider.addEventListener("input", () => {
    snappedDims = null;
    mp = snapMP(parseFloat(mpSlider.value));
    syncBox(); emit();
  });

  function snapNative() {
    if (!imageW) return;
    aspectLocked = true;
    aspectW = imageW; aspectH = imageH;
    mp = nativeMP();
    mpSlider.value = String(Math.min(MP_MAX, mp));
    snappedDims = null;
    syncBox(); emit();
  }

  function setImage(w, h, url) {
    imageW = w; imageH = h;
    if (url !== undefined) imageUrl = url;
    if (lockAspectOnImage) {
      snapNative();
    } else {
      // T2V reference image: set starting aspect but keep free shape for any bbox
      aspectW = imageW;
      aspectH = imageH;
      mp = nativeMP() || mp;
      mpSlider.value = String(Math.min(MP_MAX, mp));
      // do not force aspectLocked
    }
    paintImage();
  }
  function clearImage() {
    imageW = null; imageH = null; aspectLocked = false;
    imageUrl = null; paintImage(); syncBox(); emit();
  }
  function getState() {
    const [w, h] = currentDims();
    return { w, h, mp: mpOf(w, h), aspectW, aspectH, upscale: isUpscale(), freeAspect: isFreeAspect(), hasImage: !!imageW };
  }

  let _destroyed = false;
  let _ro = null;
  if (typeof ResizeObserver !== "undefined") {
    _ro = new ResizeObserver(() => { if (!_destroyed) syncBox(); });
    _ro.observe(root);
    _ro.observe(stage);
  }
  function resync() { if (!_destroyed) syncBox(); }

  function setBoxOffset(x, y) {
    boxOffsetX = Number(x) || 0;
    boxOffsetY = Number(y) || 0;
    if (!_destroyed) syncBox();
  }

  function destroy() {
    _destroyed = true;
    _ro?.disconnect();
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("touchmove", onMove);
    window.removeEventListener("mouseup", onUp);
    window.removeEventListener("touchend", onUp);
    root.remove();
  }

  paintImage();
  syncBox();
  emit();
  requestAnimationFrame(() => { if (!_destroyed) syncBox(); });

  return { getState, setImage, clearImage, destroy, resync, setBoxOffset, el: root };
}

function _buildClassic(o) {
  const mount = o.mount;
  if (!mount) throw new Error("buildResMaster: mount required");
  const STAGE_PX = o.stagePx || 108;
  const IMG_PX = o.imgPx || 100;

  let imageW = o.imageW || null;
  let imageH = o.imageH || null;
  let aspectLocked = !!o.aspectLocked || !!imageW;
  let mp = typeof o.mp === "number" ? o.mp : 1.0;
  const snapGrid = o.snapGrid || null;
  const gridUnit = o.gridUnit || 32;
  const onChange = typeof o.onChange === "function" ? o.onChange : () => {};
  let imageUrl = o.imageUrl || null;
  const onPickImage = o.onPickImage;
  const onClearImage = o.onClearImage;
  const onDropFile = o.onDropFile;
  const showImageZone = o.showImageZone !== false;

  let aspectW = imageW || o.aspectW || 9;
  let aspectH = imageH || o.aspectH || 16;
  let snappedDims = null;
  const MP_MIN = 0.25, MP_MAX = 4.0;
  const VISUAL_MP_FULL = 3.0;

  function nativeMP() { return imageW ? mpOf(imageW, imageH) : null; }
  function currentDims() {
    if (snappedDims) return snappedDims;
    return dimsForMP(aspectW / aspectH, mp, gridUnit);
  }
  function emit() {
    const [w, h] = currentDims();
    onChange({ w, h, mp: mpOf(w, h), aspectW, aspectH, hasImage: !!imageW });
  }

  const root = document.createElement("div");
  root.className = "gpl-rm";
  const left = document.createElement("div");
  left.className = "gpl-rm-left";
  const mid = document.createElement("div");
  mid.className = "gpl-rm-mid";
  const right = document.createElement("div");
  right.className = "gpl-rm-right";
  const imgZone = document.createElement("div");
  imgZone.className = "gpl-rm-img";
  const stage = document.createElement("div");
  stage.className = "gpl-rm-stage";
  const boxEl = document.createElement("div");
  boxEl.className = "gpl-rm-box";
  const handleHit = document.createElement("div");
  handleHit.className = "gpl-rm-hit";
  handleHit.appendChild(document.createElement("div")).className = "gpl-rm-handle";
  boxEl.appendChild(handleHit);
  stage.appendChild(boxEl);

  const mpSlider = document.createElement("input");
  mpSlider.type = "range";
  mpSlider.min = "0.25";
  mpSlider.max = "4";
  mpSlider.step = "0.05";
  mpSlider.value = String(mp);
  mpSlider.className = "gpl-rm-slider";

  left.appendChild(mpSlider);
  if (showImageZone) mid.appendChild(imgZone);
  mid.appendChild(stage);
  root.appendChild(left);
  root.appendChild(mid);
  root.appendChild(right);
  mount.appendChild(root);

  function syncBox() { emit(); }
  function setImage(w, h, url) {
    imageW = w; imageH = h; aspectW = w; aspectH = h; mp = mpOf(w, h);
    if (url !== undefined) imageUrl = url;
    syncBox();
  }
  function clearImage() { imageW = null; imageH = null; imageUrl = null; syncBox(); }
  function getState() {
    const [w, h] = currentDims();
    return { w, h, mp: mpOf(w, h) };
  }
  let _destroyed = false;
  return {
    getState, setImage, clearImage,
    destroy: () => { _destroyed = true; root.remove(); },
    resync: () => { if (!_destroyed) syncBox(); },
    el: root,
  };
}