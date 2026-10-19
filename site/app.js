/* Standalone Watch — static site.
   Data comes from site/data/*.json (built daily by export_site_data.py).
   Pages are drawn by small functions below; the URL hash picks the page. */
'use strict';

const S = {};                       // loaded data: cfg, market, companies, news, ar
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pad = n => String(n).padStart(2, '0');
const isNum = x => typeof x === 'number' && isFinite(x);
const RED = '#e10600', WHITE = '#f5f5f5', GREY = '#5e5e5e', RULE = '#1a1a1a';
const FONT = "'SF Mono', SFMono-Regular, ui-monospace, Menlo, monospace";

function fmtUSD(x) {
  if (!isNum(x)) return '—';
  if (x === 0) return '$0';
  if (Math.abs(x) >= 1e9) return '$' + (x / 1e9).toFixed(2) + 'bn';
  if (Math.abs(x) >= 1e6) return '$' + Math.round(x / 1e6).toLocaleString('en-US') + 'm';
  return '$' + Math.round(x / 1e3).toLocaleString('en-US') + 'k';   // small, illiquid names
}
const fmtPct = x => isNum(x) ? (x > 0 ? '+' : '') + x.toFixed(1) + '%' : '—';
const fmt = (x, d = 1) => isNum(x) ? x.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }) : '—';
const median = arr => { const a = arr.filter(isNum).sort((p, q) => p - q); if (!a.length) return NaN;
  const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; };

async function getJSON(name) {
  const r = await fetch('data/' + name, { cache: 'no-cache' });
  if (!r.ok) throw new Error(name + ' ' + r.status);
  return r.json();
}

/* ---------------------------------------------------------------- countdowns */
function remaining() {
  const ms = Math.max(0, Date.parse(S.cfg.decision) - Date.now());
  return { d: Math.floor(ms / 864e5), h: pad(Math.floor(ms % 864e5 / 36e5)),
           m: pad(Math.floor(ms % 36e5 / 6e4)), s: pad(Math.floor(ms % 6e4 / 1e3)) };
}
function tick() {
  const r = remaining();
  const status = S.cfg.decision_confirmed ? '' : 'EXPECTED ';
  $('#mini').innerHTML = `<span class="l">${status}MSCI DECISION IN</span><b>${r.d}D ${r.h}:${r.m}:</b><span class="red">${r.s}</span>`;
  const c = $('#clock');
  if (c) { $('#cd').textContent = r.d; $('#ch').textContent = r.h; $('#cm').textContent = r.m; $('#cs').textContent = r.s; }
}

/* ---------------------------------------------------------------- shared pieces */
const section = (n, t, m = '') =>
  `<div class="section"><div><span class="n">${n}</span><span class="t">${t}</span></div><span class="m">${m}</span></div>`;
const navArrow = (href, label, sym = '↓') =>
  `<div class="navarrow"><a href="${href}">${sym}</a><span>${label}</span></div>`;
function formula(label, parts, result) {
  const terms = parts.map(([v, c]) => `<span class="term"><span class="v">${v}</span><span class="c">${c}</span></span>`)
    .join('<span class="op">×</span>');
  return `<div class="formula"><div class="l">${label}</div><div class="eq">${terms}<span class="op">=</span>` +
         `<span class="term"><span class="v r">${result}</span><span class="c">&nbsp;</span></span></div></div>`;
}
function companyHTML(code, withPrice) {
  const p = S.companies[code] || { name: code, about: '', products: [] };
  let px = '';
  if (withPrice) {
    const t = S.market.tape.find(x => x.code === code);
    if (t && isNum(t.close)) px = `<div class="px">Last close IDR ${Math.round(t.close).toLocaleString('en-US')} &nbsp; ` +
      `<span class="${t.chg < 0 ? 'dn-c' : 'up-c'}">${t.chg < 0 ? '▼' : '▲'} ${Math.abs(t.chg).toFixed(1)}%</span></div>`;
  }
  const chips = (p.products || []).map(x => `<span class="chip">${esc(x)}</span>`).join('');
  return `<div class="code">${esc(code)} · IDX</div><div class="nm">${esc(p.name)}</div>${px}` +
         `<div class="ab">${esc(p.about) || 'Profile coming soon.'}</div>` +
         (chips ? `<div class="pl">KNOWN FOR</div><div class="chips">${chips}</div>` : '');
}
function plot(el, traces, layout) {             // Plotly loads in the background; wait for it if needed
  if (!el) return;
  if (!window.Plotly) return setTimeout(() => plot(el, traces, layout), 150);
  Plotly.react(el, traces, Object.assign({
    margin: { l: 0, r: 0, t: 10, b: 0 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: FONT, color: GREY, size: 10 }, showlegend: false,
    hoverlabel: { bgcolor: '#0b0b0b', bordercolor: '#2a2a2a', font: { family: FONT, color: WHITE, size: 11 } },
  }, layout, {
    xaxis: Object.assign({ showspikes: false }, layout.xaxis || {}),   // no thick hover line; the dark tooltip is enough
  }), { displayModeBar: false, responsive: true });
}

/* sliders: red filled track + value bubble that follows the handle */
const sliderHTML = (id, min, max, val, label) =>
  `<div class="sl"><span class="bub" id="${id}V">${label}</span><input class="rng" type="range" id="${id}" min="${min}" max="${max}" value="${val}"></div>`;
function paintSlider(el, label) {
  const pct = (el.value - el.min) / (el.max - el.min) * 100;
  el.style.setProperty('--p', pct + '%');
  const bub = document.getElementById(el.id + 'V');
  if (!bub) return;
  if (label != null) bub.textContent = label;
  bub.style.left = `calc(${pct}% + ${7 - pct * 0.14}px)`;      // keep the label centred over the 14px handle
}

