/* api/vote.js — "Are we cooked?" poll (Vercel serverless function).
 *
 * GET  /api/vote             -> { counts: {stay, frontier, standalone}, total }
 * POST /api/vote {choice, voter}
 *      One vote per browser (voter = random id kept in localStorage); voting
 *      again changes your vote instead of adding one. Light abuse limits:
 *      30 requests a minute per IP, and at most 20 different voter ids per IP a day (campus Wi-Fi shares one IP).
 *
 * Storage: Upstash Redis over its REST API. Connect it in Vercel
 * (Storage -> Upstash Redis -> Connect to project), which sets the env vars below.
 */
const crypto = require('crypto');

const CHOICES = ['stay', 'frontier', 'standalone'];
const POLL = 'poll:msci-2027';
const URL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

async function redis(commands) {                 // one round trip for several commands
  const r = await fetch(`${URL}/pipeline`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(commands),
  });
  if (!r.ok) throw new Error(`redis ${r.status}`);
  return (await r.json()).map(x => x.result);
}

async function tally() {
  const [flat] = await redis([['HGETALL', POLL]]);
  const counts = Object.fromEntries(CHOICES.map(c => [c, 0]));
  for (let i = 0; i < (flat || []).length; i += 2) if (CHOICES.includes(flat[i])) counts[flat[i]] = Math.max(0, +flat[i + 1]);
  return { counts, total: CHOICES.reduce((s, c) => s + counts[c], 0) };
}

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (!URL || !TOKEN) return res.status(503).json({ error: 'Voting is not set up yet.' });
  try {
    if (req.method === 'GET') return res.status(200).json(await tally());
    if (req.method !== 'POST') return res.status(405).json({ error: 'GET or POST only' });

    const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const { choice, voter } = body;
    if (!CHOICES.includes(choice) || !/^[a-z0-9-]{8,64}$/i.test(String(voter || '')))
      return res.status(400).json({ error: 'Bad vote' });

    const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim();
    const ipKey = crypto.createHash('sha256').update(ip + POLL).digest('hex').slice(0, 24);   // never store raw IPs
    const [hits, , seen, ids, prev] = await redis([
      ['INCR', `rl:${ipKey}`], ['EXPIRE', `rl:${ipKey}`, 60, 'NX'],
      ['SISMEMBER', `ipv:${ipKey}`, voter], ['SCARD', `ipv:${ipKey}`],
      ['HGET', `${POLL}:voters`, voter],
    ]);
    if (hits > 30) return res.status(429).json({ error: 'Too many requests, try again in a minute.' });
    if (!seen && ids >= 20) return res.status(429).json({ error: 'Vote limit reached for this network today.' });

    if (prev !== choice) {
      const cmds = [['HSET', `${POLL}:voters`, voter, choice], ['HINCRBY', POLL, choice, 1],
                    ['SADD', `ipv:${ipKey}`, voter], ['EXPIRE', `ipv:${ipKey}`, 86400, 'NX']];
      if (CHOICES.includes(prev)) cmds.push(['HINCRBY', POLL, prev, -1]);
      await redis(cmds);
    }
    return res.status(200).json({ ...(await tally()), mine: choice });
  } catch (e) {
    return res.status(500).json({ error: 'Could not reach the vote store.' });
  }
};
