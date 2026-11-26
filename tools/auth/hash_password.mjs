#!/usr/bin/env node
// パスワードのハッシュを作る（users.json の password 欄に貼り付ける）
// usage: node tools/auth/hash_password.mjs <パスワード>
//   形式: pbkdf2_sha256$反復回数$salt(Base64)$hash(Base64)  （Node.js 版・Spring 版・Thymeleaf 版で共通）
import { pbkdf2Sync, randomBytes } from 'node:crypto';
const pw = process.argv[2];
if (!pw) { console.error('usage: node tools/auth/hash_password.mjs <パスワード>'); process.exit(1); }
const it = 120000, salt = randomBytes(16);
console.log(`pbkdf2_sha256$${it}$${salt.toString('base64')}$${pbkdf2Sync(pw, salt, it, 32, 'sha256').toString('base64')}`);
