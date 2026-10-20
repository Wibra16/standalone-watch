/* live.js — real-time ticker prices over Yahoo Finance's streaming WebSocket.
 *
 * Yahoo pushes each quote as base64-encoded protobuf ("PricingData"). We only
 * need three fields, so a tiny decoder below reads them instead of pulling in
 * a protobuf library:  1 = symbol, 2 = price, 8 = day % change.
 * Every element with data-code="BBCA" (home columns, phone strips, the strip
 * under the nav) is updated in place, so the tickers change as trades happen.
 * Quotes are unofficial and may be delayed; the daily JSON stays the fallback.
 */
(() => {
  const URL = 'wss://streamer.finance.yahoo.com/?version=2';
  const last = {};                 // code -> { price, chg } so re-rendered pages pick up live values
  let ws, retry = 1000, codes = [];

  /* ---- minimal protobuf reader for the fields we need ---- */
  function decode(b64) {
    const bin = atob(b64), buf = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
    const view = new DataView(buf.buffer), out = {};
    let i = 0;
    const varint = () => { let r = 0, s = 0, b; do { b = buf[i++]; r += (b & 0x7f) * 2 ** s; s += 7; } while (b & 0x80); return r; };
    while (i < buf.length) {
      const key = varint(), field = Math.floor(key / 8), wire = key & 7;
      if (wire === 0) { const v = varint(); if (field === 3) out.time = v / 2; }   // time: zigzag-encoded milliseconds
      else if (wire === 1) i += 8;
      else if (wire === 2) { const n = varint(); if (field === 1) out.id = new TextDecoder().decode(buf.subarray(i, i + n)); i += n; }
      else if (wire === 5) { const v = view.getFloat32(i, true); if (field === 2) out.price = v; if (field === 8) out.chg = v; if (field === 12) out.change = v; i += 4; }
      else break;                  // unknown wire type: stop rather than misread
    }
    return out;
  }

  /* ---- IDX trading hours (WIB = UTC+7): Mon–Fri 09:00–16:00 ---- */
  function idxOpen() {
    const wib = new Date(Date.now() + 7 * 3600e3), day = wib.getUTCDay(), m = wib.getUTCHours() * 60 + wib.getUTCMinutes();
    return day >= 1 && day <= 5 && m >= 9 * 60 && m < 16 * 60;
  }

  const fmtPx = p => Math.round(p).toLocaleString('en-US');
  const arrow = c => `${c < 0 ? '▼' : '▲'}${Math.abs(c).toFixed(1)}%`;

  function paint(code, q, flash) {
    document.querySelectorAll(`[data-code="${code}"]`).forEach(el => {
      const p = el.querySelector('.p'), x = el.querySelector('.x');
      if (!p) return;
      const prev = parseFloat(p.textContent.replace(/,/g, ''));
      p.textContent = fmtPx(q.price);
      if (x && Number.isFinite(q.chg)) {
        x.textContent = (el.classList.contains('tk') ? arrow(q.chg).replace(/^(.)/, '$1 ') : arrow(q.chg));
        x.className = 'x ' + (q.chg < 0 ? 'dn-c' : 'up-c');
      }
      if (flash && Number.isFinite(prev) && Math.round(prev) !== Math.round(q.price)) {
        el.classList.remove('up-f', 'dn-f'); void el.offsetWidth;          // restart the animation
        el.classList.add(q.price > prev ? 'up-f' : 'dn-f');
      }
    });
  }

  function badge(state) {
    const b = document.getElementById('live');
    if (!b) return;
    b.className = 'live ' + state;
    b.title = state === 'on' ? 'Prices stream live from Yahoo Finance (may be delayed by a few minutes)'
            : state === 'closed' ? 'IDX is closed: showing the last traded prices'
            : 'Live prices unavailable: showing the latest daily close';
    b.textContent = state === 'on' ? 'LIVE' : state === 'closed' ? 'IDX CLOSED' : 'DELAYED';
  }

  function connect() {
    if (!codes.length) return;
    try { ws = new WebSocket(URL); } catch { return badge('off'); }
    ws.onopen = () => {
      retry = 1000;
      ws.send(JSON.stringify({ subscribe: codes.map(c => c + '.JK').concat(['^JKSE', 'EIDO']) }));   // + index & ETF for the charts
      badge(idxOpen() ? 'on' : 'closed');
    };
    ws.onmessage = e => {
      let msg; try { msg = JSON.parse(e.data); } catch { return; }
      if (msg.type !== 'pricing' || !msg.message) return;
      const q = decode(msg.message);
      if (!q.id || !Number.isFinite(q.price)) return;
      const code = q.id.replace(/\.JK$/, '');
      last[code] = q;
      paint(code, q, true);
      window.onLive && window.onLive(code, q);     // app.js folds it into today's chart bar
    };
    ws.onclose = () => {             // reconnect with backoff (max 30 s)
      badge('off');
      setTimeout(connect, retry); retry = Math.min(retry * 2, 30000);
    };
    ws.onerror = () => ws.close();
  }

  /* app.js calls this once the ticker list is known */
  window.startLive = list => { codes = list; connect(); setInterval(() => ws && ws.readyState === 1 && badge(idxOpen() ? 'on' : 'closed'), 60000); };
  /* and this after each page render, so freshly drawn tickers show live values */
  window.liveLast = last;
  window.repaintLive = () => Object.entries(last).forEach(([c, q]) => paint(c, q, false));
})();
