// 使い方: cd frontend && tsc --ignoreConfig src/model/defaults.ts src/utils/calc.ts --outDir /tmp/out --module commonjs --target es2020 --skipLibCheck && cp ../tools/dump_fields.js /tmp/out/ && node /tmp/out/dump_fields.js
const d = require('./model/defaults.js');
const O = require('./constants/options.js');
const leaves = [];
const walk = (v, p, def) => {
  if (v !== null && typeof v === 'object') {
    if (Array.isArray(v)) { if (v.length) walk(v[0], p + '[]', null); return; }
    for (const k of Object.keys(v)) walk(v[k], p ? `${p}.${k}` : k);
  } else leaves.push({ path: p, type: typeof v });
};
const r = d.createEmptyReport(); r.images = [d.createImageItem()];
const pt = d.createEmptyPatient(); pt.admissions = [{ admitDate: '', dischargeDate: '', doctor: '', diagnosis: '', summary: '' }];
walk(pt, 'patient'); walk(r, 'report');
// 配列長
const arrLen = {};
const walkA = (v, p) => { if (Array.isArray(v)) { arrLen[p] = v.length; if (v.length) walkA(v[0], p + '[]'); } else if (v && typeof v === 'object') for (const k of Object.keys(v)) walkA(v[k], p ? `${p}.${k}` : k); };
walkA(d.createEmptyReport(), 'report');
// 定数からのラベル・選択肢
const consts = {};
for (const [name, val] of Object.entries(O)) {
  if (typeof val === 'function') continue;
  consts[name] = val;
}
require('fs').writeFileSync('/tmp/dump.json', JSON.stringify({ leaves, arrLen, consts }));
console.log(leaves.length);
