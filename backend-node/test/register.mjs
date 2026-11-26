// テスト用：import の '.js' を、同名の '.ts' があればそちらに読み替える（ビルドなしで src/*.ts をテストするため）
import { register } from 'node:module';
register('data:text/javascript,' + encodeURIComponent(`
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
export async function resolve(spec, ctx, next) {
  if (spec.endsWith('.js') && (spec.startsWith('.') || spec.startsWith('/')) && ctx.parentURL?.startsWith('file:')) {
    const ts = new URL(spec.replace(/\\.js$/, '.ts'), ctx.parentURL);
    if (existsSync(fileURLToPath(ts))) return next(ts.href, ctx);
  }
  return next(spec, ctx);
}`));
