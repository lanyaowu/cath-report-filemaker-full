import { APP_CONFIG } from '../config';
import { LocalStorageAdapter } from './LocalStorageAdapter';
import { RemoteStorageAdapter, type AuthHooks } from './RemoteStorageAdapter';
import type { StorageAdapter, StorageKind } from './StorageAdapter';

export type { StorageAdapter, StorageKind, AuthHooks };
export { LocalStorageAdapter, RemoteStorageAdapter };
export { AuthError } from './RemoteStorageAdapter';

export interface StorageSettings { kind: StorageKind; remoteUrl: string }
const SETTINGS_KEY = 'cath.storageSettings';
export const DEFAULT_SETTINGS: StorageSettings = { kind: APP_CONFIG.storageLock === 'remote' ? 'remote' : 'local', remoteUrl: APP_CONFIG.remoteUrl };

/** 保存先が設定（config.js の storageLock）で固定されているか */
export const storageLocked = APP_CONFIG.storageLock !== '';

/** 固定されている場合は、保存された選択より固定値を優先する */
function applyLock(s: StorageSettings): StorageSettings {
  return APP_CONFIG.storageLock ? { ...s, kind: APP_CONFIG.storageLock } : s;
}

export function loadSettings(): StorageSettings {
  try {
    return applyLock({ ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) ?? '{}') });
  } catch {
    return applyLock(DEFAULT_SETTINGS);
  }
}
export function saveSettings(s: StorageSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(applyLock(s)));
}

export function createAdapter(s: StorageSettings, auth?: AuthHooks): StorageAdapter {
  const x = applyLock(s);
  return x.kind === 'remote' ? new RemoteStorageAdapter(x.remoteUrl, auth) : new LocalStorageAdapter(auth?.user);
}
