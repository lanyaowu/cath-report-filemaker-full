// Thymeleaf 版（cath-report-tl）へ多言語表示の部品を書き出す。
//   node tools/i18n/build-tl.mjs ../cath-report-tl
// 出力（Thymeleaf 版の src/main/resources/static/js/）：
//   i18n.js        … frontend/src/i18n/translator.ts を変換したもの（window.CathI18nCore）
//   i18n-en.js・i18n-zh-CN.js … 辞書 frontend/src/i18n/{en,zh-CN}.json（window.CATH_I18N）
// 起動・言語の切替（Cookie cath_lang）は Thymeleaf 版の static/js/i18n-boot.js。
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let ts;
try {
  ts = require('typescript');
} catch {
  ts = require('/opt/npm-tools/node_modules/typescript');
}
const root = path.resolve(import.meta.dirname, '../..');
const tl = path.resolve(process.argv[2] ?? path.join(root, '../cath-report-tl'));
const outDir = path.join(tl, 'src/main/resources/static/js');
if (!fs.existsSync(outDir)) throw new Error('Thymeleaf 版が見つかりません: ' + tl);

const src = fs.readFileSync(path.join(root, 'frontend/src/i18n/translator.ts'), 'utf-8');
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019, removeComments: false } }).outputText;
const head = '/* このファイルは cathreport の tools/i18n/build-tl.mjs で作成（元：frontend/src/i18n/translator.ts）。直接編集しない */\n';
fs.writeFileSync(path.join(outDir, 'i18n.js'), `${head}(function () {\nvar exports = {};\n${js}\nwindow.CathI18nCore = exports;\n})();\n`);
// 辞書（言語ごと）。window.CATH_I18N = { en: {...}, 'zh-CN': {...} }
for (const lang of ['en', 'zh-CN']) {
  const dict = fs.readFileSync(path.join(root, `frontend/src/i18n/${lang}.json`), 'utf-8');
  fs.writeFileSync(path.join(outDir, `i18n-${lang}.js`), `${head.replace('translator.ts', `${lang}.json`)}window.CATH_I18N = window.CATH_I18N || {};\nwindow.CATH_I18N[${JSON.stringify(lang)}] = ${dict.trim()};\n`);
}
console.log('written', outDir, 'i18n.js i18n-en.js i18n-zh-CN.js');
