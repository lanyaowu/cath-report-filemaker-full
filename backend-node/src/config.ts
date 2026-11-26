import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

export const config = {
  port: Number(process.env.PORT ?? 8080),
  mongoUri: process.env.MONGODB_URI ?? 'mongodb://localhost:27017',
  dbName: process.env.MONGODB_DB ?? 'cathreport',
  corsOrigin: (process.env.CORS_ORIGIN ?? 'http://localhost:5173').split(','),
  seedOnStartup: (process.env.SEED_ON_STARTUP ?? 'true') === 'true',
  sampleDir: process.env.SAMPLE_DIR ? path.resolve(process.env.SAMPLE_DIR) : path.resolve(here, '../../sample-data'),
  bodyLimit: process.env.BODY_LIMIT ?? '20mb',
  // ---- 認証・権限（docs/security.md）
  authEnabled: (process.env.AUTH_ENABLED ?? 'true') === 'true',
  /** トークン署名の秘密鍵。未設定なら起動ごとに乱数（再起動でログアウト） */
  authSecret: process.env.AUTH_SECRET ?? '',
  authTokenTtlMinutes: Number(process.env.AUTH_TOKEN_TTL_MIN ?? 480),
  /** 利用者の定義ファイル（既定はサンプルの利用者。本番では必ず差し替える） */
  usersFile: process.env.AUTH_USERS_FILE
    ? path.resolve(process.env.AUTH_USERS_FILE)
    : path.resolve(process.env.SAMPLE_DIR ? path.resolve(process.env.SAMPLE_DIR) : path.resolve(here, '../../sample-data'), 'users.json'),
  /** POST /api/admin/seed（全データ置換）を許可するか。既定は無効 */
  allowSeedApi: (process.env.ALLOW_SEED_API ?? 'false') === 'true',
  // ---- HTTPS（両方を指定すると HTTPS で待ち受け）
  tlsCertFile: process.env.TLS_CERT_FILE ?? '',
  tlsKeyFile: process.env.TLS_KEY_FILE ?? '',
};
