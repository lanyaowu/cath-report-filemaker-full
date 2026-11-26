import { useApp } from '../../state/AppContext';
import type { ReactNode } from 'react';
import { PatientHeader } from './PatientHeader';
import { useForm } from '../../form/FormContext';

export function ScreenFrame({ headerExtra, children }: { headerExtra?: ReactNode; children: ReactNode }) {
  const f = useForm();
  const app = useApp();
  return (
    <div className="screen">
      {f.readOnly && (
        <div className="lock-banner">
          {app.draft?.report.status === '確定'
            ? '🔒 このレポートは「確定」済みのため編集できません。修正する場合はサイドメニューの「確定」をクリックして「入力中」に戻してください。'
            : app.user || !app.authRequired
              ? '🔒 閲覧のみの権限のため編集できません。'
              : '🔒 ログインが必要です。ログインすると編集・保存できます（入力内容は残っています）。'}
        </div>
      )}
      <PatientHeader extra={headerExtra} />
      <div className="screen-body">{children}</div>
    </div>
  );
}
