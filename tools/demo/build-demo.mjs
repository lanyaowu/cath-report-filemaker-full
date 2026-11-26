// デモ用単一HTMLのビルド: tsc で CommonJS へ変換 → mini-react と結合 → 1ファイルに埋め込み
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const root = path.resolve(import.meta.dirname, '../..');
const fe = path.join(root, 'frontend');
const out = '/tmp/demo-build';
fs.rmSync(out, { recursive: true, force: true });
fs.writeFileSync('/tmp/demo-tsconfig.json', JSON.stringify({
  extends: path.join(fe, 'tsconfig.json'),
  compilerOptions: { noEmit: false, module: 'commonjs', moduleResolution: 'bundler', outDir: out, rootDir: path.join(fe, 'src'), jsx: 'react-jsx', target: 'es2020', types: [], noUnusedLocals: false },
  include: [path.join(fe, 'src'), process.env.SHIM ?? '/tmp/shim/react-shim.d.ts'],
}));
execSync('tsc -p /tmp/demo-tsconfig.json', { stdio: 'inherit' });

const modules = {};
const walk = (d) => {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    if (fs.statSync(p).isDirectory()) walk(p);
    else if (f.endsWith('.js')) modules['./' + path.relative(out, p).replace(/\\/g, '/').replace(/\.js$/, '')] = fs.readFileSync(p, 'utf-8');
  }
};
walk(out);
for (const f of ['patients', 'reports', 'masters', 'users']) {
  modules[`./data/${f}.json`] = 'module.exports = ' + fs.readFileSync(path.join(fe, 'src/data', f + '.json'), 'utf-8');
}
// 監査ログの項目名の辞書
modules['./audit/audit-labels.json'] = 'module.exports = ' + fs.readFileSync(path.join(fe, 'src/audit/audit-labels.json'), 'utf-8');
// 多言語表示の辞書（英語・中国語簡体字）
for (const l of ['en', 'zh-CN']) modules[`./i18n/${l}.json`] = 'module.exports = ' + fs.readFileSync(path.join(fe, `src/i18n/${l}.json`), 'utf-8');
const css = fs.readFileSync(path.join(fe, 'src/styles.css'), 'utf-8');
const seedVersion = 'demo-' + crypto.createHash('sha1').update(['patients', 'reports', 'masters'].map((f) => fs.readFileSync(path.join(fe, 'src/data', f + '.json'))).join('')).digest('hex').slice(0, 10);
const runtime = fs.readFileSync(path.join(import.meta.dirname, 'mini-react.js'), 'utf-8');

const loader = `
(function(){
  const defs = {${Object.entries(modules).map(([k, v]) => `${JSON.stringify(k)}: function(module, exports, require){\n${v}\n}`).join(',\n')}};
  const cache = {};
  const ext = { 'react': window.__miniReact.React, 'react/jsx-runtime': window.__miniReact.jsxRuntime, 'react-dom/client': window.__miniReact.dom };
  function resolve(from, req) {
    if (ext[req]) return req;
    if (req.endsWith('.css')) return '__css';
    const parts = from.split('/'); parts.pop();
    for (const seg of req.split('/')) { if (seg === '.') continue; if (seg === '..') parts.pop(); else parts.push(seg); }
    const id = parts.join('/');
    if (defs[id]) return id;
    if (defs[id + '/index']) return id + '/index';
    throw new Error('module not found: ' + req + ' from ' + from);
  }
  function load(id) {
    if (id === '__css') return {};
    if (ext[id]) return ext[id];
    if (cache[id]) return cache[id].exports;
    const m = cache[id] = { exports: {} };
    defs[id](m, m.exports, (r) => load(resolve(id, r)));
    return m.exports;
  }
  load('./main');
})();`;

const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>心カテーテルレポート（レビュー用デモ）</title>
<style>${css}
.demo-banner{position:fixed;left:0;bottom:0;z-index:70;background:#3f5560;color:#fff;font-size:11px;padding:3px 10px;border-top-right-radius:6px;opacity:.85}
</style>
</head>
<body>
<div id="root"></div>
<div class="demo-banner no-print">レビュー用デモ（データはブラウザの Local Storage に保存・サンプルデータ入り）</div>
<script>window.__DEMO_SEED_VERSION__ = ${JSON.stringify(seedVersion)};</script>
<script>${runtime}</script>
<script>${loader}</script>
</body>
</html>`;
const dest = process.argv[2] ?? path.join(root, 'demo/cath-report-demo.html');
fs.mkdirSync(path.dirname(dest), { recursive: true });
fs.writeFileSync(dest, html);
console.log('written', dest, (html.length / 1024).toFixed(0) + 'KB');
