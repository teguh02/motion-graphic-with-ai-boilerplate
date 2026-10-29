// ---------------------------------------------------------------- 2. ALUR KERJA
SCENES.push({
  id: 'alur', mood: 'warm', get start() { return cue('Cukup') - 0.15; }, get end() { return cue('Sudah') - 0.15; },
  build(root) {
    const t0 = this.start;
    const steps = [
      { word: 'naskah', icon: 'file-text', num: '01', title: 'Naskah', sub: 'narasi.txt' },
      { word: 'dubbing', icon: 'mic', num: '02', title: 'Dubbing', sub: 'dubing.wav' },
      { word: 'ilustrasi', icon: 'sparkles', num: '03', title: 'Adegan', sub: 'src/scenes/' },
    ];
    const tTepat = cue('tepat');

    const head = abs(h('div', { cls: 'title', style: 'font-size:78px;text-align:center', html: 'Tiga langkah <span class="accent">saja</span>' }), 'left:0;right:0;top:20px');
    const cards = steps.map((st, i) => {
      const card = abs(h('div', { cls: 'card', style: 'padding:34px 28px;display:flex;flex-direction:column;gap:20px' }, [
        h('div', { cls: 'row', style: 'justify-content:space-between' }, [disc(st.icon, 92, 48, i === 2 ? 'warm' : 'accent'), h('div', { cls: 'label', text: st.num })]),
        h('div', { cls: 'title', style: 'font-size:52px', text: st.title }),
        h('div', { cls: 'label', style: 'font-size:22px', text: st.sub }),
      ]), `left:${60 + i * 330}px;top:170px;width:300px`);
      return { card, t: cue(st.word) };
    });

    // timeline: the line draws on "tepat", word ticks light up one by one
    const tl = s('svg', { width: 960, height: 160, viewBox: '0 0 960 160' });
    const line = s('path', { d: 'M20 80 H940', pathLength: 1, stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round', fill: 'none' });
    tl.appendChild(line);
    const ticks = [0, 1, 2, 3, 4, 5].map((k) => {
      const g = s('circle', { cx: 80 + k * 160, cy: 80, r: 18, fill: 'var(--surface)', stroke: 'var(--ink)', 'stroke-width': 5 });
      tl.appendChild(g);
      return g;
    });
    const tlWrap = abs(h('div', {}, [tl]), 'left:60px;top:560px;width:960px;height:160px');
    const tlLabel = abs(h('div', { cls: 'label', style: 'text-align:center', text: 'kata diucapkan → elemen muncul' }), 'left:0;right:0;top:730px');

    root.append(head, ...cards.map((c) => c.card), tlWrap, tlLabel);
    cards.forEach((c) => E.sfx(c.t, 'pop', 0.8));
    E.sfx(tTepat, 'whoosh', 0.6);
    ticks.forEach((_, k) => E.sfx(tTepat + 0.25 + k * 0.12, 'tick', 0.6));

    return (t) => {
      E.rise(head, t, t0 + 0.1, 0.5, 0, 30);
      cards.forEach((c) => E.pop(c.card, t, c.t, 0.55, 0.5, { y: E.float(t, 4, 1.3, c.t) }));
      E.set(tlWrap, { o: E.prog(t, tTepat - 0.1, 0.2) });
      E.draw(line, t, tTepat, 0.7);
      ticks.forEach((g, k) => {
        const on = t >= tTepat + 0.25 + k * 0.12;
        g.setAttribute('fill', on ? 'var(--warm)' : 'var(--surface)');
        g.setAttribute('r', on ? 18 + 6 * (1 - E.prog(t, tTepat + 0.25 + k * 0.12, 0.25)) : 18);
      });
      E.rise(tlLabel, t, tTepat + 0.6, 0.4, 0, 20);
    };
  },
});
