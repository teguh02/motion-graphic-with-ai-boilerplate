// Karaoke subtitles built from aligned word timestamps (build/words.json).
// Keyword colours / renames come from project.json -> "subtitles".
const Subs = (() => {
  let CFG = { max_chars: 24, accent: [], code: [], rename: {} };
  const CODE_WINDOWS = []; // [t0, t1] ranges where a spoken code word is shown as a mono chip
  const norm = E.norm;

  function display(text) {
    const to = CFG.rename[norm(text)];
    if (!to) return text;
    const punct = (text.match(/[.,?!:;]+$/) || [''])[0];
    return to + punct;
  }

  function chunkTokens(tokens) {
    const chunks = [];
    let cur = [];
    const flush = () => { if (cur.length) chunks.push(cur); cur = []; };
    tokens.forEach((tk, i) => {
      const len = cur.reduce((a, w) => a + w.text.length + 1, 0);
      if (cur.length && (len + tk.text.length > CFG.max_chars || cur[0].para !== tk.para)) flush();
      cur.push(tk);
      const next = tokens[i + 1];
      const curLen = len + tk.text.length;
      const gap = next ? next.start - tk.end : 1;
      if (/[.?!:]$/.test(tk.text) || (/,$/.test(tk.text) && curLen >= 9) || gap > 0.45) flush();
    });
    flush();
    return chunks;
  }

  function keyClass(w) {
    const n = norm(w.text);
    const inCode = CODE_WINDOWS.some(([a, b]) => w.start >= a && w.start < b);
    if (CFG.code.includes(n) && (inCode || !CODE_WINDOWS.length)) return 'k-code';
    return CFG.accent.includes(n) ? 'k-accent' : '';
  }

  let built = [];
  function build(root, words, config = {}, codeWindows = []) {
    CFG = { ...CFG, ...config, accent: (config.accent || []).map(norm), code: (config.code || []).map(norm) };
    CFG.rename = Object.fromEntries(Object.entries(config.rename || {}).map(([k, v]) => [norm(k), v]));
    CODE_WINDOWS.push(...codeWindows);
    const tokens = words.map((w) => ({ ...w, text: display(w.text) }));
    const chunks = chunkTokens(tokens);
    built = chunks.map((ws, ci) => {
      const el = E.h('div', { cls: 'chunk' });
      const spans = ws.map((w) => {
        const sp = E.h('span', { cls: `w ${keyClass(w)}`, text: w.text.replace(/[,:;]$/, '') });
        el.appendChild(sp);
        return sp;
      });
      root.appendChild(el);
      const start = ws[0].start - 0.06;
      const nextStart = chunks[ci + 1] ? chunks[ci + 1][0].start - 0.06 : Infinity;
      const last = ws[ws.length - 1];
      // stay up through the last word even when the next chunk follows immediately
      const end = Math.max(last.end + 0.02, Math.min(last.end + 0.5, nextStart));
      const fadeAt = Math.max(end - 0.12, last.end);
      return { el, spans, ws, start, end, fadeAt };
    });
  }

  function update(t) {
    built.forEach((c) => {
      const visible = t >= c.start && t < c.end;
      if (!visible) { c.el.style.opacity = 0; return; }
      const pIn = E.ease.outBack(E.prog(t, c.start, 0.22));
      const pOut = E.prog(t, c.fadeAt, Math.max(0.01, c.end - c.fadeAt));
      c.el.style.opacity = (1 - pOut).toString();
      c.el.style.transform = `translateY(${(1 - pIn) * 24}px) scale(${E.lerp(0.94, 1, pIn)})`;
      c.spans.forEach((sp, i) => {
        const w = c.ws[i];
        const active = t >= w.start - 0.03 && t < w.end + 0.05;
        const said = t >= w.start - 0.03;
        sp.classList.toggle('on', active);
        sp.style.opacity = said ? 1 : 0.38;
        const pw = E.prog(t, w.start - 0.03, 0.18);
        sp.style.transform = active ? `scale(${E.lerp(1.12, 1.05, E.ease.outCubic(pw))})` : 'scale(1)';
      });
    });
  }

  return { build, update };
})();
