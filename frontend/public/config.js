// 心カテーテルレポートの実行時設定（ビルド後も dist/config.js を書き換えれば反映されます）
//   本番：保存先を Remote DB に固定（Local Storage を使わせない）
//     window.__CATH_CONFIG__ = { storageLock: 'remote', remoteUrl: '/api' };
//   デモ・試用（既定）：利用者が保存先を選べる
window.__CATH_CONFIG__ = {};
