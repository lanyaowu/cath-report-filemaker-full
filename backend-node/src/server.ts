import { readFileSync } from 'node:fs';
import https from 'node:https';
import express, { type NextFunction, type Request, type Response } from 'express';
import cors from 'cors';
import { config } from './config.js';
import { close, connect, seedIfEmpty, seedOptionMasters } from './db.js';
import { api } from './routes/api.js';
import { authApi, authenticate, loadUsers } from './auth.js';

async function main() {
  loadUsers();
  await connect();
  if (config.seedOnStartup) await seedIfEmpty();
  await seedOptionMasters(); // 選択値マスタは本番でも必要（無いカテゴリだけ追加）

  const app = express();
  app.use(cors({ origin: config.corsOrigin }));
  app.use(express.json({ limit: config.bodyLimit }));
  app.set('trust proxy', process.env.TRUST_PROXY === 'true'); // リバースプロキシ配下で利用者の IP を記録する場合
  app.use('/api', authenticate, authApi, api);

  app.use((err: Error & { type?: string }, _req: Request, res: Response, _next: NextFunction) => {
    if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'JSON の形式が不正です' });
    if (err.type === 'entity.too.large') return res.status(413).json({ error: `データが大きすぎます（上限 ${config.bodyLimit}）` });
    console.error(err);
    res.status(500).json({ error: 'サーバーでエラーが発生しました（詳細はサーバーのログを確認してください）' });
  });

  const tls = config.tlsCertFile && config.tlsKeyFile;
  const server = tls
    ? https.createServer({ cert: readFileSync(config.tlsCertFile), key: readFileSync(config.tlsKeyFile) }, app).listen(config.port)
    : app.listen(config.port);
  server.on('listening', () =>
    console.log(`Cath Report API (Node) listening on ${tls ? 'https' : 'http'}://localhost:${config.port}/api  db=${config.dbName}`));

  const shutdown = () => server.close(() => void close().then(() => process.exit(0)));
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch((e) => {
  console.error('起動に失敗しました:', e);
  process.exit(1);
});