/* ---------------------------------------------------------------- company card modal */
function openCard(code) {
  $('#modalCard').innerHTML = `<button class="x" aria-label="Close">×</button>` + companyHTML(code, true);
  $('#modal').classList.add('open');
  $('.hero')?.classList.add('paused');
}
function closeCard() { $('#modal').classList.remove('open'); $('.hero')?.classList.remove('paused'); }
$('#modal').addEventListener('click', e => { if (e.target.id === 'modal' || e.target.classList.contains('x')) closeCard(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCard(); });

/* ================================================================ HOME */
function renderHome(view) {
  const m = S.market, tape = m.tape, half = Math.ceil(tape.length / 2);
  const col = (rows, dir) => {
    const items = rows.map(t => `<div class="tk" data-code="${t.code}"><span class="c">${t.code}</span>` +
      `<span class="p">${Math.round(t.close).toLocaleString('en-US')}</span>` +
      `<span class="x ${t.chg < 0 ? 'dn-c' : 'up-c'}">${t.chg < 0 ? '▼' : '▲'} ${Math.abs(t.chg).toFixed(1)}%</span></div>`).join('');
    return `<div class="tape ${dir}"><div class="roll">${items}${items}</div></div>`;
  };
  const row = (rows, dir) => {
    const items = rows.map(t => `<span class="th" data-code="${t.code}"><b>${t.code}</b> ${Math.round(t.close).toLocaleString('en-US')} ` +
      `<span class="${t.chg < 0 ? 'dn-c' : 'up-c'}">${t.chg < 0 ? '▼' : '▲'}${Math.abs(t.chg).toFixed(1)}%</span></span>`).join('');
    return `<div class="tape-h ${dir}"><div class="rollh">${items}${items}</div></div>`;
  };
  const dur = Math.max(70, Math.round(half * 3.5));       // same calm speed however many stocks
  const status = S.cfg.decision_confirmed ? 'confirmed' : 'expected';
  const dec = new Date(S.cfg.decision).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Jakarta' });
  view.innerHTML = `
    <section class="hero" style="--dur:${dur}s">
      ${col(tape.slice(0, half), 'up')}${col(tape.slice(half), 'dn')}
      ${row(tape.slice(0, half), 'l')}${row(tape.slice(half), 'r')}
      <div class="title">Indonesia, <span class="red">downgraded?</span></div>
      <div class="clock" id="clock">
        <span class="v" id="cd">—</span><span class="k">d</span>
        <span class="v" id="ch">—</span><span class="k">h</span>
        <span class="v" id="cm">—</span><span class="k">m</span>
        <span class="v red" id="cs">—</span><span class="k">s</span>
      </div>
      <div class="cap">until MSCI decides &nbsp;·&nbsp; ${status} ${dec}</div>
      <div class="bottom">
        <div class="mkt">JCI <span class="red">${fmtPct(m.jci_change)}</span> &nbsp;&nbsp; USD/IDR <span>${fmt(m.fx_last, 0)}</span> &nbsp;&nbsp; since 15 Oct</div>
        <a class="go" href="#/news"><span class="lbl">See what's going on in Indonesia</span><span class="down">↓</span></a>
      </div>
    </section>`;
  $$('.tk, .th', view).forEach(el => el.addEventListener('click', () => openCard(el.dataset.code)));
  tick();
}

/* ================================================================ MARKET CHECK (candlesticks) */
const mk = { asset: 'eido', freq: 'Weekly' };
const ASSETS = { eido: { name: 'EIDO · USD', long: 'iShares MSCI Indonesia ETF, in US dollars: how global investors see Indonesia', px: v => '$' + v.toFixed(2) },
                 jci: { name: 'JCI · IDR', long: 'Jakarta Composite Index, in rupiah: the local market', px: v => fmt(v, 0) } };

function weekly(s) {                       // daily candles -> weekly (Mon–Fri) candles
  const out = { d: [], o: [], h: [], l: [], c: [] };
  s.d.forEach((d, i) => {
    const dt = new Date(d + 'T00:00:00'), monday = new Date(dt); monday.setDate(dt.getDate() - ((dt.getDay() + 6) % 7));
    const key = monday.toISOString().slice(0, 10), n = out.d.length - 1;
    if (n < 0 || out.d[n] !== key) { out.d.push(key); out.o.push(s.o[i]); out.h.push(s.h[i]); out.l.push(s.l[i]); out.c.push(s.c[i]); }
    else { out.h[n] = Math.max(out.h[n], s.h[i]); out.l[n] = Math.min(out.l[n], s.l[i]); out.c[n] = s.c[i]; }
  });
  return out;
}

function marketPanel() {
  return `<div class="panel">
    <div class="mk-head">
      <div><div class="label ptitle" style="margin-bottom:6px">Market check</div><div class="note" id="mkLong" style="margin:0"></div></div>
      <div class="mk-ctl"><div class="seg" id="mkAsset">${Object.entries(ASSETS).map(([k, a]) => `<button data-k="${k}" class="${k === mk.asset ? 'on' : ''}">${a.name}</button>`).join('')}</div>
        <div class="seg" id="mkFreq">${['Daily', 'Weekly'].map(f => `<button class="${f === mk.freq ? 'on' : ''}">${f}</button>`).join('')}</div></div>
    </div>
    <div class="metrics" style="--cols:4" id="mkStats"></div>
    <div id="mkChart" class="candles"></div>
  </div>`;
}

function marketDraw() {
  const s = S.candles[mk.asset], A = ASSETS[mk.asset], n = s.c.length - 1;
  const pct = (a, b) => isNum(a) && isNum(b) && b ? (a / b - 1) * 100 : null;
  const i15 = s.d.findIndex(d => d >= S.cfg.announcement) - 1;            // last close before the proposal
  const stat = (k, v, cls = '') => `<div class="metric"><div class="k">${k}</div><div class="v ${cls}">${v}</div></div>`;
  const tone = v => isNum(v) ? (v < 0 ? 'neg' : 'pos') : '';
  const dod = pct(s.c[n], s.c[n - 1]), wow = pct(s.c[n], s.c[n - 5]), since = i15 >= 0 ? pct(s.c[n], s.c[i15]) : null;
  $('#mkLong').textContent = A.long + ' · last close ' + new Date(s.d[n] + 'T00:00:00').toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  $('#mkStats').innerHTML = stat('Last close', A.px(s.c[n])) + stat('Day over day', fmtPct(dod), tone(dod)) +
                            stat('Week over week', fmtPct(wow), tone(wow)) + stat('Since 15 Oct', fmtPct(since), tone(since));
  const c = mk.freq === 'Weekly' ? weekly(s) : s;
  plot($('#mkChart'), [{
    type: 'candlestick', x: c.d, open: c.o, high: c.h, low: c.l, close: c.c,
    increasing: { line: { color: WHITE, width: 1 }, fillcolor: WHITE }, decreasing: { line: { color: RED, width: 1 }, fillcolor: RED },
    hoverlabel: { bgcolor: '#0b0b0b' }, whiskerwidth: 0,
  }], {
    margin: { l: 0, r: 0, t: 10, b: 0 }, hovermode: 'x',
    xaxis: { showgrid: false, linecolor: RULE, rangeslider: { visible: false }, type: 'date' },
    yaxis: { showgrid: true, gridcolor: '#141414', side: 'right', zeroline: false, tickprefix: mk.asset === 'eido' ? '$' : '' },
    shapes: [{ type: 'line', x0: S.cfg.announcement, x1: S.cfg.announcement, yref: 'paper', y0: 0, y1: 1, line: { color: RED, width: 1, dash: 'dot' } }],
    annotations: [{ x: S.cfg.announcement, y: 1, yref: 'paper', text: 'MSCI PROPOSAL', showarrow: false, xanchor: 'right', yanchor: 'top', font: { color: RED, size: 9 } }],
  });
}

function marketWire(view) {
  $$('#mkAsset button', view).forEach(b => b.addEventListener('click', () => {
    mk.asset = b.dataset.k; $$('#mkAsset button', view).forEach(x => x.classList.toggle('on', x === b)); marketDraw(); }));
  $$('#mkFreq button', view).forEach(b => b.addEventListener('click', () => {
    mk.freq = b.textContent; $$('#mkFreq button', view).forEach(x => x.classList.toggle('on', x === b)); marketDraw(); }));
  marketDraw();
}

/* ================================================================ INTERNET SENTIMENT (Reddit) */
function socialPanel() {
  const R = S.social;
  if (!R || !R.configured || !R.posts.length) {
    return `<div class="panel"><div class="label ptitle">Internet sentiment</div>
      <p class="note" style="margin:0">Top Reddit posts about Indonesia's markets will appear here once the Reddit connection is set up.</p></div>`;
  }
  const k = n => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
  const ago = t => { const h = Math.max(1, Math.round((Date.now() / 1000 - t) / 3600)); return h < 48 ? h + 'h ago' : Math.round(h / 24) + 'd ago'; };
  const moodWord = m => m >= 0.15 ? 'leaning positive' : m <= -0.15 ? 'leaning negative' : 'mixed';
  const sp = R.split, total = Math.max(1, sp.positive + sp.neutral + sp.negative), pc = n => (n / total * 100).toFixed(0) + '%';
  return `<div class="panel">
    <div class="mk-head"><div><div class="label ptitle" style="margin-bottom:6px">Internet sentiment</div>
      <div class="note" style="margin:0">Most-upvoted Reddit posts about Indonesia's markets, last ${R.window === 'day' ? '24 hours' : '7 days'}</div></div>
      <div class="mood"><span class="${R.mood <= -0.15 ? 'dn-c' : ''}">Mood: ${moodWord(R.mood)}</span>
        <div class="bar"><i class="p" style="width:${pc(sp.positive)}"></i><i class="u" style="width:${pc(sp.neutral)}"></i><i class="n" style="width:${pc(sp.negative)}"></i></div>
        <span class="muted">${sp.positive} positive · ${sp.neutral} neutral · ${sp.negative} negative (of ${R.sample})</span></div></div>
    <div class="posts">${R.posts.map((p, i) => `<a class="post" href="${esc(p.url)}" target="_blank" rel="noopener">
      <span class="rk">${i + 1}</span><span class="pt">${esc(p.title)}
      <span class="pm">${p.score != null ? `↑ ${k(p.score)} · ${k(p.comments)} comments · ` : ''}r/${esc(p.sub)}${p.created ? ` · ${ago(p.created)}` : ''}</span></span>
      <span class="tone ${p.label}">${p.label}</span></a>`).join('')}</div>
    <p class="note">Tone is scored automatically (VADER sentiment model) from each post's title and opening text, so treat it as a rough read, not a fact.</p>
  </div>`;
}

/* ================================================================ NEWS */
let newsLang = 'All';
function newsDays(stories, limitDays, perDay) {
  const groups = [];
  for (const s of stories) {
    const day = s.t.slice(0, 10);
    if (!groups.length || groups[groups.length - 1].day !== day) groups.push({ day, items: [] });
    groups[groups.length - 1].items.push(s);
  }
  return groups.slice(0, limitDays).map(g => {
    const d = new Date(g.day + 'T00:00:00');
    const label = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) + '<br>' +
                  d.toLocaleDateString('en-GB', { weekday: 'short' });
    const items = g.items.slice(0, perDay ?? g.items.length).map(s =>
      `<div class="item"><a href="${esc(s.l)}" target="_blank" rel="noopener">${esc(s.h)}</a>` +
      `<div class="s">${esc(s.s)} &nbsp; ${s.tags.map(t => `<i>${esc(t)}</i>`).join(' · ')}</div></div>`).join('');
    return `<div class="day"><div class="d">${label}</div><div>${items}</div></div>`;
  }).join('');
}
async function renderNews(view) {
  if (!S.news) { view.innerHTML = '<div class="loading">Fetching the latest headlines…</div>';
                 [S.news, S.candles, S.social] = await Promise.all([getJSON('news.json'), getJSON('candles.json'),
                                                                    getJSON('social.json').catch(() => null)]); }
  const all = S.news.stories;
  const shown = newsLang === 'All' ? all : all.filter(s => s.lang === (newsLang === 'English' ? 'en' : 'id'));
  const updated = new Date(S.news.generated).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jakarta' });
  view.innerHTML = section('01', 'The downgrade, day by day', `Updated ${updated} WIB · ${all.length} stories`) + marketPanel() + socialPanel() + `
    <div class="panel">
      <div class="label ptitle" style="margin-bottom:0">Latest headlines</div>
      <div>${newsDays(shown, 3, 4)}</div>
      <details class="drop"><summary>More stories</summary>${newsDays(shown, 120)}</details>
      <p class="note">Headlines and links via Google News. Tags are keyword-based.</p>
    </div>` + navArrow('#/simulator', 'Simulate the sell-off');
  marketWire(view);
}

