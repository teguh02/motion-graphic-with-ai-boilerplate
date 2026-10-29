// Deterministic motion helpers: every visual is a pure function of time t (seconds).
// Never use Date.now(), setTimeout, CSS transitions/animations or unseeded Math.random() in scenes —
// the renderer jumps to arbitrary t, so anything not derived from t will flicker or desync.
const E = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, p) => a + (b - a) * p;
  const prog = (t, t0, d) => clamp((t - t0) / d);

  // cubic-bezier(x1,y1,x2,y2) evaluated at x=p (bisection on x(t))
  function bezier(x1, y1, x2, y2, p) {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    const bx = (t) => 3 * x1 * t * (1 - t) ** 2 + 3 * x2 * t * t * (1 - t) + t ** 3;
    const by = (t) => 3 * y1 * t * (1 - t) ** 2 + 3 * y2 * t * t * (1 - t) + t ** 3;
    let lo = 0, hi = 1, t = p;
    for (let i = 0; i < 30; i++) {
      const x = bx(t);
      if (Math.abs(x - p) < 1e-5) break;
      if (x < p) lo = t; else hi = t;
      t = (lo + hi) / 2;
    }
    return by(t);
  }

  const ease = {
    linear: (p) => p,
    outCubic: (p) => 1 - Math.pow(1 - p, 3),
    inCubic: (p) => p * p * p,
    inOutCubic: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    outBack: (p) => {
      const c1 = 1.70158, c3 = c1 + 1;
      return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2);
    },
    // material standard easing, cubic-bezier(0.2, 0, 0, 1)
    material: (p) => bezier(0.2, 0, 0, 1, p),
    outExpo: (p) => (p === 1 ? 1 : 1 - Math.pow(2, -10 * p)),
    outElastic: (p) => {
      if (p === 0 || p === 1) return p;
      return Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1;
    },
    bezier,
  };

  // seeded PRNG (mulberry32): same seed -> same sequence on every frame
  function rand(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let r = Math.imul(a ^ (a >>> 15), 1 | a);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------- DOM ----------
  function h(tag, props = {}, children = []) {
    const el = document.createElement(tag);
    const { cls, style, html, text, ...attrs } = props;
    if (cls) el.className = cls;
    if (style) el.style.cssText = style;
    if (html !== undefined) el.innerHTML = html;
    if (text !== undefined) el.textContent = text;
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    [].concat(children).forEach((c) => c && el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c));
    return el;
  }

  const SVGNS = 'http://www.w3.org/2000/svg';
  function s(tag, attrs = {}, children = []) {
    const el = document.createElementNS(SVGNS, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    [].concat(children).forEach((c) => c && el.appendChild(c));
    return el;
  }

  // absolutely positioned element; css is appended to its inline style
  function abs(el, css) { el.classList.add('abs'); el.style.cssText += css; return el; }

  // ---------- icons (Lucide SVG files in assets/icons) ----------
  const ICONS = {};
  async function loadIcons(names) {
    await Promise.all(names.map(async (n) => {
      const res = await fetch(`../assets/icons/${n}.svg`);
      if (!res.ok) throw new Error(`icon missing: ${n} (run: python tools/fetch_icons.py ${n})`);
      ICONS[n] = (await res.text()).replace(/<!--.*?-->/s, '');
    }));
  }

  function icon(name, size = 64, color = 'currentColor', sw = 2) {
    const raw = ICONS[name];
    if (!raw) throw new Error(`icon not loaded: ${name} (add it to ICON_NAMES in main.js)`);
    const markup = raw
      .replace(/width="24"/, `width="${size}"`)
      .replace(/height="24"/, `height="${size}"`)
      .replace(/stroke-width="2"/, `stroke-width="${sw}"`);
    return h('span', { cls: 'ic', style: `color:${color};width:${size}px;height:${size}px`, html: markup });
  }
  const rawIcon = (n) => { if (!ICONS[n]) throw new Error(`icon not loaded: ${n}`); return ICONS[n]; };

  // ---------- transforms ----------
  function set(el, { o = 1, x = 0, y = 0, sc = 1, r = 0, blur = 0, sx, sy } = {}) {
    const scale = sx !== undefined || sy !== undefined ? `scale(${sx ?? sc},${sy ?? sc})` : `scale(${sc})`;
    el.style.opacity = o;
    el.style.transform = `translate(${x}px,${y}px) ${scale} rotate(${r}deg)`;
    el.style.filter = blur > 0.05 ? `blur(${blur}px)` : 'none';
  }

  // pop in with overshoot; returns progress 0..1
  function pop(el, t, t0, d = 0.5, from = 0.3, extra = {}) {
    const p = prog(t, t0, d);
    set(el, { o: ease.outCubic(clamp(p * 2.5)), sc: lerp(from, 1, ease.outBack(p)), ...extra });
    return p;
  }

  // slide from offset with fade + blur; returns progress 0..1
  function rise(el, t, t0, d = 0.55, dx = 0, dy = 60, extra = {}) {
    const p = prog(t, t0, d);
    const e = ease.material(p);
    set(el, { o: e, x: dx * (1 - e), y: dy * (1 - e), blur: 10 * (1 - e), ...extra });
    return p;
  }

  // stroke drawing: the SVG path must have pathLength="1"
  function draw(el, t, t0, d, fn = ease.inOutCubic) {
    const p = fn(prog(t, t0, d));
    el.style.strokeDasharray = '1 1';
    el.style.strokeDashoffset = `${1 - p}`;
    return p;
  }

  function count(t, t0, d, from, to, fn = ease.outCubic) {
    return lerp(from, to, fn(prog(t, t0, d)));
  }

  // typewriter: the visible prefix of `str` at time t, typed at `cps` characters per second
  function typed(str, t, t0, cps = 18) {
    return str.slice(0, Math.floor(clamp((t - t0) * cps, 0, str.length)));
  }

  // damped shake offset, starts at t0
  function shake(t, t0, d = 0.45, amp = 18) {
    const p = prog(t, t0, d);
    if (p <= 0 || p >= 1) return 0;
    return Math.sin((t - t0) * 70) * amp * (1 - p);
  }

  // soft idle float
  const float = (t, amp = 6, speed = 1.4, phase = 0) => Math.sin(t * speed + phase) * amp;

  // ---------- word cues (build/words.json) ----------
  let WORDS = [];
  const norm = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, '');
  function setWords(words) { WORDS = words; }

  // start time of the n-th spoken occurrence of `phrase` (one or more words), optionally after time `after`
  function cue(phrase, n = 1, after = 0) {
    const keys = phrase.split(/\s+/).map(norm).filter(Boolean);
    let seen = 0;
    for (let i = 0; i <= WORDS.length - keys.length; i++) {
      if (WORDS[i].start < after) continue;
      if (keys.every((k, j) => norm(WORDS[i + j].text) === k) && ++seen === n) return WORDS[i].start;
    }
    throw new Error(`cue not found: "${phrase}" #${n} after ${after}s — the word must exist in content/narasi.txt`);
  }
  // end time of the last word of that occurrence
  function cueEnd(phrase, n = 1, after = 0) {
    const st = cue(phrase, n, after);
    const i = WORDS.findIndex((w) => w.start === st);
    const len = phrase.split(/\s+/).map(norm).filter(Boolean).length;
    return WORDS[i + len - 1].end;
  }

  // ---------- sfx registry (mixed into the audio at render time, see tools/sfx.py) ----------
  const SFX = [];
  const SFX_TYPES = ['whoosh', 'pop', 'tick', 'click', 'hit', 'stamp', 'ding', 'swell', 'fall', 'coins'];
  function sfx(t, type, gain = 1) {
    if (!SFX_TYPES.includes(type)) throw new Error(`unknown sfx: ${type} (one of ${SFX_TYPES.join(', ')})`);
    SFX.push({ t: +t.toFixed(3), type, gain });
    return t;
  }

  return {
    clamp, lerp, prog, ease, rand, h, s, abs, icon, rawIcon, loadIcons, set, pop, rise, draw, count, typed, shake, float,
    norm, cue, cueEnd, setWords, sfx, SFX,
  };
})();
