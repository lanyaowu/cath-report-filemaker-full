/**
 * 実行時の設定。配置先の config.js（public/config.js）で window.__CATH_CONFIG__ を設定すると、ビルドし直さずに変更できる。
 *  storageLock: 'remote' … 保存先を Remote DB に固定し、Local Storage を選べなくする（本番用。患者情報を端末に残さない）
 *               'local'  … Local Storage に固定（デモ用）
 *               ''       … 利用者が選べる（既定）
 *  remoteUrl  : REST API の URL（既定 /api）
 */
export interface AppConfig {
  storageLock: '' | 'local' | 'remote';
  remoteUrl: string;
}

const raw = ((globalThis as { __CATH_CONFIG__?: Partial<AppConfig> }).__CATH_CONFIG__ ?? {}) as Partial<AppConfig>;

export const APP_CONFIG: AppConfig = {
  storageLock: raw.storageLock === 'remote' || raw.storageLock === 'local' ? raw.storageLock : '',
  remoteUrl: typeof raw.remoteUrl === 'string' && raw.remoteUrl ? raw.remoteUrl : '/api',
};