/* ================================================================ SIMULATOR */
const GLOSSARY = {
  'Ticker': "The stock's code on the Indonesia Stock Exchange (BBCA = Bank Central Asia). ◆ marks the fintech and digital-finance names.",
  'Wt': "Weight: the stock's estimated share of the MSCI Indonesia index. Bigger weight means index funds hold more of it, so they must sell more.",
  'Out $m': 'Outflow: dollars of this stock that index funds would be forced to sell, in millions.',
  'ADV $m': 'Average daily value: how many dollars of this stock change hands on a normal day (20-day average), in millions. It measures how easy the stock is to sell.',
  'Days': 'Days of forced selling: how many trading days it takes to sell the outflow without crashing the price, if sellers stay under the participation rate. Higher means a longer squeeze.',
  'P/B': "Price-to-book: share price ÷ the company's net assets per share. Below 1 means the market values the company at less than its accounts say it's worth, which is cheap.",
  'P/E': 'Price-to-earnings: share price ÷ yearly profit per share. Lower means cheaper. Blank means the company is losing money.',
  'Δ 15 Oct': "How much the share price has moved since MSCI's proposal on 15 Oct 2026.",
  'Flag': 'OVERSOLD? = more forced selling and a lower P/B than the typical stock here. These may be falling because of index rules rather than the business itself. Not in index = trades too little (under $100k a day) for MSCI funds to hold.',
};
const SCENARIO_NOTES = {
  'Stay EM': 'MSCI backs down. Indonesia stays in the index, so nobody is forced to sell.',
  'Frontier': 'Moved to the Frontier index. EM funds sell, but some Frontier funds buy, so about 85% of the selling remains.',
  'Standalone': 'Dropped from both indexes. Every fund tracking MSCI EM must sell its Indonesian shares.',
};
const sim = { scenario: 'Standalone', page: 0, pick: null, inputs: null };

