/** サンプルデータ投入スクリプト: npm run seed */
import { close, connect, seed } from './db.js';

await connect();
const r = await seed();
console.log(`サンプルデータを投入しました: 患者 ${r.patients} 件 / レポート ${r.reports} 件`);
await close();
