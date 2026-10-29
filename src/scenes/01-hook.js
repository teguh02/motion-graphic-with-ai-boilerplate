// ---------------------------------------------------------------- 1. HOOK
// Every timed reveal is keyed to a spoken word via cue(), so visuals land on the voice.
// start/end are getters because word timings load after this file runs.
SCENES.push({
  id: 'hook', mood: 'accent', start: 0, get end() { return cue('Cukup') - 0.15; },
  build(root) {
    const tTitle = cue('boilerplate'), tAgent = cue('agen');

    const eyebrow = abs(h('div', { cls: 'eyebrow', text: 'Boilerplate · Template' }), 'left:0;right:0;top:40px;text-align:center');
    const badge = abs(disc('sparkles', 140, 76, 'warm'), 'left:470px;top:110px');
    const title = abs(h('div', { cls: 'title', style: 'font-size:150px;text-align:center' },
      ['Motion', h('br'), h('span', { cls: 'accent', text: 'Graphic' })]), 'left:0;right:0;top:290px');

    const agents = ['Claude Code', 'Codex', 'OpenCode'].map((name, i) => h('div', {}, [pill(name, 'bot', i === 0 ? 'accent' : 'ink')]));
    const agentRow = abs(h('div', { cls: 'row', style: 'gap:18px;justify-content:center' }, agents), 'left:0;right:0;top:660px');

    root.append(eyebrow, badge, title, agentRow);
    E.sfx(tTitle, 'whoosh', 0.8);
    E.sfx(tTitle + 0.05, 'pop');
    agents.forEach((_, i) => E.sfx(tAgent + i * 0.14, 'pop', 0.7));

    return (t) => {
      E.rise(eyebrow, t, 0.1, 0.5, 0, 30);
      E.pop(badge, t, 0.2, 0.6, 0.2, { y: E.float(t, 8, 1.6) });
      E.pop(title, t, tTitle, 0.6, 0.6);
      agents.forEach((a, i) => E.rise(a, t, tAgent + i * 0.14, 0.45, 0, 50));
    };
  },
});