function simCompute() {
  const I = sim.inputs, factor = S.cfg.scenarios[sim.scenario];
  const cOut = I.aum * 1e9 * (I.weight / 100) * (I.sell / 100) * factor;   // country outflow
  const rows = S.market.stocks.map(st => {
    const out = st.weight ? cOut * st.weight : null;                       // stock's share of it
    const days = out === 0 ? 0 : out && st.adv ? out / (st.adv * I.part / 100) : null;   // days of forced selling
    const pressure = out != null && st.adv ? (out / I.days) / st.adv * 100 : null;
    return { ...st, out, days, pressure };
  });
  const mDays = median(rows.map(r => r.days)), mPB = median(rows.map(r => r.pb));
  rows.forEach(r => { r.oversold = isNum(r.days) && isNum(r.pb) && r.days > mDays && r.pb < mPB; });
  rows.sort((a, b) => (isNum(b.days) ? b.days : -Infinity) - (isNum(a.days) ? a.days : -Infinity));
  return { cOut, expected: cOut * I.prob / 100, factor, rows };
}

function renderSimulator(view) {
  const D = S.cfg.defaults;
  sim.inputs = sim.inputs || { aum: D.passive_aum_bn, weight: D.indonesia_weight, sell: D.pct_sell,
                               prob: D.probability, part: D.participation, days: D.days_to_exit };
  sim.pick = sim.pick || S.market.stocks[0].code;
  const I = sim.inputs;
  const card = (k, title, text, input) =>
    `<div class="acard"><span class="k">${k}</span>${title}<div class="x">${text}</div>${input}</div>`;
  const slider = (id, min, max, val, unit) => sliderHTML(id, min, max, val, val + unit);
  const numbox = (id, min, max, step, val) =>
    `<div class="num"><input type="text" inputmode="decimal" id="${id}" min="${min}" max="${max}" step="${step}" value="${val}">` +
    `<button data-for="${id}" data-dir="-1" aria-label="Decrease">−</button><button data-for="${id}" data-dir="1" aria-label="Increase">+</button></div>`;

  view.innerHTML = section('02', 'Forced-selling simulator', 'Illustrative estimates — not investment advice') + `
  <div class="panel"><div class="steps">
    <div class="step"><div class="i">01</div><div class="h">Index funds copy a list</div><div class="b">Trillions of dollars sit in passive funds that hold exactly what's in MSCI's Emerging Markets index. They don't pick stocks. They mirror the list.</div></div>
    <div class="step"><div class="i">02</div><div class="h">The list changes</div><div class="b">If MSCI moves Indonesia to Standalone, Indonesian stocks drop off that list. Every fund copying it must sell its Indonesian shares, whatever the price or the company's quality.</div></div>
    <div class="step"><div class="i">03</div><div class="h">The market can only absorb so much</div><div class="b">Only so much stock changes hands each day. Sell too fast and the price collapses, so funds spread it out. The days this takes is the <b>days of forced selling</b>, a measure of how long the pressure lasts.</div></div>
  </div></div>

  <div class="panel">
    <div class="label">What MSCI decides</div>
    <div class="seg" id="scen">${Object.keys(S.cfg.scenarios).map(s => `<button class="${s === sim.scenario ? 'on' : ''}">${s}</button>`).join('')}</div>
    <p class="note" id="scenNote">${SCENARIO_NOTES[sim.scenario]}</p>
    <div id="results"></div>
    <details class="drop hot"><summary>Change the assumptions · drag the sliders and watch the numbers move</summary><div class="inner agrid">
      <div>
        ${card('A1', 'Passive money tracking MSCI EM', 'Dollars in index funds that copy MSCI Emerging Markets, in billions (500 = $500bn). Rough industry estimate.',
               numbox('aum', 0, 20000, 50, I.aum))}
        ${card('A2', "Indonesia's share of the index", 'Of every $100 in an EM fund, about this much is in Indonesian stocks. In reality it has been roughly 1–3%; try other values to stress-test.',
               numbox('weight', 0, 100, 0.1, I.weight.toFixed(1)))}
        ${card('A3', 'Share of funds that actually sell', '100% means every tracker exits. Lower it if some funds keep holdings or have flexible mandates.', slider('sell', 0, 100, I.sell, '%'))}
      </div>
      <div>
        ${card('A4', 'Probability MSCI goes through with it', "Your estimate. It turns the 'if downgraded' outflow into an expected outflow.", slider('prob', 0, 100, I.prob, '%'))}
        ${card('A5', 'Participation rate', "The share of a stock's normal daily trading that sellers can be without crashing the price. Traders often use 10–25%.", slider('part', 1, 50, I.part, '%'))}
        ${card('A6', 'Days funds take to exit', 'If funds squeeze the selling into this many days, how big is it compared with normal trading?', slider('days', 1, 120, I.days, ' days'))}
      </div>
    </div></details>
  </div>

  <div class="panel" id="tablePanel">
    <div class="label">Forced selling vs fundamentals</div>
    <div class="tablewrap"><table class="stocks"><thead><tr>
      <th class="ck"></th>${['Ticker', 'Wt', 'Out $m', 'ADV $m', 'Days', 'P/B', 'P/E', 'Δ 15 Oct', 'Flag'].map(h => `<th title="${esc(GLOSSARY[h])}">${h === 'Flag' ? '' : h}</th>`).join('')}
    </tr></thead><tbody id="tbody"></tbody></table></div>
    <div class="pager"><button id="prev" aria-label="Previous page">‹</button><div class="lbl" id="pgLbl"></div><button id="next" aria-label="Next page">›</button></div>
    <p class="note"><span class="red">Click any row</span> to see what the company does and its numbers below. Hover over a column name for a quick explanation.</p>
    <details class="drop"><summary>What do these columns mean?</summary><div class="gloss">
      ${Object.entries(GLOSSARY).map(([n, d]) => `<div class="g"><div class="n">${n}</div><div class="d">${d}</div></div>`).join('')}
    </div></details>
  </div>

  <div class="panel" id="stockPanel">
    <div class="dd" id="pick">
      <button class="dd-btn" type="button" aria-haspopup="listbox"><span id="pickLbl"></span></button>
      <div class="dd-pop" role="listbox">
        <input class="dd-q" type="text" placeholder="Search ticker or company…" aria-label="Search stocks">
        <div class="dd-list">${S.market.stocks.map(s => `<div class="dd-opt" data-code="${s.code}"><b>${s.code}</b> ${esc(s.name)}</div>`).join('')}</div>
      </div>
    </div>
    <div id="stock"></div>
  </div>

  <details class="drop"><summary>Methodology &amp; assumptions</summary><ul class="method">
    <li><b>Country outflow</b> = passive AUM × Indonesia weight × % that sell × scenario factor (Stay EM 0 · Frontier ${S.cfg.scenarios.Frontier} · Standalone 1). The Frontier factor is an assumption.</li>
    <li><b>Index weights</b>: free-float market cap (shares × (1 − insider holding %) × latest price, from Yahoo Finance), as a share of our stocks, × an assumed ${Math.round(S.cfg.coverage * 100)}% coverage of MSCI Indonesia. These are not official MSCI weights.</li>
    <li><b>Liquidity screen</b>: stocks trading under $${S.cfg.min_adv.toLocaleString('en-US')}/day are treated as outside the MSCI index (weight 0), since MSCI screens out very illiquid names.</li>
    <li><b>ADV</b> = 20-day average of close × volume, converted at the latest USD/IDR. Post-crash volumes are unusually high, so ADV may overstate normal liquidity.</li>
    <li><b>Days of forced selling</b> = stock outflow ÷ (ADV × participation rate). <b>Expected</b> = outflow × probability.</li>
    <li><b>P/E, P/B</b> = latest price ÷ EPS or book value per share. For companies that report in USD, book value is converted to rupiah first. Loss-makers have no P/E.</li>
    <li>Prices are from Yahoo Finance, refreshed daily, and may be delayed. The decision date is expected, because MSCI has only said "by end of June 2027".</li>
  </ul></details>
  ${navArrow('#/argentina', 'What happened to Argentina')}`;

  // --- wiring
  $$('#scen button', view).forEach(b => b.addEventListener('click', () => {
    sim.scenario = b.textContent;
    $$('#scen button', view).forEach(x => x.classList.toggle('on', x === b));
    $('#scenNote').textContent = SCENARIO_NOTES[sim.scenario];
    simUpdate();
  }));
  const units = { sell: '%', prob: '%', part: '%', days: ' days' };
  ['aum', 'weight', 'sell', 'prob', 'part', 'days'].forEach(id => $('#' + id).addEventListener('input', e => {
    const v = parseFloat(String(e.target.value).replace(',', '.'));
    if (!isNum(v)) return;
    const lo = parseFloat(e.target.getAttribute('min')), hi = parseFloat(e.target.getAttribute('max'));
    I[id] = Math.min(hi, Math.max(lo, v));
    if (units[id]) paintSlider(e.target, I[id] + units[id]);
    simUpdate();
  }));
  $$('.num button', view).forEach(b => b.addEventListener('click', () => {
    const inp = $('#' + b.dataset.for), step = parseFloat(inp.getAttribute('step'));
    const cur = parseFloat(String(inp.value).replace(',', '.')) || 0;
    const v = Math.round((cur + step * b.dataset.dir) / step) * step;
    inp.value = Math.min(parseFloat(inp.getAttribute('max')), Math.max(parseFloat(inp.getAttribute('min')), v)).toFixed(step < 1 ? 1 : 0);
    inp.dispatchEvent(new Event('input'));
  }));
  $$('.rng', view).forEach(r => paintSlider(r));
  $('#prev').addEventListener('click', () => { sim.page--; simTable(); });
  $('#next').addEventListener('click', () => { sim.page++; simTable(); });
  // custom dark dropdown (the system one clashes with the design)
  const dd = $('#pick'), q = $('.dd-q', dd);
  const closeDD = () => dd.classList.remove('open');
  $('.dd-btn', dd).addEventListener('click', () => {
    dd.classList.toggle('open');
    if (dd.classList.contains('open')) { q.value = ''; filterDD(''); q.focus(); $('.dd-opt.on', dd)?.scrollIntoView({ block: 'nearest' }); }
  });
  const filterDD = s => $$('.dd-opt', dd).forEach(o => { o.style.display = o.textContent.toLowerCase().includes(s.toLowerCase()) ? '' : 'none'; });
  q.addEventListener('input', () => filterDD(q.value));
  q.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDD();
    if (e.key === 'Enter') { const first = $$('.dd-opt', dd).find(o => o.style.display !== 'none'); if (first) first.click(); }
  });
  $$('.dd-opt', dd).forEach(o => o.addEventListener('click', () => { sim.pick = o.dataset.code; closeDD(); simTable(); simStock(); }));
  document.addEventListener('click', e => { if (!dd.contains(e.target)) closeDD(); });
  simUpdate();
}

