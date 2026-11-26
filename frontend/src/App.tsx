import { useEffect } from 'react';
import { AppProvider, useApp } from './state/AppContext';
import { FormProvider } from './form/FormContext';
import { TopBar } from './components/layout/TopBar';
import { SideNav } from './components/layout/SideNav';
import { Btn, Empty, Modal, Toast } from './components/common/ui';
import { ReportList } from './screens/ReportList';
import { PatientInfo } from './screens/PatientInfo';
import { CathRecordScreen } from './screens/CathRecord/CathRecordScreen';
import { CagLvgScreen } from './screens/CagLvg/CagLvgScreen';
import { PciScreen } from './screens/Pci/PciScreen';
import { PressureIvusScreen } from './screens/PressureIvus/PressureIvusScreen';
import { PcpsScreen } from './screens/PcpsScreen';
import { ConferenceScreen } from './screens/Conference/ConferenceScreen';
import { MaceScreen } from './screens/MaceScreen';
import { ImagesScreen } from './screens/ImagesScreen';
import { RestudyScreen } from './screens/RestudyScreen';
import { StatsScreen } from './screens/StatsScreen';
import { LoginScreen } from './components/auth/LoginScreen';
import type { ScreenKey } from './state/screens';
import type { ReactNode } from 'react';
import { ReportPrintOverlay } from './components/print/ReportPrint';

const RECORD_SCREENS: Partial<Record<ScreenKey, () => ReactNode>> = {
  patient: () => <PatientInfo />,
  cathRecord: () => <CathRecordScreen />,
  cagLvg: () => <CagLvgScreen />,
  restudy: () => <RestudyScreen />,
  pci: () => <PciScreen />,
  pressureIvus: () => <PressureIvusScreen />,
  images: () => <ImagesScreen />,
  pcps: () => <PcpsScreen />,
  conference: () => <ConferenceScreen />,
  mace: () => <MaceScreen />,
};

function Main() {
  const app = useApp();

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        void app.save();
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [app]);

  let body: ReactNode;
  if (app.screen === 'list') body = <ReportList />;
  else if (app.screen === 'stats') body = <StatsScreen />;
  else if (!app.form) body = <Empty>一覧からレコードを選択するか、「新規作成」してください。</Empty>;
  else body = <FormProvider api={app.form}>{RECORD_SCREENS[app.screen]?.()}</FormProvider>;

  // 未ログイン・期限切れは全画面のログイン画面（編集中の内容はアプリの状態に残る）
  if (app.authRequired)
    return (
      <>
        <LoginScreen />
        {app.toastState && <Toast {...app.toastState} />}
      </>
    );

  return (
    <div className="app">
      <TopBar />
      <div className="app-body">
        <SideNav />
        <main className="main">{body}</main>
      </div>

      {app.printing && app.draft && <ReportPrintOverlay d={app.draft} onClose={() => app.setPrinting(false)} />}

      {app.pendingNav && (
        <Modal
          title="確認"
          width={420}
          footer={
            <>
              <Btn kind="danger" onClick={() => app.resolvePending(true)}>
                放棄
              </Btn>
              <Btn kind="primary" onClick={() => app.resolvePending(false)}>
                キャンセル
              </Btn>
            </>
          }
        >
          <p>変更が有ります。修正を放棄して画面を移動しますか？</p>
          <p className="muted">「キャンセル」を押すと画面に留まり、変更した項目を黄色で表示します。</p>
        </Modal>
      )}

      {app.confirmState && (
        <Modal
          title={app.confirmState.title}
          width={420}
          onClose={app.closeConfirm}
          footer={
            <>
              <Btn
                kind={app.confirmState.danger ? 'danger' : 'primary'}
                onClick={() => {
                  const c = app.confirmState!;
                  app.closeConfirm();
                  c.onOk();
                }}
              >
                {app.confirmState.okLabel ?? 'OK'}
              </Btn>
              <Btn onClick={app.closeConfirm}>キャンセル</Btn>
            </>
          }
        >
          <p>{app.confirmState.message}</p>
        </Modal>
      )}


      {app.toastState && <Toast {...app.toastState} />}
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Main />
    </AppProvider>
  );
}
