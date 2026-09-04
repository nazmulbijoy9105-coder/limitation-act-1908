/* Vercel Serverless Function — GET /api/search?q=article+113&k=5 */
const fs = require('fs');
const path = require('path');

const KB = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', 'kb.json'), 'utf-8'));

const BN_DIGITS = '০১২৩৪৫৬৭৮৯';
const bn2en = s => String(s).replace(/[০-৯]/g, d => String(BN_DIGITS.indexOf(d)));
const tok = s => bn2en(String(s || '')).toLowerCase()
  .replace(/[^\p{L}\p{N}]+/gu, ' ').split(' ').filter(Boolean);

const DOCS = [];
KB.definitions.forEach(d => DOCS.push({ cite: 'D:' + d.term,
  title: `Definition of "${d.term}" (s.${d.section})`, text: d.definition }));
KB.sections.forEach(s => DOCS.push({ cite: 'S' + s.id,
  title: `Section ${s.id} — ${s.title}`, text: s.gist }));
for (const [div, arts] of Object.entries(KB.schedule))
  arts.forEach(a => !a.omitted && DOCS.push({ cite: 'A' + a.a, div,
    title: `Article ${a.a} — ${a.d}`, text: `${a.d} Period: ${a.p} Begins: ${a.s}` }));
KB.faq.forEach((f, i) => DOCS.push({ cite: 'FAQ' + i, title: f.q, text: f.a }));

const TOKS = DOCS.map(d => tok(d.title + ' ' + d.text));
const DF = {};
TOKS.forEach(t => new Set(t).forEach(w => DF[w] = (DF[w] || 0) + 1));
const AVG = TOKS.reduce((a, t) => a + t.length, 0) / TOKS.length;

function bm25(q, k) {
  const qt = tok(q);
  return DOCS.map((d, i) => {
    let s = 0; const t = TOKS[i];
    for (const w of qt) {
      const tf = t.filter(x => x === w).length; if (!tf) continue;
      s += Math.log(1 + (TOKS.length - (DF[w] || 0) + .5) / ((DF[w] || 0) + .5))
         * tf * 2.2 / (tf + 1.2 * (.25 + .75 * t.length / AVG));
    }
    return { ...d, score: +s.toFixed(3) };
  }).filter(r => r.score > 0).sort((a, b) => b.score - a.score).slice(0, k);
}

module.exports = async (req, res) => {
  const { q = '', k = '5' } = req.query;
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.status(200).json({
    act: 'Limitation Act 1908 (Bangladesh)',
    query: q,
    disclaimer: 'General information only — NOT legal advice. Sections 4-25 exclusions may apply; verify with an advocate.',
    results: q ? bm25(q, Math.min(+k, 20)) : DOCS.slice(0, 10)
  });
};
