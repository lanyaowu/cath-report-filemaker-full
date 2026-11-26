import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal } from '../common/ui';
import { RemoteStorageAdapter, storageLocked, type StorageSettings } from '../../storage';

/** 永続化先の切替（Local Storage / Remote DB） */
export function SettingsDialog({ onClose }: { onClose: () => void }) {
  const app = useApp();
  const [s, setS] = useState<StorageSettings>(app.settings);
  const [ping, setPing] = useState<string>('');

  return (
    <Modal
      title="保存先設定"
      onClose={onClose}
      footer={
        <>
          <Btn
            kind="primary"
            onClick={() => {
              onClose();
              app.changeSettings(s);
            }}
          >
            適用
          </Btn>
          <Btn onClick={onClose}>キャンセル</Btn>
        </>
      }
    >
      <div className="settings">
        {storageLocked ? (
          <p>保存先は管理者の設定で <b>{s.kind === 'remote' ? 'Remote DB' : 'Local Storage'}</b> に固定されています。</p>
        ) : (
          <>
            <label className="chk">
              <input type="radio" checked={s.kind === 'local'} onChange={() => setS({ ...s, kind: 'local' })} />
              <span>Local Storage（ブラウザ内保存・デモ用。デモ用の利用者でログイン）</span>
            </label>
            <label className="chk">
              <input type="radio" checked={s.kind === 'remote'} onChange={() => setS({ ...s, kind: 'remote' })} />
              <span>Remote DB（REST API → データベース。サーバーで認証）</span>
            </label>
          </>
        )}
        <div className="f" style={{ marginTop: 8 }}>
          <label className="lbl" style={{ width: 90 }}>API URL</label>
          <input className="inp" style={{ width: 300 }} value={s.remoteUrl} onChange={(e) => setS({ ...s, remoteUrl: e.target.value })} />
          <Btn
            small
            onClick={async () => {
              setPing('確認中…');
              setPing((await new RemoteStorageAdapter(s.remoteUrl).ping()) ? '✔ 接続OK' : '✖ 接続できません');
            }}
          >
            接続テスト
          </Btn>
          <span className="muted">{ping}</span>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          Node 版・Spring Boot 版バックエンドは同一 API（既定 http://localhost:8080/api）。開発サーバーでは /api がプロキシされます。
        </p>
        {app.can('seed') && (
          <>
            <hr />
            <Btn kind="danger" onClick={() => { onClose(); app.resetSample(); }}>
              現在の保存先にサンプルデータを投入
            </Btn>
            {s.kind === 'remote' && <p className="muted">Remote DB では、サーバーで投入が許可されている場合（ALLOW_SEED_API=true）だけ実行できます。</p>}
          </>
        )}
      </div>
    </Modal>
  );
}
