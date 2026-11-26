import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { storageLocked } from '../../storage';
import { DEMO_USERS } from '../../auth/localAuth';
import { ROLE_LABEL } from '../../auth/permissions';
import { SettingsDialog } from '../dialogs/SettingsDialog';
import { LangSwitch } from '../../i18n';

/**
 * ログイン画面（全画面）。未ログイン・ログインの期限切れの時に表示する。
 * - Remote DB：サーバーで認証（5 回失敗で 15 分ロックなどはサーバー側）
 * - Local Storage（デモ）：デモ用の利用者でブラウザ内で照合。役割ごとの権限を体験できる
 * 編集中の内容はアプリの状態に残るので、ログインし直すと続きから保存できる。
 */
export function LoginScreen() {
  const app = useApp();
  const remote = app.adapter.kind === 'remote';
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [settings, setSettings] = useState(false);

  const submit = async () => {
    if (!username.trim() || !password) return setError('ユーザー名とパスワードを入力してください');
    setBusy(true);
    setError('');
    try {
      await app.login(username.trim(), password);
      setPassword('');
    } catch (e) {
      setError((e as Error).message || 'ログインできませんでした');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo" aria-hidden="true">♥</div>
          <div>
            <h1>心カテーテルレポート</h1>
            <div className="login-sub">Cardiac Catheterization Report</div>
          </div>
          <LangSwitch className="login-lang" />
        </div>

        <form
          className="login-form"
          onSubmit={(e: { preventDefault: () => void }) => {
            e.preventDefault();
            void submit();
          }}
        >
          <label className="login-lbl" htmlFor="login-user">ユーザー名</label>
          <input id="login-user" className="inp login-inp" autoFocus autoComplete="username" value={username}
            onChange={(e) => setUsername(e.target.value)} />
          <label className="login-lbl" htmlFor="login-pass">パスワード</label>
          <input id="login-pass" className="inp login-inp" type="password" autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="login-error" role="alert">{error}</p>}
          {app.draft && <p className="login-note">編集中の内容は残っています。ログイン後に保存してください。</p>}
          <button type="submit" className="btn btn-primary login-btn" disabled={busy}>
            {busy ? 'ログイン中…' : 'ログイン'}
          </button>
        </form>

        <div className="login-store">
          <span>保存先：{remote ? `サーバー（${app.settings.remoteUrl}）` : 'このブラウザ（Local Storage・デモ）'}</span>
          {!storageLocked && (
            <button type="button" className="login-link" onClick={() => setSettings(true)}>保存先設定</button>
          )}
        </div>

        {!remote && (
          <div className="login-demo">
            <div className="login-demo-title">デモ用の利用者（クリックで入力。パスワードは demo-ユーザー名）</div>
            <table>
              <tbody>
                {DEMO_USERS.map((u) => (
                  <tr key={u.username} onClick={() => { setUsername(u.username); setPassword(`demo-${u.username}`); setError(''); }}>
                    <td className="code">{u.username}</td>
                    <td>{u.displayName}</td>
                    <td className="muted">{u.roles.map((r) => ROLE_LABEL[r] ?? r).join('・')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="login-foot">Local Storage のログインは画面を体験するためのものです。本番は保存先を Remote DB に固定し、サーバーで認証します。</p>
          </div>
        )}
      </div>
      {settings && <SettingsDialog onClose={() => setSettings(false)} />}
    </div>
  );
}