let simState = null;
function simUpdate() { simState = simCompute(); simResults(); simTable(); simStock(); }

function simResults() {
  const { cOut, expected, factor } = simState, I = sim.inputs;
  $('#results').innerHTML = `
    <div class="metrics"><div class="metric"><div class="k">If downgraded</div><div class="v">${fmtUSD(cOut)}</div></div>
      <div class="metric"><div class="k">Expected outflow</div><div class="v">${fmtUSD(expected)}</div></div></div>` +
    formula('If downgraded: total Indonesian stock passive funds must sell', [
      ['$' + I.aum.toLocaleString('en-US') + 'bn', 'A1 passive money'], [I.weight.toFixed(1) + '%', 'A2 Indonesia share'],
      [I.sell + '%', 'A3 that sell'], [String(factor), sim.scenario + ' factor']], fmtUSD(cOut)) +
    formula('Expected outflow: the same amount, weighted by how likely it is', [
      [fmtUSD(cOut), 'if downgraded'], [I.prob + '%', 'A4 probability']], fmtUSD(expected));
}

function simTable() {
  const rows = simState.rows, PAGE = 15, nPages = Math.max(1, Math.ceil(rows.length / PAGE));
  sim.page = Math.max(0, Math.min(nPages - 1, sim.page));
  const view = rows.slice(sim.page * PAGE, (sim.page + 1) * PAGE);
  const cell = (v, txt) => `<td class="${isNum(v) ? '' : 'na'}">${isNum(v) ? txt : 'None'}</td>`;
  $('#tbody').innerHTML = view.map(r => `<tr data-code="${r.code}" class="${r.code === sim.pick ? 'sel' : ''}">
      <td class="ck"><span></span></td><td>${r.code}${r.fintech ? ' ◆' : ''}</td>
      <td>${isNum(r.weight) ? (r.weight * 100).toFixed(2).replace(/\.?0+$/, '') + '%' : 'None'}</td>
      ${cell(r.out, fmt(r.out / 1e6, 0))}${cell(r.adv, fmt(r.adv / 1e6, 1))}${cell(r.days, fmt(r.days, 1))}
      ${cell(r.pb, fmt(r.pb, 1))}${cell(r.pe, fmt(r.pe, 1))}${cell(r.since, fmtPct(r.since))}
      <td class="flag">${!r.eligible ? 'Not in index' : r.oversold ? 'OVERSOLD?' : ''}</td></tr>`).join('');
  $$('#tbody tr').forEach(tr => tr.addEventListener('click', () => {
    sim.pick = tr.dataset.code; simTable(); simStock();
    $('#stockPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
  $('#prev').disabled = sim.page === 0;
  $('#next').disabled = sim.page >= nPages - 1;
  $('#pgLbl').innerHTML = `Page <b>${sim.page + 1}</b> of ${nPages} &nbsp;·&nbsp; stocks ${sim.page * PAGE + 1}–${sim.page * PAGE + view.length} of ${rows.length}` +
                          `<span class="wide">, most forced selling first</span>`;
}

function simStock() {
  const r = simState.rows.find(x => x.code === sim.pick), I = sim.inputs;
  $('#pickLbl').innerHTML = `<b>${r.code}</b> ${esc(r.name)}`;
  $$('#pick .dd-opt').forEach(o => o.classList.toggle('on', o.dataset.code === r.code));
  const sentence = isNum(r.days) && r.out > 0 ? `<p class="note">Funds would need to sell ${fmtUSD(r.out)} of ${r.code}. About ${fmtUSD(r.adv)} of it trades on a normal day, ` +
    `and sellers can be ${I.part}% of that, so the exit takes about <b>${fmt(r.days, 0)} trading days</b>.</p>` : '';
  $('#stock').innerHTML = `<div class="co inline">${companyHTML(r.code, false)}</div>
    <div class="metrics" style="--cols:4">
      <div class="metric"><div class="k">Must be sold</div><div class="v">${fmtUSD(r.out)}</div></div>
      <div class="metric"><div class="k">Days of forced selling</div><div class="v">${isNum(r.days) ? fmt(r.days, 0) : '—'}</div></div>
      <div class="metric" title="Selling it all in ${I.days} days (A6), compared with a normal day's trading"><div class="k">× normal volume</div><div class="v">${isNum(r.pressure) ? fmt(r.pressure / 100, 1) + '×' : '—'}</div></div>
      <div class="metric"><div class="k">Since 15 Oct</div><div class="v">${fmtPct(r.since)}</div></div>
    </div>${sentence}<div class="chart" id="stockChart"></div>`;
  const i0 = r.dates.findIndex(d => d >= S.cfg.announcement);
  const hover = '%{x|%d %b}  IDR %{y:,.0f}<extra></extra>';
  plot($('#stockChart'), [
    { x: r.dates, y: r.close, mode: 'lines', line: { color: WHITE, width: 1.2 }, hovertemplate: hover },
    ...(i0 >= 0 ? [{ x: r.dates.slice(i0), y: r.close.slice(i0), mode: 'lines+markers', line: { color: RED, width: 1.6 }, marker: { size: 4 }, hovertemplate: hover }] : []),
  ], { margin: { l: 0, r: 56, t: 10, b: 28 },
       xaxis: { showgrid: false, linecolor: RULE, type: 'date', tickformat: '%b %y', nticks: 8, showticklabels: true },
       yaxis: { showgrid: true, gridcolor: '#141414', side: 'right', zeroline: false, tickformat: ',.0f', nticks: 6, showticklabels: true } });
}

/* ================================================================ ARGENTINA */
const ar = { lo: -30, hi: 120 };
async function renderArgentina(view) {
  if (!S.ar) { view.innerHTML = '<div class="loading">Loading Argentina market history…</div>'; S.ar = await getJSON('argentina.json'); }
  const A = S.ar, sign = v => (v > 0 ? '+' : '') + v.toFixed(1) + '%';
  const stats = [[sign(A.day1), 'ARGT, the day after the announcement'], [sign(A.effective), 'ARGT by the effective date (30 Nov 2021)'],
                 [sign(A.low), 'ARGT at its low, within a year'], ['5 yrs+', 'still Standalone (2026 review)']];
  const events = [
    ['2009', 'Downgraded to Frontier', 'MSCI drops Argentina from Emerging Markets over capital controls.', 0],
    ['Jun 2018', 'Promoted back to EM', 'Under market-friendly reforms, MSCI announces Argentina will rejoin EM.', 0],
    ['Sep 2019', 'Capital controls return', 'After a currency crisis, the government reimposes the cepo (strict FX limits).', 0],
    ['24 Jun 2021', 'Standalone announced', 'MSCI says the controls break its accessibility rules. ADRs fall, some by 11%+.', 1],
    ['30 Nov 2021', 'Change takes effect', 'Argentina leaves MSCI EM. Funds tracking the index must have sold by this date.', 1],
    ['2022 – 2026', 'Still Standalone', 'Annual reviews keep Argentina in the lowest tier. Upgrade talk returns, but no move.', 0]];
  const arOut = 500e9 * 0.002, idOut = 500e9 * S.cfg.defaults.indonesia_weight / 100;
  view.innerHTML = section('03', 'Case study: Argentina, 2021', 'The last country MSCI made Standalone') + `
  <div class="panel">
    <p class="lede">In June 2021, MSCI did to Argentina what it now proposes for Indonesia. It cut the country from Emerging Markets to <b>Standalone</b>, the lowest tier. The reason was capital controls that had stopped foreign investors from moving money freely since 2019. Five years later, Argentina is still there.</p>
    <div class="stats">${stats.map(([v, c]) => `<div class="stat"><div class="v ${v.startsWith('-') ? 'r' : ''}">${v}</div><div class="c">${c}</div></div>`).join('')}</div>
  </div>
  <div class="panel"><div class="label">What happened</div><div class="tl">
    ${events.map(([d, h, b, hot]) => `<div class="e ${hot ? 'hot' : ''}"><div class="d">${d}</div><div><div class="h">${h}</div><div class="b">${b}</div></div></div>`).join('')}
  </div></div>
  <div class="panel">
    <div class="label">How the market moved, before vs after the announcement</div>
    <p class="note" style="margin-top:0">Two different years on one clock. Each line counts trading days from <b>its own country's announcement</b> (Argentina: 24 Jun 2021 · Indonesia: 15 Oct 2026), and every line is rescaled so that day equals 100. Left of 0 is the run-up; right of 0 is what happened after. Below 100 means lower than on announcement day.</p>
    <div class="range">
      <div><div class="lab">Days before the announcement</div>${sliderHTML('lo', -60, 0, ar.lo, ar.lo)}</div>
      <div><div class="lab">Days after the announcement</div>${sliderHTML('hi', 20, 250, ar.hi, '+' + ar.hi)}</div>
    </div>
    <div id="arChart"></div>
    <p class="takeaway" id="arTake"></p>
    <p class="note">ARGT is a US-listed ETF of Argentine companies (it includes MercadoLibre), so it shows the hit in dollars. The Merval is converted at the official peso rate, which understates the true currency loss. The red line only runs to today, because Indonesia's story is still unfolding and we never use future data for it. ARGT's later lows also reflect Argentina's inflation and November 2021 elections, not only MSCI.</p>
  </div>
  <div class="panel">
    <div class="label">How much was force-sold?</div>
    <p class="lede" style="font-size:14px">No one published an official figure. Argentina was tiny in the index, about <b>0.1–0.3%</b> of MSCI EM, because only a few US-listed companies qualified. Running it through the same model as the simulator:</p>
    ${formula('Argentina 2021: our estimate', [['$500bn', 'passive money*'], ['0.2%', 'Argentina share'], ['100%', 'that sell'], ['1', 'standalone']], fmtUSD(arOut))}
    ${formula('Indonesia now: same model', [['$500bn', 'passive money*'], [S.cfg.defaults.indonesia_weight.toFixed(1) + '%', 'Indonesia share'], ['100%', 'that sell'], ['1', 'standalone']], fmtUSD(idOut))}
    <p class="takeaway">Indonesia's forced selling would be roughly <b>${Math.round(idOut / arOut)}× larger</b> than Argentina's.</p>
    <p class="note">* Illustrative estimate, not a reported figure. The same rough assumptions as the simulator are used for both, so the comparison matters more than either number.</p>
  </div>
  <div class="panel"><div class="label">What it means for Indonesia</div><div class="steps">
    <div class="step"><div class="i">01</div><div class="h">The first hit was small</div><div class="b">ARGT fell only about 2% the next day, then even rallied. The real damage built over the following months, as the downgrade combined with inflation and politics.</div></div>
    <div class="step"><div class="i">02</div><div class="h">Standalone is sticky</div><div class="b">Argentina has been stuck there since 2021. Getting back in means convincing MSCI over several annual reviews.</div></div>
    <div class="step"><div class="i">03</div><div class="h">Size changes everything</div><div class="b">Argentina was a rounding error in EM. Indonesia is roughly 1.5% of it, so the same rule moves far more money.</div></div>
  </div></div>
  <p class="note">Sources: MSCI 2021 Market Classification Review (announced 24 Jun 2021, effective Nov 2021 review); Bloomberg, Infobae and El Economista coverage of the market reaction; Schroders on Argentina's EM weight; prices from Yahoo Finance.</p>
  ${navArrow('#/', 'Back to the countdown', '↑')}`;
  ['lo', 'hi'].forEach(id => $('#' + id).addEventListener('input', e => {
    ar[id] = parseInt(e.target.value, 10);
    paintSlider(e.target, (id === 'hi' ? '+' : '') + ar[id]);
    arChart();
  }));
  $$('.rng', view).forEach(r => paintSlider(r));
  arChart();
}

function arChart() {
  const A = S.ar, { lo, hi } = ar;
  const cut = s => { const x = [], y = []; s.x.forEach((d, i) => { if (d >= lo && d <= hi) { x.push(d); y.push(s.y[i]); } }); return { x, y }; };
  const line = (s, name, color, width, dash) => ({ ...cut(s), name, mode: 'lines', line: { color, width, dash },
    hovertemplate: `${name}<br>day %{x}: %{y:.1f}<extra></extra>` });
  const shapes = [{ type: 'line', x0: lo, x1: hi, y0: 100, y1: 100, line: { color: RULE, width: 1 } },
                  { type: 'line', x0: 0, x1: 0, yref: 'paper', y0: 0, y1: 1, line: { color: GREY, width: 1, dash: 'dot' } },
                  { type: 'rect', x0: lo, x1: 0, yref: 'paper', y0: 0, y1: 1, fillcolor: 'rgba(255,255,255,0.025)', line: { width: 0 }, layer: 'below' }];
  const notes = [{ x: 0, y: 1, yref: 'paper', text: 'DAY 0 · ANNOUNCED', showarrow: false, xanchor: 'left', yanchor: 'top', font: { color: GREY, size: 9 } },
                 { x: 0, y: 0, yref: 'paper', text: '← BEFORE  ', showarrow: false, xanchor: 'right', yanchor: 'bottom', font: { color: GREY, size: 9 } },
                 { x: 0, y: 0, yref: 'paper', text: '  AFTER →', showarrow: false, xanchor: 'left', yanchor: 'bottom', font: { color: GREY, size: 9 } }];
  if (A.eff_day >= lo && A.eff_day <= hi) {
    shapes.push({ type: 'line', x0: A.eff_day, x1: A.eff_day, yref: 'paper', y0: 0, y1: 1, line: { color: GREY, width: 1, dash: 'dot' } });
    notes.push({ x: A.eff_day, y: 1, yref: 'paper', text: 'EFFECTIVE', showarrow: false, xanchor: 'right', yanchor: 'top', font: { color: GREY, size: 9 } });
  }
  plot($('#arChart'), [
    line(A.series.argt, 'Argentina ETF (ARGT) · day 0 = 24 Jun 2021', WHITE, 1.6),
    line(A.series.merv, 'Merval in USD · 2021', GREY, 1.1),
    line(A.series.ypf, 'YPF (ADR) · 2021', GREY, 1.1, 'dot'),
    line(A.series.jci, 'Indonesia JCI · day 0 = 15 Oct 2026', RED, 2.2),
  ], { showlegend: true, hovermode: 'x unified', shapes, annotations: notes,
       legend: { orientation: 'h', y: -0.22, x: 0, font: { size: 10 } },
       xaxis: { showgrid: false, linecolor: RULE, zeroline: false, range: [lo, hi],
                title: { text: "trading days from each country's announcement", font: { size: 10, color: GREY } } },
       yaxis: { showgrid: false, side: 'right', zeroline: false } });
  const j = A.series.jci, a = A.series.argt, n = Math.max(...j.x);
  if (n > 0) {
    const gap = j.y[j.x.indexOf(n)] - a.y[a.x.indexOf(n)];
    $('#arTake').innerHTML = `${n} trading day${n !== 1 ? 's' : ''} after its announcement, the JCI is <b>${Math.abs(gap).toFixed(1)} points ${gap < 0 ? 'below' : 'above'}</b> where Argentina was at the same point.`;
  }
}

/* ================================================================ ABOUT */
function renderAbout(view) {
  const C = S.cfg;
  view.innerHTML = section('04', 'About', 'Standalone Watch') + `
  <div class="panel"><p class="lede">Standalone Watch follows MSCI's proposal to move Indonesia from Emerging Markets to <b>Standalone</b> status. It counts down to the decision, tracks the news day by day, estimates how much stock index funds would be forced to sell, and compares it all with Argentina, the last country MSCI made Standalone.</p></div>
  <div class="panel about">
    <div class="top"><div><span class="k">Created by</span>${esc(C.author)}</div>
      <div><span class="k">Contact</span><a href="mailto:${esc(C.email)}">${esc(C.email)}</a></div></div>
    <p><b>Not investment advice.</b> Standalone Watch is an independent educational project. All figures are illustrative estimates built on stated assumptions and free public data, which may be delayed, incomplete or wrong. Nothing here is a recommendation to buy or sell any security. Do your own research and consult a licensed adviser before making investment decisions.</p>
    <p><b>No affiliation.</b> This site is not affiliated with, endorsed by or sponsored by MSCI Inc., the Indonesia Stock Exchange (IDX), OJK, or any company mentioned. MSCI and other names are trademarks of their respective owners and are used only to describe public events.</p>
    <p><b>Data &amp; news.</b> Market data via Yahoo Finance, refreshed daily. Headlines link to their original publishers via Google News; all articles remain the property of their publishers. Only headlines and links are shown.</p>
    <p><b>No warranty.</b> Provided "as is" without warranty of any kind. The author accepts no liability for any loss arising from use of this site.</p>
    <div class="c">© ${C.year} ${esc(C.author)}. All rights reserved.</div>
  </div>`;
}

/* ================================================================ ROUTER */
const ROUTES = { '': ['home', renderHome], 'news': ['news', renderNews], 'simulator': ['simulator', renderSimulator],
                 'argentina': ['argentina', renderArgentina], 'about': ['about', renderAbout] };
async function route() {
  const key = location.hash.replace(/^#\/?/, '').split('?')[0];
  const [tab, render] = ROUTES[key] || ROUTES[''];
  closeCard();
  document.body.classList.toggle('home', tab === 'home');
  $$('.tabs a').forEach(a => a.classList.toggle('on', a.dataset.tab === tab));
  window.scrollTo(0, 0);
  const view = $('#view');
  try { await render(view); }
  catch (e) { view.innerHTML = `<div class="loading">Couldn't load this page (${esc(e.message)}). Please refresh.</div>`; console.error(e); }
}

(async function start() {
  try {
    [S.cfg, S.market, S.companies] = await Promise.all([getJSON('config.json'), getJSON('market.json'), getJSON('companies.json')]);
  } catch (e) {
    $('#view').innerHTML = `<div class="loading">Couldn't load data (${esc(e.message)}).</div>`; return;
  }
  tick(); setInterval(tick, 1000);
  const items = S.market.tape.map(t => `<span class="th" data-code="${t.code}"><b>${t.code}</b> ${Math.round(t.close).toLocaleString('en-US')} ` +
    `<span class="${t.chg < 0 ? 'dn-c' : 'up-c'}">${t.chg < 0 ? '▼' : '▲'}${Math.abs(t.chg).toFixed(1)}%</span></span>`).join('');
  $('#strip').innerHTML = `<div class="rollh">${items}${items}</div>`;
  $('#strip').style.setProperty('--dur', Math.max(90, S.market.tape.length * 2.2) + 's');
  $$('#strip .th').forEach(el => el.addEventListener('click', () => openCard(el.dataset.code)));
  window.addEventListener('hashchange', route);
  route();
})();
