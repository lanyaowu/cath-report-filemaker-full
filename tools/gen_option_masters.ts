/**
 * 選択値マスタの初期データを作る（constants/options.ts の cat(...) の定義 → JSON）。
 *   npx tsx tools/gen_option_masters.ts
 * 出力：
 *   sample-data/option-masters.json         … Node.js 版が初回起動時に MongoDB へ投入（全バージョン共通の初期データ）
 *   frontend/src/data/option-masters.json   … 同じ内容（フロントのテストで定義との一致を確認）
 * Thymeleaf 版（PostgreSQL）の Flyway の初期データ（V6__option_masters.sql）も、このファイルから作る。
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defaultOptionCategories } from '../frontend/src/model/optionMaster';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = defaultOptionCategories().map(({ version: _v, ...c }) => c);
const json = `${JSON.stringify(data, null, 1)}\n`;
for (const f of ['sample-data/option-masters.json', 'frontend/src/data/option-masters.json']) {
  writeFileSync(path.join(root, f), json, 'utf-8');
  console.log(`${f}: ${data.length} カテゴリ / ${data.reduce((n, c) => n + c.items.length, 0)} 選択値`);
}
