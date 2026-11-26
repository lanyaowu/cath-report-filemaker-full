// 本番用の設定例。配置時に dist/config.js をこの内容で置き換えてください。
// 保存先を Remote DB に固定し、ログインを必須にします（患者情報を端末のブラウザに残さない）。
window.__CATH_CONFIG__ = { storageLock: 'remote', remoteUrl: '/api' };
