// Boot: load config + word timings, build every scene once, then expose renderAt(t) for frame capture.
// Every icon a scene uses must be listed here (missing files: python tools/fetch_icons.py <name>).
const ICON_NAMES = ['file-text', 'mic', 'sparkles', 'captions', 'volume-2', 'clapperboard', 'smartphone', 'bot', 'check', 'arrow-right'];
const ENTER = 0.42, EXIT = 0.32; // scene cross-fade durations (s)

const $ = (id) => document.getElementById(id);
const built = [];
const moods = {};
let CFG = {};
let TOTAL = 0;
let VOICE_END = 0; // end of the last spoken word
let tickerHalf = 1;
let creditEl = null;

function buildChrome() {
  $('brandName').textContent = CFG.brand.name;
  $('brandTag').textContent = CFG.brand.tag;
  $('brandMark').textContent = CFG.brand.name.slice(0, 2);

  const track = $('tickerTrack');
  for (let r = 0; r < 3; r++) {
    (CFG.ticker || []).forEach((item) => {
      track.appendChild(E.h('span', { text: item }));
      track.appendChild(E.h('span', { cls: 'sep', text: '·' }));
    });
  }
  tickerHalf = Math.max(1, track.scrollWidth / 3);

  const bars = $('progress');
  built.forEach((b) => { const i = E.h('i'); const fill = E.h('b'); i.appendChild(fill); bars.appendChild(i); b.bar = fill; });

  const credit = E.h('div', { cls: 'credit', html: CFG.brand.credit });
  const wrap = E.h('div', { cls: 'creditWrap' }, [credit]);
  $('frame').appendChild(wrap);
  return wrap;
}

async function waitImages(strict) {
  await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((ok, bad) => {
    im.onload = ok;
    im.onerror = strict ? () => bad(new Error(`image failed: ${im.src}`)) : ok;
  }))));
}

async function init() {
  CFG = await fetch('../project.json').then((r) => r.json());
  document.documentElement.style.setProperty('--W', `${CFG.width}px`);
  document.documentElement.style.setProperty('--H', `${CFG.height}px`);
  await E.loadIcons(ICON_NAMES);
  const res = await fetch('../build/words.json');
  if (!res.ok) throw new Error('build/words.json missing — run: python tools/transcribe.py (or tools/estimate_words.py for a draft)');
  const words = await res.json();
  E.setWords(words);
  VOICE_END = words[words.length - 1].end;
  TOTAL = +(VOICE_END + CFG.outro).toFixed(2);
  await document.fonts.ready;

  SCENES.forEach((def) => {
    const root = E.h('div', { cls: 'scene', 'data-id': def.id });
    $('stage').appendChild(root);
    const update = def.build(root);
    built.push({ def, root, update, start: def.start, end: Math.min(def.end, TOTAL) });
  });
  await waitImages(true);
  Subs.build($('subs'), words, CFG.subtitles, CODE_WINDOWS);
  creditEl = buildChrome();
  document.querySelectorAll('.glow').forEach((g) => { moods[g.dataset.mood] = g; });

  window.SFX_EVENTS = E.SFX.slice().sort((a, b) => a.t - b.t);
  window.TOTAL = TOTAL;
  window.CONFIG = CFG;
  window.SCENE_TIMES = built.map((b) => ({ id: b.def.id, start: +b.start.toFixed(2), end: +b.end.toFixed(2) }));
  window.READY = true;
}

function renderAt(t) {
  const moodW = Object.fromEntries(Object.keys(moods).map((m) => [m, 0]));
  built.forEach((b) => {
    const visible = t >= b.start && t < b.end + EXIT;
    b.bar.style.transform = `scaleX(${E.prog(t, b.start, b.end - b.start)})`;
    if (!visible) { b.root.style.opacity = 0; b.root.style.visibility = 'hidden'; return; }
    b.root.style.visibility = 'visible';
    const pin = E.ease.material(E.prog(t, b.start, ENTER));
    const pout = E.ease.inCubic(E.prog(t, b.end, EXIT));
    const o = Math.min(pin, 1 - pout);
    b.root.style.opacity = o;
    b.root.style.transform = `translateY(${(1 - pin) * 60 - pout * 50}px) scale(${E.lerp(0.96, 1, pin) + pout * 0.04})`;
    b.root.style.filter = (1 - pin) + pout > 0.02 ? `blur(${((1 - pin) + pout) * 12}px)` : 'none';
    if (b.def.mood in moodW) moodW[b.def.mood] = Math.max(moodW[b.def.mood], o);
    b.update(t);
  });
  Object.entries(moods).forEach(([m, el]) => { el.style.opacity = moodW[m] * (0.85 + 0.15 * Math.sin(t * 2.2)); });

  $('dots').style.transform = `translateY(${(t * 14) % 44}px)`;
  $('tickerTrack').style.transform = `translateX(${-((t * 80) % tickerHalf)}px)`;

  const flash = window.SFX_EVENTS.filter((e) => e.type === 'hit')
    .reduce((m, e) => Math.max(m, t >= e.t ? (1 - E.prog(t, e.t, 0.22)) * 0.35 * e.gain : 0), 0);
  $('flash').style.opacity = flash;

  Subs.update(t);
  // credit sits in the subtitle zone, so it waits until the last subtitle has gone
  const pc = E.ease.material(E.prog(t, VOICE_END + 0.6, 0.6));
  creditEl.style.opacity = pc;
  creditEl.style.transform = `translateY(${(1 - pc) * 24}px)`;
}

window.renderAt = renderAt;
init().catch((err) => { window.INIT_ERROR = String((err && err.stack) || err); });

// ---------- preview (not used by the renderer) ----------
// ?t=12.5  -> freeze at 12.5 s     ?dev -> scrubber + play with build/voice.wav
function fitToWindow() {
  const k = Math.min(innerWidth / CFG.width, (innerHeight - 70) / CFG.height);
  $('frame').style.transform = `scale(${k})`;
  $('frame').style.transformOrigin = 'top left';
  document.body.classList.add('preview');
}

function devPanel() {
  const audio = new Audio('../build/voice.wav');
  const bar = E.h('div', { id: 'dev' });
  const btn = E.h('button', { text: '▶' });
  const range = E.h('input', { type: 'range', min: 0, max: TOTAL, step: 0.01, value: 0 });
  const label = E.h('span', { text: '0.00s' });
  bar.append(btn, range, label);
  document.body.appendChild(bar);
  let playing = false;
  const show = (t) => { renderAt(t); range.value = t; label.textContent = `${(+t).toFixed(2)}s / ${TOTAL}s`; };
  range.addEventListener('input', () => { audio.currentTime = +range.value; show(+range.value); });
  btn.addEventListener('click', () => {
    playing = !playing;
    btn.textContent = playing ? '❚❚' : '▶';
    if (playing) { audio.currentTime = +range.value; audio.play().catch(() => {}); } else audio.pause();
  });
  const loop = () => {
    if (playing) show(audio.ended || audio.error ? Math.min(TOTAL, +range.value + 1 / 60) : audio.currentTime);
    requestAnimationFrame(loop);
  };
  show(0);
  loop();
}

const params = new URLSearchParams(location.search);
if (params.has('dev') || params.has('t')) {
  const wait = setInterval(() => {
    if (window.INIT_ERROR) { clearInterval(wait); document.body.innerHTML = `<pre id="err">${window.INIT_ERROR}</pre>`; return; }
    if (!window.READY) return;
    clearInterval(wait);
    fitToWindow();
    if (params.has('dev')) devPanel(); else renderAt(+params.get('t'));
  }, 50);
}
