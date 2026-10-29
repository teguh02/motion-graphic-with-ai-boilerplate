// ---------------------------------------------------------------- 4. PENUTUP + OUTRO
// The last scene runs to TOTAL (last word + project.json "outro"); main.js fades the credit in during it.
SCENES.push({
  id: 'outro', mood: 'warm', get start() { return cue('Selamat') - 0.15; }, get end() { return cueEnd('berkarya') + CFG.outro; },
  build(root) {
    const tSel = cue('Selamat');
    const badge = abs(disc('sparkles', 160, 88, 'warm'), 'left:460px;top:80px');
    const title = abs(h('div', { cls: 'title', style: 'font-size:132px;text-align:center' },
      ['Selamat', h('br'), h('span', { cls: 'accent', text: 'berkarya!' })]), 'left:0;right:0;top:300px');
    const under = abs(h('div', { style: 'height:10px;border-radius:5px;background:var(--warm);transform-origin:left' }), 'left:240px;width:600px;top:600px');
    root.append(badge, title, under);
    E.sfx(tSel, 'hit', 0.7);
    E.sfx(tSel + 0.05, 'pop');

    return (t) => {
      E.pop(badge, t, tSel, 0.6, 0.2, { r: E.float(t, 6, 1.1), y: E.float(t, 8, 1.5) });
      E.pop(title, t, tSel + 0.08, 0.6, 0.6, { x: E.shake(t, tSel, 0.4, 10) });
      under.style.transform = `scaleX(${E.ease.material(E.prog(t, tSel + 0.4, 0.6))})`;
    };
  },
});
