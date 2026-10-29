// ---------------------------------------------------------------- 3. FITUR
SCENES.push({
  id: 'fitur', mood: 'accent', get start() { return cue('Sudah') - 0.15; }, get end() { return cue('Selamat') - 0.15; },
  build(root) {
    const t0 = this.start;
    const tVert = cue('vertikal'), tRender = cue('render');
    const feats = [
      { word: 'subtitle', icon: 'captions', text: 'Subtitle karaoke' },
      { word: 'efek', icon: 'volume-2', text: 'Efek suara sintetis' },
      { word: 'render', icon: 'clapperboard', text: 'Render otomatis' },
    ];

    const head = abs(h('div', { cls: 'eyebrow', text: 'Sudah termasuk' }), 'left:60px;top:30px');
    const rows = feats.map((f, i) => {
      const el = abs(h('div', { cls: 'card row', style: 'gap:24px;padding:22px 28px' }, [
        disc(f.icon, 84, 44, 'accent'),
        h('div', { cls: 'title', style: 'font-size:40px', text: f.text }),
        h('div', { style: 'margin-left:auto' }, [icon('check', 40, 'var(--accent)', 3)]),
      ]), `left:60px;top:${100 + i * 150}px;width:600px`);
      return { el, t: cue(f.word) };
    });
    const cmd = codeBlock(['python tools/render.py'], { file: 'terminal', tag: 'bash', size: 30 });
    abs(cmd.el, 'left:60px;top:580px;width:600px');

    // phone frame, appears on "vertikal"
    const phone = abs(h('div', { style: 'width:300px;height:560px;border-radius:44px;border:10px solid var(--ink);background:var(--bg-2);box-shadow:var(--shadow-lift);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px' }, [
      icon('smartphone', 72, 'var(--accent)', 2),
      h('div', { style: 'font-family:var(--mono);font-weight:800;font-size:34px', text: '1080×1920' }),
      h('div', { cls: 'label', text: '30 fps · MP4' }),
    ]), 'left:720px;top:110px');

    root.append(head, ...rows.map((r) => r.el), cmd.el, phone);
    rows.forEach((r) => E.sfx(r.t, 'pop', 0.8));
    E.sfx(tVert, 'swell', 0.6);
    E.sfx(tVert + 0.1, 'ding', 0.6);

    return (t) => {
      E.rise(head, t, t0 + 0.1, 0.45, -40, 0);
      rows.forEach((r) => E.rise(r.el, t, r.t, 0.5, -80, 0));
      E.rise(cmd.el, t, tRender + 0.2, 0.5, 0, 40);
      cmd.lines[0].hl.style.opacity = E.prog(t, tRender + 0.5, 0.3);
      E.pop(phone, t, tVert, 0.6, 0.5, { r: E.lerp(-8, 0, E.ease.outBack(E.prog(t, tVert, 0.6))), y: E.float(t, 6, 1.2) });
    };
  },
});
