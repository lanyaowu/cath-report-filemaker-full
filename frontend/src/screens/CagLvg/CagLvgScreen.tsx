import { useState } from 'react';
import { Scope } from '../../form/FormContext';
import { Tabs } from '../../components/common/ui';
import { ScreenFrame } from '../../components/layout/ScreenFrame';
import { CatheterPanel } from './CatheterPanel';
import { CagTab } from './CagTab';
import { LvgTab } from './LvgTab';
import { useApp } from '../../state/AppContext';
import { hasAnyValue } from '../../utils/path';

/** CAG/LVG：患者情報・カテ履歴・カテーテルの3画面構成＋CAG/LVGタブ */
export function CagLvgScreen() {
  const [tab, setTab] = useState('cag');
  const d = useApp().draft!;
  return (
    <ScreenFrame>
      <Scope path="/report.cagLvg">
        <CatheterPanel />
        <Tabs
          active={tab}
          onChange={setTab}
          tabs={[
            { key: 'cag', label: 'CAG', hasData: hasAnyValue(d.report.cagLvg.cag) },
            { key: 'lvg', label: 'LVG', hasData: hasAnyValue(d.report.cagLvg.lvg) },
          ]}
        />
        <div className="tab-body tone-slate-bg">
          {tab === 'cag' ? (
            <Scope path="cag">
              <CagTab />
            </Scope>
          ) : (
            <Scope path="lvg">
              <LvgTab />
            </Scope>
          )}
        </div>
      </Scope>
    </ScreenFrame>
  );
}
