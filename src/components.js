// Shared building blocks for scenes. Add project-specific pieces here (logos, mock UIs, charts).
// Scene contract: SCENES.push({ id, mood, start, end, build(root) -> update(t) }).
const SCENES = [];
const CODE_WINDOWS = []; // times where a spoken word is a code keyword (subtitle shows it as a code chip)
const { h, s, abs, icon, cue, cueEnd } = E;

// mark a spoken word as "code" for the subtitles (needs the word in project.json subtitles.code)
function codeWord(word, n = 1, after = 0) { const t = cue(word, n, after); CODE_WINDOWS.push([t - 0.01, t + 0.01]); return t; }

// photo from assets/img (credit it in assets/img/CREDITS.json)
function img(name, cap) {
  const box = h('div', { cls: 'photo' }, [h('img', { src: `../assets/img/${name}`, alt: '' })]);
  if (cap) box.appendChild(h('div', { cls: 'cap', text: cap }));
  return box;
}

// round-cornered icon tile; tone: accent | warm | ink
function disc(name, size = 88, iconSize = 46, tone = 'accent') {
  return h('div', { cls: `iconDisc tone-${tone}`, style: `width:${size}px;height:${size}px` }, [icon(name, iconSize, 'currentColor', 2.2)]);
}

function pill(text, iconName, tone = 'accent') {
  return h('div', { cls: `pill tone-${tone}` }, [iconName ? icon(iconName, 36, 'currentColor', 2.4) : null, text]);
}

// Code block. A line is a string or an array of segments: plain strings, or [text, markId] for spans that can be lit.
// Text inside is checked verbatim against content/brief.md by tools/check.py.
// opts: { file, tag, size, light, out: { cmd, text } }
function codeBlock(lines, opts = {}) {
  const { file = '', tag = '', size = 34, light = false, out = null } = opts;
  const root = h('div', { cls: light ? 'code light' : 'code' });
  const bar = h('div', { cls: 'bar' }, [h('span', { cls: 'd' }), h('span', { cls: 'd' }), h('span', { cls: 'd' }),
    h('span', { cls: 'fn', text: file }), h('span', { cls: 'tg', text: tag })]);
  const pre = h('pre', { style: `font-size:${size}px`, 'data-verbatim': '' });
  const marks = {};
  const lineEls = lines.map((spec) => {
    const tx = h('span', { cls: 'tx' });
    [].concat(typeof spec === 'string' ? [spec] : spec).forEach((seg) => {
      if (typeof seg === 'string') { tx.appendChild(document.createTextNode(seg)); return; }
      const [text, id] = seg;
      const sp = h('span', { cls: /^\s+$/.test(text) ? 'ws' : 'kw', text });
      (marks[id] = marks[id] || []).push(sp);
      tx.appendChild(sp);
    });
    const hl = h('span', { cls: 'hl' });
    const ln = h('span', { cls: 'ln' }, [hl, tx]);
    pre.appendChild(ln);
    return { ln, hl, tx };
  });
  root.append(bar, pre);
  let outEl = null;
  if (out) {
    outEl = h('div', { cls: 'out', style: `font-size:${Math.round(size * 0.86)}px` }, [h('div', { cls: 'pr', text: out.cmd || '' }), h('div', { text: out.text })]);
    root.appendChild(outEl);
  }
  const mark = (id, on, cls = 'on') => (marks[id] || []).forEach((sp) => sp.classList.toggle(cls, on));
  return { el: root, lines: lineEls, marks, mark, outEl, bar };
}

// position of el relative to an ancestor (layout is static, so this is safe to cache)
function offsetIn(el, ancestor) {
  let x = 0, y = 0, n = el;
  while (n && n !== ancestor) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
  return { x, y };
}
